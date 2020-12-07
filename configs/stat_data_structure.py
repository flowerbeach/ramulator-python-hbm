class BaseStatistic(object):
    def __init__(self):
        self.__name = ''
        self.__desc = ''
    
    def set_name(self, name):
        self.__name = name
        return self
    
    def set_desc(self, desc):
        self.__desc = desc
        return self
    
    def get_name(self):
        return self.__name
    
    def get_desc(self):
        return self.__desc


class ScalarStatistic(BaseStatistic):
    def __init__(self, init_scalar):
        super(ScalarStatistic, self).__init__()
        assert type(init_scalar) in [int, float]
        self.scalar = init_scalar


class VectorStatistic(BaseStatistic):
    def __init__(self):
        super(VectorStatistic, self).__init__()
        self.vector = []
