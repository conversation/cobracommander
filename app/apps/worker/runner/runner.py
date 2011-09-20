import redis
import subprocess, shlex, os, time, random, multiprocessing, threading,\
    shutil, datetime hashlib

from collections import defaultdict
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from app.apps.build.models import Step
from app.apps.build.models import Build

from ..utils import get_logger
from .git import Git


class Runner:
    """
    Execute a set of commands serially.
    """
    def __init__(self, build_id, parent_process_queue):
        self.logger = get_logger(__name__)
        self.build = Build.objects.select_related().get(id=build_id)
        self.target = self.build.target
        self.project = self.target.project
        self.parent_process = parent_process_queue
        self.codebase = os.path.join(settings.BUILD_ROOT,
            self.build_project.name_slug)
        self.git = Git(path=self.clone_path)
        self.build_log = list()
        self.build_state = list()
        self.build_steps = []
        self.pass_steps = []
        self.fail_steps = []


    @property
    def redis(self):
        if self._redis_conn == None:
            self._redis_conn = redis.Redis(**settings.REDIS_DATABASE)
        return self._redis_conn

    @property
    def steps(self):
        return {
            'build_steps': self.build_steps,
            'passing_steps': self.pass_steps,
            'failing_steps': self.fail_steps
        }

    def console_output(self, message):
        key = 'build_%s_step_%s_console' % (self.build.id, hashlib.sha1(step).hexdigest()[:6])
        self.push_message(self, self.get_redis_console_key(), message)

    def setup_redis_keys(self, key, **kwargs):
        """
        Create key mappings for redis for this build
        """
        keys = defaultdict({})
        keys['build_steps'] = 'build_%s_steps' % self.build.id

        for step in self.build_steps:

            keys['build_steps_keys'][sha] = step

        keys = {
            'steps':,
            'console':,
        }
        return keys[key]

    def push_message(self, key, message):
        """
        push a message for the build onto the messsage queue
        """
        key = self.get_redis_key_for(key)
        self.redis.rpush(key, message)

    def execute_cmd(self, cmd):
        """
        shell out and run `cmd` within the codebase
        """
        return subprocess.Popen(cmd, cwd=self.clone_path, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def update_codebase(self):
        """
        Check that we have the most recent codebase, and reset hard to the refspec
        that we are building against.
        """
        def path_exists_and_resembles_repo():
            return os.path.exists(self.clone_path) and os.path.exists(
                os.path.join(self.clone_path, '.git'))

        # there seems to be a repo here for this project already, run fetch
        if path_exists_and_resembles_repo():
            cmd = 'git fetch'
        # repo does not seem to exist, we should clone it
        else:
            cmd = 'git clone -v "%s" "%s"' % (self.clone_url, self.clone_path)

        # run the cmd
        self.console_output("running `%s`" % (cmd))
        for line in self.git.run(cmd):
            self.step_console(line)

        # run reset hard against the repo to reset to our build refspec
        cmd = 'git reset --hard "%s"' % (self.build_branch)
        self.push_message("running `%s`" % (cmd))
        for line in self.git.run(cmd):
            self.push_message(line)

    def load_buildsteps(self):
        """
        Try and load ./buildfile from the root of the repo.
        raises BuildfileNotFound if the buildfile does not exist.
        """
        try:
            buildfile_path = os.path.abspath(os.path.join(self.clone_path,
                settings.BUILD_FILE_NAME))
            buildfile = open(buildfile_path, "rb")
            _step = None
            for line in buildfile.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                if line == "[steps]":
                    _step = self.build_steps
                elif line == "[pass]":
                    _step = self.pass_steps
                elif line == "[fail]":
                    _step = self.fail_steps
                elif len(line) > 0 and _step != None:
                    _step.append(line)
            buildfile.close()
        except IOError, e:
            self.push_message("ERROR: Could not load build steps. %s" % (e))

    def start_build(self):
        """
        Execute the build
        """
        self.build.start_datetime = datetime.datetime.now()
        self.update_codebase()
        self.load_buildsteps()
        self.setup_redis_keys()
        self.run_build_steps()
        self.build.end_datetime = datetime.datetime.now()
        self.build.log = "\n".join(self.build_log)
        self.build.save()
        self.push_message("Build completed.")
        self.parent_process.put("COMPLETE", False)

    def run_build_steps(self):
        """
        Run each build step in order and propagate the results to the DB
        """
        for step in self.build_steps:
            self.push_message("STEP: %s" % (step))
            current_step = Step(build=self.build, command=step)

            # shell out and run the step command then handle the response and output
            current_step.start_datetime = datetime.datetime.now()
            step_process = self.execute_cmd(step)
            while step_process.poll() is None:
                line = step_process.stdout.readline()
                if line:
                    line = escape(smart_unicode("%s" % (output.replace("\n", ""))))
                    self.build_log.append(line)
                    self.push_message(line)
                time.sleep(0.01)

            # if the return code shows that the task exited normally then the
            # step passes
            if self.active_step_process.returncode == 0:
                current_step.state = 'c'
                self.build_state.append(True)
                self.push_message("%s" % ('PASSED'))

            # Non-zero returncode means that the step is failing.
            else:
                current_step.state = 'd'
                self.build_state.append(False)
                self.push_message("%s" % ('FAILED'))

            # save the step execution out to the DB
            current_step.end_datetime = datetime.datetime.now()
            current_step.save()





# ----------------------

class BuildRunner:
    def __init__(self, build_id, queue):
        self.logger = get_logger(__name__)
        self.build = Build.objects.get(id=build_id)
        self.build_target = self.build.target
        self.build_project = self.build_target.project
        self.build_branch = 'origin/%s' % self.build_target.branch

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
        print "\nrun_build_steps()"

        for step in self.steps:
            self._exec_step(step)
        time.sleep(5)

    def push_message(self, message):
        """ push a message for the build onto the messsage queue """
        self.redis.rpush(self.redis_key, message)

    def start(self):
        """ start a build """
        print "\nstart()"
        try:
            self.build.start_datetime = datetime.datetime.now()
            self.build.save()
            self.clone()
            self._load_buildsteps()
            self.run_build_steps()
            print "\nrun_build_steps() has returned"
            self.queue.put("COMPLETE", False)
        except Exception, e:
            self.push_message("ERROR: %s" % (e))
            self.queue.put("QUIT", False)
            raise e
        self.build_complete()

    def build_complete(self):
        """ Perform cleanup in redis and propagate relevant stuff to DB. """
        print "\nbuild_complete()"
        self.build.log = "\n".join(self.build_log)
        # self.build.state =
        self.build.end_datetime = datetime.datetime.now()
        self.build.save()
        # remove key from redis, we no longer need it...
        self.push_message("Build completed")
        self.push_message("end")

    def _load_buildsteps(self):
        """
        Try and load the buildfile from the repo.
        If it fails then the build fails and we message why to the user
        """
        print "\n_load_buildsteps()"

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
            self.push_message("Could not load build steps %s" % (e))

    def clone(self):
        """ pull down the remote repo """
        print "\nclone()"

        if os.path.exists(self.clone_path) and os.path.exists(os.path.join(self.clone_path, '.git')):
            cmd = 'git fetch'
            self.push_message("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.push_message(line)
        else:
            cmd = 'git clone -v "%s" "%s"' % (self.clone_url, self.clone_path)
            self.push_message("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.push_message(line)
        cmd = 'git reset --hard "%s"' % (self.build_branch)
        self.push_message("running `%s`" % (cmd))
        output = self.git.run(cmd)
        for line in output:
            self.push_message(line)

    def _exec_step(self, step):
        current_step = Step(build=self.build, command=step)
        self.push_message("STEP: %s" % (step))
        try:
            self.process = subprocess.Popen(
                step,
                cwd=self.clone_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            current_step.state = 'b'
            current_step.save()
            while self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    line = escape(smart_unicode("%s" % (output.replace("\n", ""))))
                    self.build_log.append(line)
                    self.push_message(line)
                time.sleep(0.02)
            if self.process.returncode == 0:
                current_step.state = 'c'
                self.build_state.append(True)
                self.push_message("%s" % ('PASSED'))
            else:
                current_step.state = 'd'
                self.build_state.append(False)
                self.push_message("%s" % ('FAILED'))
            current_step.save()
        except Exception, e:
            self.push_message("Exception: %s" % (e))
            raise e
