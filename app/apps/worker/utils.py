class BuildSteps():
  def extract_from_file(self, file):
    steps = []
    pass_steps = []
    fail_steps = []
    current_step = None
    for line in file:
      line = line.rstrip().lstrip()
      if line.startswith("#"):
        continue
      if line == "[steps]":
        current_step = steps
      else if line == "[pass]":
        current_step = pass_steps
      else if line == "[fail]":
        current_step = fail_steps
      else if line.length > 0 && current_step:
        current_step.append(line)