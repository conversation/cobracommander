from collections import defaultdict
from django.utils import simplejson
from ..utils import get_logger
from ..utils.json_encoder import ModelJSONEncoder


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect
    def removed(self):
        return self.set_past - self.intersect
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


class StatusAccessor(object):
    def __init__(self, builder):
        self.logger = get_logger(__name__)
        self.has_changed = False
        self.builder = builder
        self.status = defaultdict(dict)
        self.status_keys = (
            'building',
            'queue',
        )

    def _serialize(self, data):
        return simplejson.dumps(data, cls=ModelJSONEncoder)

    def get_status(self):
        return self._serialize(self.status)

    def update(self):
        print "update()"
        self.has_changed = False
        for key in self.status_keys:
            print " - checking key: '%s'" % key
            changed, value = getattr(self, 'check_' + key)()
            if changed:
                print "  - has changed (%s -> %s)" % (self.status[key], value)
                self.has_changed = True
            self.status[key] = value
        print "\n"
        return (self.has_changed, self._serialize(self.status))

    def check_building(self):
        changed = False
        if self.status['building'] != self.builder.status['building']:
            changed = True
        return (changed, self.builder.status['building'])

    def check_queue(self):

        def _check_queues(old, new):
            print old, new
            print len(old['pending']), ' - ', len(new['pending'])
            if len(old['pending']) != len(new['pending']):
                print 'lengths are different'
                return True
            return False

        changed = False
        queue = self.builder.get_queue()
        diff = DictDiffer(current_dict=queue, past_dict=self.status['queue'])
        if diff.added() or diff.removed() or diff.changed() or _check_queues(self.status['queue'], queue):
            changed = True
        return (changed, queue)
