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
        self.target = self.build.target_set.all()[0]
        self.parent_process = parent_process_queue
        self.codebase = os.path.join(settings.BUILD_ROOT,
            self.build.project_name_slug)
        self.git = Git(path=self.codebase)
        self._redis_conn = None
        self.build_log = list()
        self.build_state = list()
        self.build_steps = list()
        self.pass_steps = list()
        self.fail_steps = list()
        self.stage_output_buffer = defaultdict(list)
        self.run()

    @property
    def redis(self):
        if self._redis_conn == None:
            self._redis_conn = redis.Redis(**settings.REDIS_DATABASE)
        return self._redis_conn

    @property
    def steps(self):
        return {
            'build_steps': (self.build_steps),
            'passing_steps': (self.pass_steps),
            'failing_steps': (self.fail_steps)
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
        self.stage_output_buffer[self.console_output_stage] += data
        self.push_data({
            'type':'console',
            'data':data
        })

    def push_data(self, data):
        """
        push a message for the build onto the messsage queue
        """
        data['stage'] = self.console_output_stage
        try:
            lines = data['data']
            lines = lines.replace("\n", "")
            lines = smart_unicode(lines)
            lines = escape(lines)
            data['data'] = lines
        except Exception, e:
            pass
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
            cmd = 'git clone -v "%s" "%s"' % (self.build.project.url, self.codebase)

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
                start_datetime=datetime.datetime.now(), sha=sha)

            self.push_data({
                'type':'step_start',
                'step_hash':sha,
                'step':step
            })

            # shell out and run the step command then handle the response and output
            step_output = list()
            step_process = self.execute_cmd(step)
            while step_process.poll() is None:
                line = step_process.stdout.readline()
                if line:
                    step_output.append(line)
                    self.console_output(line)
                time.sleep(0.01)
            self.build_log += step_output

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
            current_step.log = "\n".join(step_output)
            current_step.save()

    @_stage('setup')
    def setup(self):
        setup_step = Step(type='a', build=self.build, command='setup',
                start_datetime=datetime.datetime.now())
        self.build.start_datetime = datetime.datetime.now()
        self.update_codebase()
        self.load_buildsteps()
        setup_step.log = "\n".join(self.stage_output_buffer['setup'])
        setup_step.end_datetime = datetime.datetime.now()
        setup_step.save()


    @_stage('teardown')
    def teardown(self):
        self.build.end_datetime = datetime.datetime.now()
        self.build.log = "\n".join(self.build_log)
        duration_delta = self.build.end_datetime - self.build.start_datetime
        self.build.duration_ms = duration_delta.seconds*1000000 + duration_delta.microseconds
        if False in self.build_state:
            self.build.state = 'd'
        else:
            self.build.state = 'c'
        self.build.save()
        self.console_output("Build completed.")
        self.redis.delete("build_%s_output" % self.build.id)
        self.parent_process.put("COMPLETE", False)

    def run(self):
        """
        Execute the build
        """
        self.setup()
        self.run_build_steps()
        self.teardown()

