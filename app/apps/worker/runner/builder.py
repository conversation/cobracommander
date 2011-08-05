from gevent import monkey
monkey.patch_all()
# import gevent

from django.conf import settings
import os
# from multiprocessing import Process, Pipe
import shutil
import threading
import redis
import random
import subprocess, shlex, os, time

from app.apps.build.models import Step
from app.apps.build.models import Build


class Git(object):
    """docstring for Git"""
    def __init__(self, path):
        super(Git, self).__init__()
        self.path = path
    
    def run(self, command):
        """docstring for run"""
        proc = subprocess.Popen(
            command,
            cwd=settings.BUILD_ROOT,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return proc


class Builder:
    def __init__(self, id):
        self.build = Build.objects.get(id=id)
        self.build_project = self.build.project
        self.remote = self.build_project.repo_clone_url
        self.build_branch = 'origin/%s' % self.build_project.branch
        self.clone_path = os.path.join(settings.BUILD_ROOT, self.build_project.name_slug)
        self.git = Git(path=self.clone_path)
        self.redis = redis.Redis(**settings.REDIS_DATABASE)
        self.redis_key = "build_output_%s" % self.build.id
        self.steps = []
        self.pass_steps = []
        self.fail_steps = []
        self.send('Builder.__init__()')
        self.start()
    
    def start_runner(self):
        """
        execute the build command
        """
        for step in self.steps:
            self._exec_step(step)
    
    def send(self, message):
        """
        push a message for the build onto the messsage queue
        """
        self.redis.rpush(self.redis_key, message)
    
    def start(self):
        """
        start a build
        """
        
        try:
            self.send("running: self.clone()")
            self.clone()
            
            self.send("running: self._load_buildsteps()")
            self._load_buildsteps()
            
            self.send("running: self.start_runner()")
            self.start_runner()
        except Exception, e:
            self.send("ERROR: %s" % (e))
            raise e
    
    def stop(self):
        """
        stop the build process
        """
        if hasattr(self, 'job') and self.job is not None:
            self.runner.terminate()
    
    def _load_buildsteps(self):
        """
        Try and load the buildfile from the repo.
        If it fails then the build fails and we message why to the user
        """
        try:
            buildfile_path = os.path.abspath(os.path.join(self.clone_path, settings.BUILD_FILE_NAME))
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
        except Exception, e:
            self.send("Could not load build steps %s" % (e))
            raise e
    
    def clone(self):
        """
        pull down the remote repo
        """
        if os.path.exists(self.clone_path):
            cmd = 'git fetch'
            self.send("running `%s`" % (cmd))
            git_fetch = self.git.run(cmd)
        else:
            cmd = 'git clone %s %s' % (self.remote, self.clone_path)
            self.send("running `%s`" % (cmd))
            git_clone = self.git.run(cmd)
        
        cmd = 'git reset --hard %s' % (self.build_branch)
        self.send("running `%s`" % (cmd))
        git_reset = self.git.run(cmd)
    
    def _exec_step(self, step):
        current_step = Step(build=self.build, command=step)
        self.send("Running step: %s" % (step))
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
                output = self.process.stdout.readline().strip()
                if output:
                    self.send("%s" % (output))
            if self.process.returncode == 0:
                current_step.state = 'c'
                self.send("%s" % ('PASSED'))
            else:
                current_step.state = 'd'
                self.send("%s" % ('FAILED'))
            current_step.save()
        except Exception, e:
            raise e