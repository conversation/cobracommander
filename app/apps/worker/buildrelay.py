import re, json, urlparse, logging

import gevent
from collections import defaultdict
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

from .utils import get_logger
from .wsgi import WSGIBase
from .builder import Builder


class StatusAccessor(object):
    def __init__(self, builder):
        self.has_changed = False
        self.builder = builder
        self.status = defaultdict(dict)
        self.status_keys = ('state', 'build_queue', 'active_build',)
        
    def _update_value_for_key(self, key, new_value):
        if self.status.get(key) != new_value:
            self.status[key] = new_value
            self.has_changed = True
    
    def update(self):
        self.has_changed = False
        for key in self.status_keys:
            self._update_value_for_key(key, getattr(self, 'get_' + key)())
        return (self.has_changed, self.status)
    
    def get_state(self):
        return self.builder.status['state']
    
    def get_build_queue(self):
        return self.builder.status['build_queue']
    
    def get_active_build(self):
        if 'active_build' in self.builder.status:
            return self.builder.status['active_build'].get('build')
        return None


class BuildRelay(WSGIBase):
    """
    BuildRelay runs a WSGI server and listens for connections over websockets.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        self.url_map = Map([
            Rule('/', endpoint='root'),
            Rule('/status', endpoint='status'),
            Rule('/build/<build_id>', endpoint='build'),
            Rule('/build/<build_id>/console', endpoint='build_output'),
            Rule('/build/<build_id>/stop', endpoint='build_stop')
        ])
        self.builder = Builder()
        self.builder_status = StatusAccessor(builder=self.builder)
        super(BuildRelay, self).__init__()

    def on_root(self, request):
        return Response('Sup!? :)')
    
    def on_status(self, request, websocket=None):
        initial_connection = True
        if websocket:
            while True:
                status_changed, status = self.builder_status.update()
                if status_changed or initial_connection:
                    initial_connection = False
                    websocket.send(json.dumps(status))
                gevent.sleep(2)
        status_changed, status = self.builder_status.update()
        return Response(json.dumps(status))
    
    def on_build(self, request, build_id):
        return Response('on_build build_id:%s' % build_id)
    
    def on_build_output(self, request, build_id, websocket=None):
        if websocket:
            self.logger.debug("Client connected via websocket to on_build_output()")
            if build_id:
                last_index = 0
                redis_key = "build_output_%s" % build_id
                while True:
                    try:
                        console_length = self.builder.redis.llen(redis_key)
                    except Exception, e:
                        console_length = 0
                        self.logger.warn("Exception: %s", e)
                    if console_length:
                        lines = self.builder.redis.lrange(redis_key, last_index,
                            console_length)
                        if lines:
                            last_index = console_length
                            if type(lines) == type(list()):
                                for line in lines:
                                    websocket.send('<div>%s</div>' % line)
                    gevent.sleep(0.5)
            websocket.close()