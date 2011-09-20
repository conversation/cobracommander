import re, urlparse
import gevent
from django.utils import simplejson
from collections import defaultdict
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

from .utils import get_logger
from .utils.wsgi import WSGIBase
from .utils.json_encoder import ModelJSONEncoder
from .status.status_accessor import StatusAccessor

from .builder import Builder


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
        """ root http request """
        return Response('Sup!? :)')

    def on_status(self, request, websocket=None):
        """
        websocket request for status updates.
        """
        last_updated_status = None
        if websocket:
            initial_connection = True
            while True:
                if websocket.websocket_closed:
                    break
                if initial_connection:
                    initial_connection = False
                    self.logger.info("New client listening on status (%s)",
                        websocket.origin)

                status_changed, status = self.builder_status.update()
                if status_changed or not last_updated_status:
                    last_updated_status = status
                    self.logger.info("status_changed has changed!")
                    websocket.send('status updated')
                    websocket.send(status)
                gevent.sleep(0.25)
        status_changed, status = self.builder_status.update()
        return Response(status)

    def on_build(self, request, build_id):
        return Response('on_build build_id:%s' % build_id)

    def on_build_output(self, request, build_id, websocket=None):
        """
        websocket request for pending or running build.
        """
        if websocket:
            websocket.send('test')
            self.logger.info("Client connected via websocket to on_build_output()")
            if build_id:
                last_index = 0
                redis_key = "build_output_%s" % build_id
                while True:
                    if websocket.websocket_closed:
                        break
                    try:
                        console_length = self.builder.redis.llen(redis_key)
                    except Exception, e:
                        console_length = 0
                        self.logger.warn("Exception: %s", e)
                    if console_length:
                        lines = self.builder.redis.lrange(redis_key, last_index,
                            console_length)
                        lines = filter(None, lines)
                        if lines:
                            last_index = console_length
                            if type(lines) == type(list()):
                                pass
                                websocket.send(simplejson.dumps(lines))
                    gevent.sleep(0.2)
            websocket.close_connection()
