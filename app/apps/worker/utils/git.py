from django.conf import settings
import os, subprocess


# TODO: replace with dulwich or somthing less completely crap
class Git(object):
    """ Shell out and run git commands from the build root """
    def __init__(self, path):
        super(Git, self).__init__()
        self.path = path
    
    def _check_cmd_path_prefix(self):
        self.cmd_path_prefix = ""
        if os.path.exists(self.path):
            self.cmd_path_prefix ='cd "%s" && ' % self.path
    
    def run(self, command):
        self._check_cmd_path_prefix()
        cmd = "%s%s" % (self.cmd_path_prefix, command)
        proc = subprocess.Popen(
            cmd,
            cwd=settings.BUILD_ROOT,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc.communicate()