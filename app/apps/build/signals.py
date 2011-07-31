from ..worker.tasks import exec_build

def trigger_build(sender, instance, created, **kwargs):
    if created:
        async_build = exec_build.delay(build=instance)