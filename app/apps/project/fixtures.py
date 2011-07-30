from .models import Project
from poseur.fixtures import FakeModel

class FakeProject(FakeModel):
  class Meta:
    model = Project
    count = 10