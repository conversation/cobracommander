from django.conf import settings
from celery.decorators import task

import time
from .build_runner.builder import Builder

@task(name='app.apps.worker.tasks')
def exec_build(build):
    logger = exec_build.get_logger()
    logger.info("Running exec_build for %s:%s" % (build.project, build.ref))
    
    logger.info("Updating Build instance state")
    build.state = 'b'
    build.save()
    
    builder = Builder(build=build)
    builder.start()