import redis
import subprocess, shlex, os, time, random, multiprocessing, threading,\
    shutil, datetime, hashlib

from collections import defaultdict
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils import simplejson
from django.utils.html import escape
from functools import wraps
import dateutil.parser

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
            self.project.name_slug)
        self.git = Git(path=self.codebase)
        self._redis_conn = None
        self.build_log = list()
        self.build_state = list()
        self.build_steps = list()
        self.pass_steps = list()
        self.fail_steps = list()
        self.run()

    @property
    def redis(self):
        if self._redis_conn == None:
            self._redis_conn = redis.Redis(**settings.REDIS_DATABASE)
        return self._redis_conn

    @property
    def steps(self):
        return {
            'build_steps': dict(self.build_steps),
            'passing_steps': dict(self.pass_steps),
            'failing_steps': dict(self.fail_steps)
        }

    def _stage(stage):
        """"""
        def factory(func):
            @wraps(func)
            def decorator(self):
                self._console_output_stage(stage)
                return func(self)
            return decorator
        return factory

    def _console_output_stage(self, stage):
        self.console_output_stage = stage

    def console_output(self, data):
        self.push_data({
            'type':'console',
            'data':data
        })

    def push_data(self, data):
        """
        push a message for the build onto the messsage queue
        """
        data['stage'] = self.console_output_stage
        self.redis.rpush("build_%s_output" % self.build.id, simplejson.dumps(data))

    def execute_cmd(self, cmd):
        """
        shell out and run `cmd` within the codebase
        """
        return subprocess.Popen(cmd, cwd=self.codebase, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def update_codebase(self):
        """
        Check that we have the most recent codebase, and reset hard to the refspec
        that we are building against.
        """
        def path_exists_and_resembles_repo():
            return os.path.exists(self.codebase) and os.path.exists(
                os.path.join(self.codebase, '.git'))

        # there seems to be a repo here for this project already, run fetch
        if path_exists_and_resembles_repo():
            cmd = 'git fetch'
        # repo does not seem to exist, we should clone it
        else:
            cmd = 'git clone -v "%s" "%s"' % (self.project.url, self.codebase)

        # run the cmd
        self.console_output("running `%s`" % (cmd))
        for line in self.git.run(cmd):
            self.console_output(line)

        # run reset hard against the repo to reset to our build refspec
        cmd = 'git reset --hard "%s"' % (self.target.branch)
        self.console_output("running `%s`" % (cmd))
        for line in self.git.run(cmd):
            self.console_output(line)

        # send the refspec and repo status to the client
        cmd = "git log -n 1 --pretty='format:%h|%d|%ci|%an|%ae|%s'"
        git_log = self.git.run(cmd)
        git_log = dict(zip(['refspec', 'refs', 'date', 'author_name',
            'author_email', 'message'], git_log[0].split('|')))
        git_log['message'] = escape(smart_unicode(git_log['message']))
        self.push_data({
            'type':'refspec',
            'data':git_log
        })

    def load_buildsteps(self):
        """
        Try and load ./buildfile from the root of the repo.
        raises BuildfileNotFound if the buildfile does not exist.
        """
        try:
            buildfile_path = os.path.abspath(os.path.join(self.codebase,
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
                    _step.append((hashlib.sha1(line).hexdigest()[:6], line,))
            buildfile.close()

            # send the loaded buildsteps back to the client
            self.push_data({
                'type':'build_steps',
                'data':self.steps
            })
        except IOError, e:
            self.console_output("ERROR: Could not load build steps. %s" % (e))

    @_stage('build')
    def run_build_steps(self):
        """
        Run each build step in order and propagate the results to the DB
        """
        for sha, step in self.build_steps:
            current_step = Step(build=self.build, command=step,
                start_datetime=datetime.datetime.now())

            self.push_data({
                'type':'step_start',
                'step_hash':sha,
                'step':step
            })

            # shell out and run the step command then handle the response and output
            step_process = self.execute_cmd(step)
            while step_process.poll() is None:
                line = step_process.stdout.readline()
                if line:
                    line = escape(smart_unicode("%s" % (line.replace("\n", ""))))
                    self.build_log.append(line)
                    self.console_output(line)
                time.sleep(0.01)

            # if the return code shows that the task exited normally then the
            # step passes
            if step_process.returncode == 0:
                current_step.state = 'c'
                self.build_state.append(True)

            # Non-zero returncode means that the step is failing.
            else:
                current_step.state = 'd'
                self.build_state.append(False)

            self.push_data({
                'type':'step_complete',
                'step_hash':sha,
                'state':current_step.get_state_display()
            })

            # save the step execution out to the DB
            current_step.end_datetime = datetime.datetime.now()
            current_step.save()

    @_stage('setup')
    def setup(self):
        self.build.start_datetime = datetime.datetime.now()
        self.update_codebase()
        self.load_buildsteps()

    @_stage('teardown')
    def teardown(self):
        self.build.end_datetime = datetime.datetime.now()
        self.build.log = "\n".join(self.build_log)
        self.build.save()
        self.console_output("Build completed.")
        self.parent_process.put("COMPLETE", False)

    def run(self):
        """
        Execute the build
        """
        self.setup()
        self.run_build_steps()
        self.teardown()





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

    def push_data(self, message):
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
            self.push_data("ERROR: %s" % (e))
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
        self.push_data("Build completed")
        self.push_data("end")

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
            self.push_data("Could not load build steps %s" % (e))

    def clone(self):
        """ pull down the remote repo """
        print "\nclone()"

        if os.path.exists(self.clone_path) and os.path.exists(os.path.join(self.clone_path, '.git')):
            cmd = 'git fetch'
            self.push_data("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.push_data(line)
        else:
            cmd = 'git clone -v "%s" "%s"' % (self.clone_url, self.clone_path)
            self.push_data("running `%s`" % (cmd))
            output = self.git.run(cmd)
            for line in output:
                self.push_data(line)
        cmd = 'git reset --hard "%s"' % (self.build_branch)
        self.push_data("running `%s`" % (cmd))
        output = self.git.run(cmd)
        for line in output:
            self.push_data(line)

    def _exec_step(self, step):
        current_step = Step(build=self.build, command=step)
        self.push_data("STEP: %s" % (step))
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
                    self.push_data(line)
                time.sleep(0.02)
            if self.process.returncode == 0:
                current_step.state = 'c'
                self.build_state.append(True)
                self.push_data("%s" % ('PASSED'))
            else:
                current_step.state = 'd'
                self.build_state.append(False)
                self.push_data("%s" % ('FAILED'))
            current_step.save()
        except Exception, e:
            self.push_data("Exception: %s" % (e))
            raise e
