from .models import Project
from poseur.fixtures import FakeModel
from ..build.fixtures import FakeBuild

class FakeProject(FakeModel):
  # for x in range(0, 3):
  #   
  # builds = 
  
  class Meta:
    model = Project
    count = 10