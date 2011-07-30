from django.conf import settings
from lettuce import before, after, world
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command
from django.db import connection

old_names = []

@before.harvest
def initial_setup(server):
    from splinter.browser import Browser
    setup_test_environment()
    old_names = setup_databases()
    call_command('flush', interactive=False, verbosity=0)
    call_command('loaddata', 'all', verbosity=0)
    world.browser = Browser('webdriver.firefox')

@after.harvest
def cleanup(server):
    teardown_databases(old_names)
    teardown_test_environment()
    world.browser.quit()

@before.each_scenario
def reset_data(scenario):
    call_command('flush', interactive=False, verbosity=0)
    call_command('loaddata', 'all', verbosity=0)

def setup_databases():
    from django.db import connections
    for alias in connections:
        connection = connections[alias]
        old_names.append((connection, connection.settings_dict['NAME']))
        connection.creation.create_test_db(True, autoclobber=True)
    return old_names

def teardown_databases(old_names):
    from django.db import connections
    for connection, old_name in old_names:
        connection.creation.destroy_test_db(old_name, True)