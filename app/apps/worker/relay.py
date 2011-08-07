from gevent import monkey
monkey.patch_all()

from django.conf import settings
import gevent
from gevent import pywsgi
from gevent import queue
from geventwebsocket.handler import WebSocketHandler
from multiprocessing import Process, Queue
import redis
import re

from runner.builder import Builder

class BuildRelay(object):
    """
    
    """
    def __init__(self):
        self.current_build = None
        
        self._connect_redis()
        gevent.spawn(self.build_queue_listener)
        self._init_server()
    
    
    def _connect_redis(self):
        """
        Connect to redis
        """
        print "connecting to redis on %(host)s:%(port)s db:%(db)s" % settings.REDIS_DATABASE
        self.redis = redis.Redis(**settings.REDIS_DATABASE)
    
    
    def _init_server(self):
        """
        start the wsqi server
        """
        
        connection = (settings.BUILDRELAY_WEBSOCKET_HOST,
            settings.BUILDRELAY_WEBSOCKET_PORT)
        print "serving on %s:%s" % connection
        self.server = pywsgi.WSGIServer(connection, self._route,
            handler_class=WebSocketHandler)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
    
    
    def start_build(self):
        """docstring for start_build"""
        build_id = self.redis.lpop('build_queue')
        queue = Queue()
        self.current_build = Process(
            name='builder-%s' % build_id,
            target=Builder,
            args=(build_id, queue)
        )
        self.current_build.start()
        while True:
            try:
                message = queue.get(False)
                if message == "QUIT":
                    self.current_build.terminate()
                    self.current_build = None
                    print "build id:%s completed - ready to build again." % (build_id)
                    break
                print message
            except Exception, e: # Queue.Empty
                pass
            gevent.sleep(0.5)
    
    
    def build_queue_listener(self):
        """
        listen on the build queue for newly submitted builds
        """
        print "listening for incoming builds"
        
        while True:
            if self.redis.llen('build_queue') > 0:
                if self.current_build == None:
                    print "starting new build worker."
                    self.start_build()
                elif isinstance(self.current_build, Process) and not self.current_build.is_alive():
                    self.start_build()
            gevent.sleep(0.5)
    
    
    def _route(self, environ, start_response):
        """
        route requests
        """
        
        request_path = environ["PATH_INFO"]
        
        if "wsgi.websocket" in environ:
            websocket = environ["wsgi.websocket"]
            if request_path.startswith('/worker'):
                return self.worker_console(start_response, websocket)
        else:
            if request_path == '/':
                start_response('200 OK', [('Content-Type', 'text/plain')])
                return ['Sup? :-)']
            if request_path == '/status':
                return self.relay_status(start_response)
        
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['404 Not Found']
    
    
    def relay_status(self, start_response):
        """docstring for status"""
        start_response('200 OK', [('Content-Type', 'text/plain')])
        body = list()
        body.append("status: running.")
        body.append(" - builds in queue: %s" % (self.redis.llen('build_queue')))
        body.append(' - current_build: %s' % self.current_build)
        return body
    
    
    def worker_console(self, start_response, websocket):
        """docstring for status"""
        
        websocket.send('connected...')
        
        path_build_id = re.match(r'/worker/build/(?P<build_id>[\d]+)/console/', websocket.path)
        build_id = path_build_id.groupdict().get('build_id')
        
        if build_id:
            last_index = 0
            key = "build_output_%s" % build_id
            
            while True:
                console_length = self.redis.llen(key)
                lines = self.redis.lrange(key, last_index, console_length)
                if lines:
                    last_index = console_length
                    if type(lines) == type(list()):
                        for line in lines:
                            websocket.send('<div>%s</div>' % line)
                gevent.sleep(0.5)
        
        elif websocket.path == '/worker/test':
            import os
            import random
            for i in xrange(10000):
                websocket.send("0 %s %s\n" % (i, random.random()))
                gevent.sleep(0.5)

