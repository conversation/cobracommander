import redis
import subprocess, shlex, os, time, random, multiprocessing, threading,\
    shutil, datetime

from django.conf import settings
from app.apps.build.models import Step
from app.apps.build.models import Build

from .utils import Git


class BuildRunner:
    def __init__(self, build_id, queue):
        self.build = Build.objects.get(id=build_id)
        self.build_target = self.build.target
        self.build_project = self.build_target.project
        self.build_branch = '%s' % self.build_target.branch

        self.clone_url = self.build_project.url
        self.clone_path = os.path.join(settings.BUILD_ROOT,
            self.build_project.name_slug)
        self.git = Git(path=self.clone_path)

        self.redis = redis.Redis(**settings.REDIS_DATABASE)
        self.redis_key = "build_output_%s" % self.build.id
        self.build_log = list()
        self.build_state = list()
        self.queue = queue
        self.steps = []
        self.pass_steps = []
        self.fail_steps = []
        self.start()
    
    @property
    def steps(self):
        return {
            'build_steps': self.steps,
            'passing_steps': self.pass_steps,
            'failing_steps': self.fail_steps
        }

    def run_build_steps(self):
        """ execute the build command """
        for step in self.steps:
            self._exec_step(step)
    
    def send(self, message):
        """ push a message for the build onto the messsage queue """
        self.redis.rpush(self.redis_key, message)
    
    def start(self):
        """ start a build """
        try:
            self.build.start_datetime = datetime.datetime.now()
            self.build.save()
            self.clone()
            self._load_buildsteps()
            self.run_build_steps()
            self.queue.put("COMPLETE", False)
        except Exception, e:
            self.send("ERROR: %s" % (e))
            self.queue.put("QUIT", False)
            raise e
        self.build_complete()
    
    def build_complete(self):
        """ Perform cleanup in redis and propagate relevant stuff to DB. """
        self.build.log = self.build_log
        # self.build.state = 
        self.build.end_datetime = datetime.datetime.now()
        self.build.save()
        # remove key from redis, we no longer need it...
        self.redis.delete(self.redis_key)
        self.send("Build completed")

    def _load_buildsteps(self):
        """
        Try and load the buildfile from the repo.
        If it fails then the build fails and we message why to the user
        """
        try:
            buildfile_path = os.path.abspath(os.path.join(self.clone_path,
                settings.BUILD_FILE_NAME))
            buildfile = open(buildfile_path, "rb")
            current_step = None
            for line in buildfile.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                if line == "[steps]":
                    current_step = self.steps
                elif line == "[pass]":
                    current_step = self.pass_steps
                elif line == "[fail]":
                    current_step = self.fail_steps
                elif len(line) > 0 and current_step != None:
                    current_step.append(line)
            buildfile.close()
        except IOError, e:
            self.send("Could not load build steps %s" % (e))
    
    def clone(self):
        """ pull down the remote repo """
        if os.path.exists(self.clone_path) and os.path.exists(os.path.join(self.clone_path, '.git')):
            cmd = 'git fetch'
            self.send("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.send(line)
        else:
            cmd = 'git clone -v "%s" "%s"' % (self.clone_url, self.clone_path)
            self.send("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.send(line)
        cmd = 'git reset --hard "%s"' % (self.build_branch)
        self.send("running `%s`" % (cmd))
        output = self.git.run(cmd)
        for line in output:
            self.send(line)
    
    def _exec_step(self, step):
        current_step = Step(build=self.build, command=step)
        self.send("STEP: %s" % (step))
        try:
            self.process = subprocess.Popen(
                step,
                cwd=self.clone_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            current_step.state = 'b'
            current_step.save()
            while self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    line = "%s" % (output)
                    self.build_log.append(line)
                    self.send(line)
                time.sleep(0.5)
            if self.process.returncode == 0:
                current_step.state = 'c'
                self.build_state.append(True)
                self.send("%s" % ('PASSED'))
            else:
                current_step.state = 'd'
                self.build_state.append(False)
                self.send("%s" % ('FAILED'))
            current_step.save()
        except Exception, e:
            self.send("Exception: %s" % (e))
            raise e