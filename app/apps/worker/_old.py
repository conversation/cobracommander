from gevent import monkey
monkey.patch_all()

import redis
import re, json, urlparse, logging
import gevent
from gevent import pywsgi
from gevent import queue
from geventwebsocket.handler import WebSocketHandler
from multiprocessing import Process, Queue
from collections import defaultdict

from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

from django.conf import settings
from app.apps.build.models import Build
from runner.buildrunner import BuildRunner


class BuildRelayBaseclass(object):
    """
    Base class for BuildRelay to set up server and dispatch requests
    """
    def __init__(self):
        """
        start the wsgi server
        """
        self._connect_redis()
        gevent.spawn(self.listen_to_build_queue)
        self._start_server()
    
    def _start_server(self):
        connection = (settings.BUILDRELAY_WEBSOCKET_HOST,
            settings.BUILDRELAY_WEBSOCKET_PORT)
        self.logger.info("serving on %s:%s", connection[0], connection[1])
        self.server = pywsgi.WSGIServer(connection, self.wsgi_app,
            handler_class=WebSocketHandler)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass

    def _connect_redis(self):
        """ set up connection to redis """
        self.logger.info("connecting to redis on %(host)s:%(port)s db:%(db)s",
            settings.REDIS_DATABASE)
        self.redis = redis.Redis(**settings.REDIS_DATABASE)

    def dispatch_request(self, request):
        """
        dispatch the matched request to the view function
        """
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if "wsgi.websocket" in request.environ:
                values['websocket'] = request.environ["wsgi.websocket"]
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

    def wsgi_app(self, environ, start_response):
        """
        Set up the response cycle
        """
        response = self.dispatch_request(Request(environ))
        return response(environ, start_response)
    
    def start_build(self):
        """docstring for start_build"""
        queue = Queue()
        build = self.queue.pop(0)
        self.internal_status['active_build']['build'] = build
        self.internal_status['active_build']['worker'] = Process(name='worker-%s' % build.id,
            target=Builder, args=(build.id, queue))
        self.internal_status['active_build']['worker'].start()
        while True:
            try:
                message = queue.get(False)
                if message == "QUIT":
                    self.stop_build()
                    break
                print message
            except Exception, e: # Queue.Empty?
                pass
            gevent.sleep(0.5)
        self.stop_build()
    
    def stop_build(self):
        self.logger.info("build id:%s completed, ready to build again.",
            (self.internal_status['active_build']['build'].id))
        self.internal_status['active_build']['worker'].terminate()
        del self.internal_status['active_build']

    def listen_to_build_queue(self):
        """
        listen on the build queue for newly submitted builds
        """
        self.logger.info("listening for incoming builds")
        while True:
            try:
                if self.redis.llen('build_queue') > 0:
                    # pop build id off build_queue and add corresponding Build
                    # object to internal queue 
                    build_id = self.redis.lpop('build_queue')
                    build = Build.objects.get(id=build_id)
                    self.queue.append(build)

                    if self.current_build == None:
                        self.logger.info("starting new build worker")
                        self.start_build()
                    elif isinstance(self.current_build, Process) and not self.current_build.is_alive():
                        self.start_build()
            except Exception, e:
                pass
            gevent.sleep(0.5)



class BuildRelay(BuildRelayBaseclass):
    """
    
    """
    def __init__(self):
        self._init_logger()
        self.url_map = Map([
            Rule('/', endpoint='root'),
            Rule('/status', endpoint='status'),
            Rule('/builds', endpoint='builds'),
            Rule('/build/<build_id>', endpoint='build'),
            Rule('/build/<build_id>/console', endpoint='build_output')
        ])
        self.queue = list()
        self.internal_status = defaultdict(list)
        self.status = defaultdict(None)
        self.logger.info("Starting Build Relay...")
        super(BuildRelay, self).__init__()
        
    def _init_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s:%(asctime)s - %(name)s: %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_state(self):
        return 'test'
    
    def get_build_queue(self):
        """
        Returns a queryset of build model objects from 'build_queue' ids.
        """
        build_queue_build_ids = self.redis.lrange('build_queue', 0, -1)
        return list(Build.objects.filter(id__in=build_queue_build_ids))
    
    def get_active_build(self):
        return 'test2'

    def on_root(self, request):
        return Response('Sup!? :)')
    
    def on_status(self, request, websocket=None):
        """ """
        status_keys = ['state', 'build_queue', 'active_build']

        def update_status():
            """ """
            status_has_changed = False
            def update_at_key(key, new_value):
                if self.status.get(key) != new_value:
                    self.status[key] = new_value
                    print 'test'
                    status_has_changed = True
            
            for key in status_keys:
                update_at_key(key, getattr(self, 'get_' + key)())
            print status_has_changed
            return status_has_changed
        
        if websocket:
            while True:
                if update_status():
                    websocket.send(json.dumps(self.status))
                gevent.sleep(2)
        return Response('')
    
    def on_builds(self, request):
        """ return json response of current build """
        return Response('on_builds')

    def on_build(self, request, build_id):
        return Response('on_build build_id:%s' % build_id)
    
    def on_build_output(self, request, build_id, websocket=None):
        """
        Streams the output of the console for the build back to the client over
        a websocket connection. This 
        """
        if websocket:
            if build_id:
                last_index = 0
                key = "build_output_%s" % build_id
                while True:
                    try:
                        console_length = self.redis.llen(key)
                    except Exception, e:
                        console_length = 0
                        pass
                    if console_length:
                        lines = self.redis.lrange(key, last_index, console_length)
                        if lines:
                            last_index = console_length
                            if type(lines) == type(list()):
                                for line in lines:
                                    websocket.send('<div>%s</div>' % line)
                    gevent.sleep(0.5)
            
            websocket.close()
        return Response('')

