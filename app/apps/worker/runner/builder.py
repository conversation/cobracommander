

class Builder(object):
    """
    Builder runs tasks around starting, stopping and monitoring state of
    builds.
    """
    def __init__(self):
        self.status = defaultdict(None)
        