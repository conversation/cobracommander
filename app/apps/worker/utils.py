from django.conf import settings
import subprocess, logging

def get_logger(name):
    logging.basicConfig(level=logging.DEBUG, 
        format='[%(asctime)s] %(name)-28s %(levelname)-12s %(message)s')
    return logging.getLogger(name)


class Git(object):
    """ Shell out and run git commands from the build root """
    def __init__(self, path):
        super(Git, self).__init__()
        self.path = path
    
    def run(self, command):
        return subprocess.Popen(
            command,
            cwd=settings.BUILD_ROOT,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )