import gevent
from collections import defaultdict
from werkzeug.wrappers import Response
from ..status.status_accessor import StatusAccessor


class BuilderStatus(object):
    """docstring for BuilderStatus"""
    def __init__(self, builder):
        self.clients = set()
        self.builder_status = StatusAccessor(builder=builder)
        gevent.spawn(self.update_build_status)

    def __call__(self, request):
        """
        Websocket request for status updates.

        This is called once for every incoming connection. We store the socket in
        a set so that we can still send data over it later on. This method will
        halt until the client disconnects, at which point we pop them off the set.
        """
        websocket = request.environ["wsgi.websocket"]
        if not websocket.websocket_closed:

            # add websocket connection object to stack
            self.clients.add(websocket)

            # always send the status to newly connecting clients
            websocket.send(self.builder_status.get_status())

            while True:
                # wait for messages from the client, handle disconnect
                message = websocket.wait()
                if message == None:
                    # remove disconnecting client from stack
                    websocket.close_connection()
                    self.clients.remove(websocket)
                    break
        return Response('')

    def update_build_status(self):
        while True:
            status_changed, status = self.builder_status.update()
            if status_changed:
                self.broadcast(status)
            gevent.sleep(0.5)

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)
