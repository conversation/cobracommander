from django import forms
from django.forms.util import ErrorList
from django.forms import ModelForm
from django.conf import settings
from django.template.defaultfilters import slugify

from .models import Project
from ..target.models import Target

class CreateProjectForm(ModelForm):
    """"""
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(CreateProjectForm, self).__init__(*args, **kwargs)

    # fields
    legend = u'Create a New Project'
    name_slug = forms.CharField(widget=forms.HiddenInput, required=False)
    targets = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        name = cleaned_data.get('name')
        url = cleaned_data.get('url')

        if name:
            slug = u'%s' % slugify(name)
            self.cleaned_data['name_slug'] = slug
            try:
                Project.objects.get(name_slug=slug, url=url) # raises error if record exists
                del cleaned_data["name_slug"]
                self._errors["name"] = self.error_class([
                    "A Project with that name and url already exists"
                ])
            except Exception, e:
                pass
        return cleaned_data

    def save(self, commit=True):
        project = super(CreateProjectForm, self).save(commit=False)

        if commit:
            project.save()
            master_target = Target(branch='master')
            master_target.save()
            project.targets.add(master_target)
            project.save()
        return project

    # meta shit
    class Media:
        css = {'all':()}
        js = ()

    class Meta:
        exclude = ('created_datetime',)
        model = Project
