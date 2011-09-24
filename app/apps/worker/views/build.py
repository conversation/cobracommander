import gevent
import redis
from django.conf import settings
from django.utils import simplejson
from werkzeug.wrappers import Response


class BuildConsole(object):
    """docstring for BuilderStatus"""
    def __init__(self):
        self.clients = set()
        self.redis_connection = None
        self.console_buffer = []
        self.build_updater = None


    def __call__(self, request, build_id):

        self.build_id = build_id
        if self.build_updater == None:
            self.build_updater = gevent.spawn(self.update_build_log)

        websocket = request.environ["wsgi.websocket"]
        if not websocket.websocket_closed:

            # add websocket connection object to stack
            self.clients.add(websocket)

            # always send the status to newly connecting clients
            websocket.send(simplejson.dumps(self.console_buffer))

            while True:
                # wait for messages from the client, handle disconnect
                message = websocket.wait()
                if message == None:
                    # remove disconnecting client from stack
                    websocket.close_connection()
                    self.clients.remove(websocket)
                    break
        return Response('')

    @property
    def redis(self):
        if self.redis_connection == None:
            self.redis_connection = redis.Redis(**settings.REDIS_DATABASE)
        return self.redis_connection

    def update_build_log(self):
        redis_key = "build_%s_output" % self.build_id
        last_index = 0
        console_length = 0
        while True:
            console_length = self.redis.llen(redis_key)
            if console_length:
                lines = self.redis.lrange(redis_key, last_index,
                            console_length)
                lines = filter(None, lines)
                if lines:
                    last_index = console_length
                    if type(lines) == type(list()):
                        self.console_buffer += lines
                        self.broadcast(simplejson.dumps(lines))
            gevent.sleep(0.05)

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)


def stop(request, build_id):
    return Response('Build stop id:%s.' % (build_id))
