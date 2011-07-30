import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../')))

name = 'gunicorn_ledgerapp_next'
bind = '127.0.0.1:29000'
logfile = '/home/ledgerapp/www/next.ledgerapp.cc/logs/gunicorn.log'
workers = 1
user = 'ledgerapp'