from gevent import monkey
monkey.patch_all()

from django.conf import settings
import gevent
from gevent import pywsgi
from gevent import queue
from geventwebsocket.handler import WebSocketHandler
import redis
import re

from runner.builder import Builder

class BuildRelay(object):
    """
    
    """
    def __init__(self):
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
        self.server.serve_forever()
    
    
    def build_queue_listener(self):
        """
        listen on the build queue for newly submitted builds
        """
        print "listening for incoming builds"
        client = self.redis.pubsub()
        client.subscribe('build_queue')
        self.build_queue = client.listen()
        
        while True:
            build = self.build_queue.next()
    
    
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
        return [
            "status: running.",
            " - builds in queue: %s" % (self.redis.llen('build_queue'))
        ]
    
    
    def worker_console(self, start_response, websocket):
        """docstring for status"""
        
        path_build_id = re.match(r'/worker/build/(?P<build_id>[\d]+)/console/', websocket.path)
        build_id = path_build_id.groupdict().get('build_id')
        
        if build_id:
            websocket.send("build_id: %s" % (build_id))
            self.current_build = Builder(id=build_id)
            self.current_build.start()
            
            last_index = 0
            key = "build_output_%s" % self.build.id
            
            while True:
                console_length = self.redis.llen(key)
                lines = self.redis.lrange(key, last_index, console_length)
                if line:
                    last_index = console_length
                    for line in lines:
                        websocket.send(line)
                gevent.sleep(0.01)
        
        elif websocket.path == '/worker/test':
            import os
            import random
            for i in xrange(10000):
                websocket.send("0 %s %s\n" % (i, random.random()))
                gevent.sleep(0.01)


# 
# class BuildRelay(object):
#     """
#     
#     """
#     def __init__(self, port, path, queue):
#         self.port = int(port)
#         self.path = path
#         self.queue = queue
#         print "listener starting on 127.0.0.1:%s" % self.port
#         listener = eventlet.listen(('127.0.0.1', self.port))
#         wsgi.server(listener, self.dispatch)
#     
#     def dispatch(self, environ, start_response):
#         if environ['PATH_INFO'] == self.path:
#             return self.handle(environ, start_response)
#     
#     @websocket.WebSocketWSGI
#     def handle(self, ws):
#         if ws.path == self.path:
#             while True:
#                 message = ws.wait()
#                 if message is None:
#                     break
#                 ws.send(message)
#     
#     def kill(self):
#         return