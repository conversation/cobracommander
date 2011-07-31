import hashlib
import random
from poseur.fixtures import FakeField
from .models import Build
from poseur.fixtures import FakeModel

class FakeRefField(FakeField):
    def get_random_value(self, lower=None, upper=None):
        return hashlib.sha1(str(random.getrandbits(32))).hexdigest()


class FakeBuild(FakeModel):
    ref = FakeRefField.new.get_random_value
  
    class Meta:
        model = Build
        count = 5