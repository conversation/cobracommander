from lettuce import world
from nose.tools import assert_equals, assert_true


def expect_status_code(status_code):
    def inner_wrap(func):
        def expect_status_code_closure(*args, **kwargs):
            func(*args, **kwargs)
            assert_equals(status_code, world.browser.status_code.code)
        return expect_status_code_closure
    return inner_wrap