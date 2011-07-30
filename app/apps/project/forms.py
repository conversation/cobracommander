from django import forms
from django.forms.util import ErrorList
from django.forms import ModelForm
from django.conf import settings
from django.template.defaultfilters import slugify

from .models import Project

class ProjectForm(ModelForm):
    """"""
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(ProjectForm, self).__init__(*args, **kwargs)
    
    # fields
    legend = u'Create a New Project'
    name_slug = forms.CharField(widget=forms.HiddenInput, required=False)
    builds = forms.CharField(widget=forms.HiddenInput, required=False)
    
    def clean(self):
        cleaned_data = self.cleaned_data
        name = cleaned_data.get('name')
        
        if name:
            slug = u'%s' % slugify(name)
            self.cleaned_data['name_slug'] = slug
            try:
                Project.objects.get(name_slug=slug) # raises error if record exists
                del cleaned_data["name_slug"]
                self._errors["name"] = self.error_class([
                    "A Project with that name already exists"
                ])
            except Exception, e:
                pass
        return cleaned_data
    
    # meta shit
    class Media:
        css = {'all':()}
        js = ()
    
    class Meta:
        model = Project