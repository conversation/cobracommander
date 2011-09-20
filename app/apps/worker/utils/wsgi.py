from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from django.conf import settings


class WSGIBase(object):
    """
    Setup up basic functions afor WSGI app; dispatch of request response,
    etc...
    """
    def __init__(self):
        self.serve()

    def serve(self):
        """ start server, listen for incoming requests """
        # TODO: settings names are wrong?
        connection = (settings.BUILDRELAY_WEBSOCKET_HOST,
            settings.BUILDRELAY_WEBSOCKET_PORT)
        self.logger.info("Serving on http://%s:%s", connection[0], connection[1])
        self.server = pywsgi.WSGIServer(connection, self.wsgi_app,
            handler_class=WebSocketHandler)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass

    def wsgi_app(self, environ, start_response):
        """ Set up the response cycle """
        response = self.dispatch(Request(environ))
        return response(environ, start_response)

    def dispatch(self, request):
        """
        dispatch the matched request to the view function based on on_*viewname*
        pattern. Will pass websocket object to view if it is present in the
        request environment
        """
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if "wsgi.websocket" in request.environ:
                values['websocket'] = request.environ["wsgi.websocket"]
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e
