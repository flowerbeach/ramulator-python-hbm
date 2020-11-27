from offchip.standard.standard_base import BaseStandard


class DRAM(object):
    def __init__(self, standard: BaseStandard, str_level, id):
        self._id = id
