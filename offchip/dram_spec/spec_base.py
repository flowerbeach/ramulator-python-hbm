from configs import strings


class OrgEntry():
    def __init__(self):
        self.size = -1
        self.dq = -1
        self.count = []


class BaseSpec(object):
    def __init__(self, args):
        self.name_spec = args.name_spec
        
        self._num_ranks = args.num_ranks
        self._num_channels = args.num_channels
        self._organization = args.organization
        self._speed = args.speed
        
        self.start = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        self.prereq = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        self.rowhit = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        self.rowopen = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        self.lambda_ = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        self.timing = [None for _ in strings.dict_list_level_spec[self.name_spec]]
        
        self.org_entry = OrgEntry()
