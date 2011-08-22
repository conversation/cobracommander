import gevent
import redis
import datetime
from multiprocessing import Process, Queue
from Queue import Empty
from collections import defaultdict
from django.conf import settings

from .utils import get_logger
from .buildrunner import BuildRunner
from app.apps.build.models import Build

class Builder(object):
    """
    Builder runs tasks around starting, stopping and monitoring state of
    builds.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        self.redis_conn = None
        self.status = defaultdict(dict)
        self.status['active_build'] = None
        self.status['state'] = 'idle'
        self.status['queue'] = list()
        gevent.spawn(self.run_builds)
        gevent.spawn(self.poll_build_queue)
    
    @property
    def redis(self):
        if self.redis_conn == None:
            self.logger.info("Connecting to redis on %(host)s:%(port)s db:%(db)s",
                settings.REDIS_DATABASE)
            self.redis_conn = redis.Redis(**settings.REDIS_DATABASE)
        return self.redis_conn
    
    @property
    def is_idle(self):
        if self.status['state'] == 'idle' and not self.status['active_build']:
            return True
        return False 

    def run_builds(self):
        self.logger.info("Waiting for builds to run")
        while True:
            if len(self.status['queue']) and self.is_idle:
                build = self.status['queue'].pop(0)
                build_queue = Queue()
                self.logger.info("Spawning new BuildRunner process for build id:%s",
                    build.id)
                process = Process(name='worker-%s' % build.id, target=BuildRunner,
                    args=(build.id, build_queue))
                self.status['active_build'] = dict()
                self.status['active_build']['process'] = process
                self.status['active_build']['build'] = build
                self.status['state'] = 'building'
                process.start()
                while True:
                    try:
                        exit_status = build_queue.get(False)
                        if exit_status == "COMPLETE" or exit_status == "QUIT":
                            self.stop_build()
                            break
                    except Empty, e:
                        pass
                    gevent.sleep(0.25)
                self.stop_build() # cleanup
            gevent.sleep(1.0)
    
    def stop_build(self):
        if 'active_build' in self.status:
            build = self.status['active_build']['build']
            build.end_datetime = datetime.datetime.now()
            build.save()
            self.logger.info("Stopping build id: %s", build.id)
            self.status['active_build']['process'].terminate()
            del self.status['active_build']
            self.status['state'] = 'idle'

    def poll_build_queue(self):
        self.logger.info("Listening for incoming builds")
        while True:
            if self.redis.llen('build_queue') > 0:
                # pop leftmost item from the message queue
                build_id = self.redis.lpop('build_queue')
                try:
                    build = Build.objects.select_related().get(id=build_id)
                    # append build_id onto internal state
                    self.status['queue'].append(build)
                    self.logger.info("Added build with id %s to queue.", build_id)
                except Exception, e:
                    self.logger.error("Build with id %s does not exist yet was \
                        in build queue.", build_id)
            gevent.sleep(1.0)
    
