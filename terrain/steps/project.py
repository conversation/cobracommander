# -*- coding: utf-8 -*-
import os, time
from django.conf import settings
from lettuce import step
from lettuce.django import django_url
from lettuce import world

@step(u'Given that I am on the build dashboard')
def given_that_i_am_on_the_build_dashboard(step):
    assert False, 'This step must be implemented'