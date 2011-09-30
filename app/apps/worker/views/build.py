import gevent
import redis
from collections import defaultdict
from django.conf import settings
from django.utils import simplejson
from werkzeug.wrappers import Response


class BuildConsole(object):
    """docstring for BuilderStatus"""
    def __init__(self):
        self.redis_connection = None
        self.clients = defaultdict(set)
        self.console_buffer = defaultdict(list)
        self.build_updater = defaultdict(list)

    def __call__(self, request, build_id):
        """"""
        # create a build updater process for this build if it does not exist.
        if not self.build_updater[build_id]:
            self.build_updater[build_id] = gevent.spawn(self.update_build_log,
                build_id=build_id)

        websocket = request.environ["wsgi.websocket"]
        if not websocket.websocket_closed:

            # add websocket connection object to stack
            self.clients[build_id].add(websocket)

            # always send the status to newly connecting clients
            websocket.send(simplejson.dumps(self.console_buffer[build_id]))

            while True:
                # wait for messages from the client, handle disconnect
                message = websocket.wait()
                if message == None:
                    # remove disconnecting client from stack
                    websocket.close_connection()
                    self.clients[build_id].remove(websocket)

                    # clean up internal pointers if there are no clients.
                    if len(self.clients[build_id]) == 0:
                        del self.clients[build_id]
                        del self.console_buffer[build_id]
                        self.build_updater[build_id].kill()
                        del self.build_updater[build_id]
                    break
        return Response('')

    @property
    def redis(self):
        if self.redis_connection == None:
            self.redis_connection = redis.Redis(**settings.REDIS_DATABASE)
        return self.redis_connection

    def update_build_log(self, build_id):
        redis_key = "build_%s_output" % build_id
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
                        lines = map(simplejson.loads, lines)
                        self.console_buffer[build_id] += lines
                        for line in lines:
                            for client in self.clients[build_id]:
                                client.send(simplejson.dumps(line))

            gevent.sleep(0.05)

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

def stop(request, build_id):
    return Response('Build stop id:%s.' % (build_id))
