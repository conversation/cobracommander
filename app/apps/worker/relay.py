import eventlet
from eventlet import wsgi
from eventlet import websocket

class BuildWebsocketRelay(object):
    """
    
    """
    def __init__(self, port, path, queue):
        self.port = int(port)
        self.path = path
        self.queue = queue
        print "listener starting on 127.0.0.1:%s" % self.port
        listener = eventlet.listen(('127.0.0.1', self.port))
        wsgi.server(listener, self.dispatch)
    
    def dispatch(self, environ, start_response):
        if environ['PATH_INFO'] == self.path:
            return self.handle(environ, start_response)
    
    @websocket.WebSocketWSGI
    def handle(self, ws):
        if ws.path == self.path:
            while True:
                message = ws.wait()
                if message is None:
                    break
                ws.send(message)
    
    def kill(self):
        return