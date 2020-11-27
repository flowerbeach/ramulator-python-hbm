class BaseStandard(object):
    def __init__(self, args):
        self._num_ranks = args.num_ranks
        self._num_channels = args.num_channels
        self._organization = args.organization
        self._speed = args.speed
