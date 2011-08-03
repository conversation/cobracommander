import subprocess, shlex, os, time
from app.apps.build.models import Step

class Runner(object):
    def __init__(self, source_path, steps, build):
        super(Runner, self).__init__()
        self.source_path = source_path
        self.steps = steps
        self.steps_output = []
        self.build = build
    
    def _exec_step(self, step):
        current_step = Step(build=self.build, command=step)
        current_step.save()
        step_output = { 'command':step, 'output':'' }
        try:
            self.process = subprocess.Popen(
                step,
                cwd=self.source_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            current_step.state = 'b'
            current_step.save()
            while self.process.poll() is None:
                output = self.process.stdout.readline().strip()
                if output:
                    step_output['output'] += output
                    current_step.output += output + "\n"
                    current_step.save()
            if self.process.returncode == 0:
                current_step.state = 'c'
            else:
                current_step.state = 'd'
            current_step.save()
            step_output['returncode'] = self.process.returncode
        except Exception, e:
            print e
            current_step.output += e + "\n"
            current_step.state = 'd'
            current_step.save()
        self.steps_output.append(step_output)
    
    def run(self):
        for step in self.steps:
            self._exec_step(step)
        return self.steps_output
