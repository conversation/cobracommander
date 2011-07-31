# Cobra Commander

In your codebase building your builds.

## Development environment

- python ~2.7
- django 1.3
- postgres
- coffee & scss
- python requirements; see REQUIREMENTS.


## Getting up and running

Install stuff:

    brew install python rabbitmq postgres ... etc


Set up the virtual environment for development:

    mkvirtualenv --no-site-packages --distribute cobracommander
    cdvirtualenv
    echo "export DJANGO_SETTINGS_MODULE='settings.development'" >> bin/postactivate
    echo "export PYTHONPATH='`pwd`/project/cobracommander'" >> bin/postactivate
    echo "unset DJANGO_SETTINGS_MODULE" >> bin/depostactivate


Get the code, install requirements, set up DB, etc...

    git clone git@github.com:tc/cobracommander project/cobracommander
    pip install -r REQUIREMENTS
    createdb cobracommander_development
    django-admin.py syncdb
    django-admin.py migrate


From here you should be able to run the app:

    django-admin.py runserver_plus              # run the dev server
    django-admin.py celeryd --loglevel=INFO     # run the async worker

...and run the test suite:

    django-admin.py harvest --settings="settings.test"
    django-admin.py test --settings="settings.test"


## Generating fake data

    manage.py shell
    from poseur.fixtures import load_fixtures
    load_fixtures('app.apps.project.fixtures')

__Boom.__