from collections import defaultdict
from django.utils import simplejson
from ..utils import get_logger
from ..utils.json_encoder import ModelJSONEncoder


class StatusAccessor(object):
    def __init__(self, builder):
        self.logger = get_logger(__name__)
        self.has_changed = False
        self.builder = builder
        self.status = defaultdict(dict)
        self.status_keys = ('building', 'queue',)
        
    def _update_value_for_key(self, key, new_value):
        old_val = self.status.get(key)
        if old_val != new_value:
            self.status[key] = new_value
            self.has_changed = True
            self.logger.info("Status change for '%s': '%s' -> '%s'", key, old_val, new_value)
    
    def _serialize(self, data):
        return simplejson.dumps(data, cls=ModelJSONEncoder)

    def update(self):
        self.has_changed = False
        for key in self.status_keys:
            self._update_value_for_key(key, getattr(self, 'get_' + key)())
        return (self.has_changed, self._serialize(self.status))
    
    def get_building(self):
        return self.builder.status['building']
    
    def get_queue(self):
        return self.builder.queue