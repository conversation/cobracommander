from django.utils import simplejson
from django.utils import datetime_safe
from django.utils.functional import Promise
from django.utils.translation import force_unicode
from django.utils.encoding import smart_unicode
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from multiprocessing import Process
import os


class ModelJSONEncoder(DjangoJSONEncoder):
    """
    (simplejson) DjangoJSONEncoder subclass that knows how to encode fields.

    (adated from django.serializers, which, strangely, didn't
     factor out this part of the algorithm)
    """
    def handle_field(self, obj, field):
        return smart_unicode(getattr(obj, field.name), strings_only=True)

    def handle_fk_field(self, obj, field):
        related = getattr(obj, field.name)
        if related is not None:
            if field.rel.field_name == related._meta.pk.name:
                # Related to remote object via primary key
                related = related._get_pk_val()
            else:
                # Related to remote object via other field
                related = getattr(related, field.rel.field_name)
        return smart_unicode(related, strings_only=True)

    def handle_m2m_field(self, obj, field):
        if field.creates_table:
            return [
                smart_unicode(related._get_pk_val(), strings_only=True)
                for related
                in getattr(obj, field.name).iterator()
                ]

    def handle_model(self, obj):
        dic = {}
        for field in obj._meta.local_fields:
            if field.serialize:
                if field.rel is None:
                    dic[field.name] = self.handle_field(obj, field)
                else:
                    dic[field.name] = self.handle_fk_field(obj, field)
        for field in obj._meta.many_to_many:
            if field.serialize:
                dic[field.name] = self.handle_m2m_field(obj, field)
        return dic
    
    def handle_process(self, obj):
        return {'ppid':os.getppid(), 'pid':os.getpid()}

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(o)
        if isinstance(obj, Model):
            return self.handle_model(obj)
        if isinstance(obj, Process):
            return self.handle_process(obj)
        return super(ModelJSONEncoder, self).default(obj)