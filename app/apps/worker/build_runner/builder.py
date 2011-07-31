from django.conf import settings
import os
from multiprocessing import Process, Pipe
import git
import shutil
import threading
import time

from .runner import Runner


class Builder:
    def __init__(self, build):
        self.git = git.Git()
        self.build = build
        self.build_project = build.project
        self.remote = self.build_project.repo_clone_url
        self.build_branch = 'origin/%s' % self.build_project.branch
        self.clone_path = os.path.join(settings.BUILD_ROOT, self.build_project.name)
        self.steps = []
        self.pass_steps = []
        self.fail_steps = []
    
    def _load_buildsteps(self):
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
            raise e
    
    def clone(self):
        """
        pull down the remote repo
        """
        if os.path.exists(self.clone_path):
            if git.repo.fun.is_git_dir(os.path.join(self.clone_path, '.git')):
                os.chdir(self.clone_path)
                self.git.fetch()
            else:
                raise False
        else:
            self.git.clone(self.remote, self.clone_path)
        
        self.repo = git.Repo(self.clone_path)
        os.chdir(self.clone_path)
        self.git.reset('--hard', self.build_branch)
        head = self.repo.heads[0]
        head_commit = head.commit
    
    
    def start_runner(self):
        """
        execute the build command
        """
        self.runner = Runner(source_path=self.clone_path, steps=self.steps, build=self.build)
        print self.runner.run(self.build)
    
    
    def start(self):
        """
        start a build
        """
        self.clone()
        self._load_buildsteps()
        self.start_runner()
    
    
    def stop(self):
        """
        stop the build process
        """
        if hasattr(self, 'job') and self.job is not None:
            self.runner.terminate()