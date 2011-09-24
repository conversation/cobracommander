import gevent
import redis
import datetime
from multiprocessing import Process, Queue
from Queue import Empty
from collections import defaultdict
from django.conf import settings
from copy import deepcopy

from .utils import get_logger
from .runner.runner import Runner
from app.apps.build.models import Build


class Builder(object):
    """
    Builder runs tasks around starting, stopping and monitoring state of
    builds.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        self.redis_connection = None
        self.status = defaultdict(dict)
        self.process = None
        self.status['active_build'] = None
        self.status['pending_builds'] = list()
        self.status['building'] = False
        gevent.spawn(self.run_builds)
        gevent.spawn(self.poll_build_queue)

    @property
    def redis(self):
        if self.redis_connection == None:
            self.logger.info("Connecting to redis on %(host)s:%(port)s db:%(db)s",
                settings.REDIS_DATABASE)
            self.redis_connection = redis.Redis(**settings.REDIS_DATABASE)
        return self.redis_connection

    @property
    def is_idle(self):
        if not self.status['building'] and not self.status['active_build']:
            return True
        return False

    def get_queue(self):
        return deepcopy({
            'active':   self.status.get('active_build'),
            'pending':  self.status.get('pending_builds')
        })

    def run_builds(self):
        self.logger.info("Waiting for builds to run")
        while True:
            if len(self.status['pending_builds']) and self.is_idle:
                self.status['active_build'] = self.status['pending_builds'].pop(0)
                build_queue = Queue()
                self.logger.info("Spawning new BuildRunner process for build id:%s",
                    self.status['active_build'].id)
                self.process = Process(name='worker-%s' % self.status['active_build'].id,
                    target=Runner, args=(self.status['active_build'].id,
                    build_queue))
                self.status['building'] = True
                self.process.start()
                while True:
                    try:
                        exit_status = build_queue.get(False)
                        if exit_status == "COMPLETE" or exit_status == "QUIT":
                            print "exit_status: %s" % exit_status
                            self.stop_build()
                            break
                    except Empty, e:
                        pass
                    gevent.sleep(0.5)
            gevent.sleep(2.0)

    def stop_build(self):
        if 'active_build' in self.status:
            self.logger.info("Stopping build id: %s", self.status['active_build'].id)
            self.process.terminate()
            self.status['active_build'] = None
            self.status['building'] = False

    def poll_build_queue(self):
        self.logger.info("Listening for incoming builds")
        while True:
            if self.redis.llen('build_queue') > 0:
                # pop leftmost item from the message queue
                build_id = self.redis.lpop('build_queue')
                try:
                    build = Build.objects.select_related().get(id=build_id)
                    # append build_id onto internal state
                    self.status['pending_builds'].append(build)
                    self.logger.info("Added build with id %s to queue.", build_id)
                except Exception, e:
                    self.logger.error("Build with id %s does not exist yet was \
                        in build queue.", build_id)
            gevent.sleep(1.0)

