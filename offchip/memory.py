import copy
from typing import List
from configs import strings, config
from configs.stat_data_structure import ScalarStatistic
from offchip.data_structure import Request


# MemoryAccessHandler
class Memory(object):
    from offchip.controller import Controller
    initialized = False
    
    def __init__(self, args_, ctrls: List[Controller]):
        from offchip.standard import BaseSpec
        self.flag_stall = False
        self.translation = strings.translation_none
        self.type_ = strings.memory_type_RoBaRaCoCh
        self.tx_bits = None  # type: int
        
        self._num_reads_device = {}
        self._num_reads_channel = {}
        self._num_writes_device = {}
        self._num_cycles = ScalarStatistic(0)
        self._num_cycles_active = ScalarStatistic(0)
        self._max_bandwidth = ScalarStatistic(0)
        self._max_address = 0
        self._addr_bits = []
        
        self.latency = {}
        self.ctrls = []  # type: List[Memory.Controller]
        self.spec = None  # type: BaseSpec
        
        assert Memory.initialized == False
        Memory.initialized = True
        
        self.ctrls = ctrls
        self.spec = ctrls[0].spec
        assert args_.name_spec == self.spec.name_spec
        
        sz = self.spec.org_entry.count
        assert (sz[0] & (sz[0] - 1)) == 0
        assert (sz[1] & (sz[1] - 1)) == 0
        
        tx = self.spec.prefetch_size * self.spec.channel_width / 8
        self.tx_bits = config.calc_log2(int(tx))
        assert (1 << self.tx_bits) == tx
        
        self._max_address = self.spec.channel_width / 8
        for level_i in range(len(BaseSpec.level)):
            self._addr_bits.append(config.calc_log2(sz[level_i]))
            if sz[level_i] != 0:
                self._max_address *= sz[level_i]
        self._addr_bits[-1] -= config.calc_log2(self.spec.prefetch_size)
        self._max_address = None
        
        if args_.translation != strings.translation_none:
            raise Exception('TODO: translation not none')
        
        self._initialize_statistics()
    
    def _initialize_statistics(self):
        self._num_cycles \
            .set_name('num_cycles') \
            .set_desc('The number of DRAM cycles simulated')
        self._num_cycles_active \
            .set_name('num_cycles_active') \
            .set_desc('The number of cycles that the DRAM is active (serving R/W)')
    
    def send(self, request: Request):
        from offchip.standard import BaseSpec
        type_ = request.type
        device = request.device
        addr_int = copy.deepcopy(request.addr_int)
        
        addr_int = config.clear_lower_bits(addr_int, self.tx_bits)
        
        # separate the address according to the level
        for i in range(len(self._addr_bits)):
            request.addr_list.append(None)
        if self.type_ == strings.memory_type_ChRaBaRoCo:
            for i in range(len(self._addr_bits) - 1, -1, -1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, self._addr_bits[i])
        elif self.type_ == strings.memory_type_RoBaRaCoCh:
            request.addr_list[0], addr_int = config.slice_lower_bits(
                addr_int, self._addr_bits[0])
            request.addr_list[-1], addr_int = config.slice_lower_bits(
                addr_int, self._addr_bits[-1])
            for i in range(1, len(self._addr_bits) - 1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, self._addr_bits[i])
        else:
            raise Exception(self.type_)
        
        # enqueue the request and update the statistic
        if self.ctrls[request.addr_list[0]].enqueue(request) is True:
            # request enqueued successfully
            self.flag_stall = False
            if type_ == Request.Type.read:
                if device not in self._num_reads_device.keys():
                    self._num_reads_device[device] = 1
                else:
                    self._num_reads_device[device] += 1
                
                idx_channel = request.addr_list[BaseSpec.level.channel.value]
                if device not in self._num_reads_channel.keys():
                    self._num_reads_channel[idx_channel] = 1
                else:
                    self._num_reads_channel[idx_channel] += 1
            elif type_ == Request.Type.write:
                if device not in self._num_writes_device.keys():
                    self._num_writes_device[device] = 1
                else:
                    self._num_writes_device[device] += 1
            else:
                raise Exception(type_)
        else:
            # failed to enqueue the request
            self.flag_stall = True
    
    def cycle(self):
        print('--- {}'.format(self.get_num_cycle()))
        self._num_cycles.scalar += 1
        is_active = False
        for i in range(len(self.ctrls)):
            ctrl = self.ctrls[i]  # type: Memory.Controller
            print('    ctrl {}: '.format(i), end='')
            is_active = is_active or ctrl.is_active()
            ctrl.cycle()
            print()
        if is_active is True:
            self._num_cycles_active.scalar += 1
    
    def finish(self):
        from offchip.standard import BaseSpec
        spec = self.spec
        sz = spec.org_entry.count
        idx_channel = BaseSpec.level.channel.value
        self._max_bandwidth = \
            spec.speed_entry.rate * 1e6 * spec.channel_width * sz[idx_channel] / 8
        for ctrl in self.ctrls:
            if ctrl.channel.id_ not in self._num_reads_channel.keys():
                num_reads = 0
            else:
                num_reads = self._num_reads_channel[ctrl.channel.id_]
            ctrl.finish(num_reads)
    
    def set_high_writeq_watermark(self, mark):
        for ctrl in self.ctrls:
            ctrl.set_high_writeq_watermark(mark)
    
    def set_low_writeq_watermark(self, mark):
        for ctrl in self.ctrls:
            ctrl.set_low_writeq_watermark(mark)
    
    def get_num_cycle(self):
        return self._num_cycles.scalar
    
    def get_num_pending_requests(self):
        num_reqs = 0
        for ctrl in self.ctrls:
            num_reqs += (ctrl.queue_read.size() +
                         ctrl.queue_write.size() +
                         ctrl.queue_other.size() +
                         ctrl.queue_activate.size() +
                         ctrl.pending_reads.size())
        return num_reqs
    
    def print_internal_state(self):
        print('--------------')
        for i in range(len(self.ctrls)):
            print('  controller {}:'.format(i))
            self.ctrls[i].print_state()
        print('--------------')
