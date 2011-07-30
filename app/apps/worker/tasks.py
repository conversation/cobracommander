from celery.decorators import task

@task()
def exec_build(project, ref):
    pass