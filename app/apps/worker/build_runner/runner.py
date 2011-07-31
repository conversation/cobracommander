import subprocess, shlex, os, time


class Runner(object):
    def __init__(self, source_path, steps):
        super(Runner, self).__init__()
        self.source_path = source_path
        self.steps = steps
        self.steps_output = []
    
    def _exec_step(self, step):
        step_output = { 'command':step, 'output':'' }
        try:
            self.process = subprocess.Popen(
                step,
                cwd=self.source_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            while self.process.poll() is None:
                output = self.process.stdout.readline().strip()
                if output:
                    step_output['output'] += output
            step_output['returncode'] = self.process.returncode
        except Exception, e:
            print e
        self.steps_output.append(step_output)
    
    def run(self):
        for step in self.steps:
            self._exec_step(step)
        return self.steps_output