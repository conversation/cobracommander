import gevent
import redis
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
        self.status['state'] = 'idle'
        self.status['queue'] = list()
        gevent.spawn(self.poll_build_queue)
    
    @property
    def redis(self):
        if self.redis_conn == None:
            self.logger.info("Connecting to redis on %(host)s:%(port)s db:%(db)s",
                settings.REDIS_DATABASE)
            self.redis_conn = redis.Redis(**settings.REDIS_DATABASE)
        return self.redis_conn
    
    def is_idle(self):
        if self.status['state'] == 'idle' and 'active_build' not in self.status:
            return True
        return False 

    def run_build(self):
        if self.is_idle():
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
                    if build_queue.get(False) == "QUIT":
                        self.stop_build()
                        break
                except Empty, e:
                    pass
                gevent.sleep(0.5)
            self.stop_build() # cleanup
    
    def stop_build(self):
        if 'active_build' in self.status:
            build = self.status['active_build']['build']
            self.logger.info("Stopping build id: %s", build.id)
            self.status['active_build']['process'].terminate()
            del self.status['active_build']
    
    def poll_build_queue(self):
        self.logger.info("Listening for incoming builds")
        while True:
            if self.redis.llen('build_queue') > 0:
                # pop leftmost item from the message queue
                build_id = self.redis.lpop('build_queue')
                build = Build.objects.get(id=build_id)
                # append build_id onto internal state
                self.status['queue'].append(build)
                self.run_build()
            gevent.sleep(1.0)
    
