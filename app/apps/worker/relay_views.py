from gevent import queue

def relay_status():
    """docstring for status"""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    
    body = queue.Queue()
    body.put(' ' * 1000)
    body.put("status")
    
    return body


def worker_console(websocket):
    """docstring for status"""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    
    body = queue.Queue()
    body.put(' ' * 1000)
    body.put("websocket")
    
    return body