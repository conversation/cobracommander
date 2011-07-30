[steps]
django-admin.py test --noinput --failfast --settings="settings.test"
django-admin.py harvest --settings="settings.test"

[pass]
say "The build passed"

[fail]
say "The build failed"