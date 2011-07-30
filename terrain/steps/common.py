# -*- coding: utf-8 -*-
import os, time
from django.conf import settings
from lettuce import step
from lettuce.django import django_url
from lettuce import world
from nose.tools import assert_equals, assert_true

from ..decorators import *


@world.absorb
def request(request_path, status_code=200):
    @expect_status_code(200)
    def _visit():
        url = 'http:/%s' % os.path.join(("%s.%s" % ('test', settings.SERVER_NAME)),
            request_path.lstrip('/'))
        world.browser.visit(url)
    _visit()


# ----------------------------------------------------------------------------

@step(u'I should see text "(.*)"')
def i_should_see_text(step, text):
    assert_true(
        world.browser.is_text_present(text),
        u'Could not find text "%s".' % (text)
    )

@step(u'And I fill in "(.*)" field with "(.*)"')
def and_i_fill_in_group1_field_with_group2(step, field, value):
    world.browser.fill(field, value)

@step(u'And I choose option with text "(.*)" from selectbox with name "(.*)"')
def select_by_name(step, text, name):
    value = world.browser.find_option_by_text(text).first.value
    world.browser.select(name, value)

@step(u'And I choose option with value "(.*)" from selectbox with name "(.*)"')
def select_by_value(step, value, name):
    world.browser.select(name, value)

@step(u'And I click link with text "(.*)"')
def click_link_with_text(step, text):
    link = browser.find_link_by_text(text).first
    link.click()

@step(u'And I click element with selector "(.*)"')
def and_i_click_group1(step, css_selector):
    button = world.browser.find_by_css(css_selector).first
    button.click()

@step(u'And I click button called "(.*)"')
def click_button_called(step, text):
    world.browser.find_link_by_text(text).first.click()

@step(u'And I click button with name "(.*)"')
def click_button_with_name(step, name):
    world.browser.find_by_name(name).first.click()
    time.sleep(2)

@step(u'And I go to the "(.*)" url')
def and_i_go_to_the_url(step, url):
    world.request(url)