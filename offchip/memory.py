import copy
from typing import List
from configs import strings, config
from offchip.standard import BaseSpec
from configs.stat_data_structure import ScalarStatistic
from offchip.data_structure import Request
from main import ArgumentParser


# MemoryAccessHandler
class Memory(object):
    from offchip.controller import Controller
    
    options = {}
    flag_stall = False
    flag_end = False
    translation = strings.translation_none
    type_ = strings.memory_type_RoBaRaCoCh
    tx_bits = None  # type: int
    
    _num_reads_device = {}
    _num_reads_channel = {}
    _num_writes_device = {}
    _num_cycles = ScalarStatistic(0)
    _num_cycles_active = ScalarStatistic(0)
    _max_bandwidth = ScalarStatistic(0)
    _max_address = 0
    _addr_bits = []
    
    __initialized = False
    __latency = {}
    __ctrls = []  # type: List[Controller]
    __spec = None  # type: BaseSpec
    
    @staticmethod
    def initialize(args_: ArgumentParser, ctrls: List[Controller]):
        assert Memory.__initialized == False
        Memory.__initialized = True
        
        Memory.__ctrls = ctrls
        Memory.__spec = ctrls[0].spec
        assert args_.name_spec == Memory.__spec.name_spec
        
        sz = Memory.__spec.org_entry.count
        assert (sz[0] & (sz[0] - 1)) == 0
        assert (sz[1] & (sz[1] - 1)) == 0
        
        tx = Memory.__spec.prefetch_size * Memory.__spec.channel_width / 8
        Memory.tx_bits = config.calc_log2(int(tx))
        assert (1 << Memory.tx_bits) == tx
        
        Memory._max_address = Memory.__spec.channel_width / 8
        for level_i in range(len(BaseSpec.level)):
            Memory._addr_bits.append(config.calc_log2(sz[level_i]))
            if sz[level_i] != 0:
                Memory._max_address *= sz[level_i]
        Memory._addr_bits[-1] -= config.calc_log2(Memory.__spec.prefetch_size)
        Memory._max_address = None
        
        if args_.translation != strings.translation_none:
            raise Exception('TODO: translation not none')
        
        Memory._initialize_statistics()
    
    @staticmethod
    def _initialize_statistics():
        Memory._num_cycles \
            .set_name('num_cycles') \
            .set_desc('The number of DRAM cycles simulated')
        Memory._num_cycles_active \
            .set_name('num_cycles_active') \
            .set_desc('The number of cycles that the DRAM is active (serving R/W)')
    
    @staticmethod
    def send(request: Request):
        type_ = request.type
        device = request.device
        addr_int = copy.deepcopy(request.addr_int)
        
        addr_int = config.clear_lower_bits(addr_int, Memory.tx_bits)
        
        # separate the address according to the level
        for i in range(len(Memory._addr_bits)):
            request.addr_list.append(None)
        if Memory.type_ == strings.memory_type_ChRaBaRoCo:
            for i in range(len(Memory._addr_bits) - 1, -1, -1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, Memory._addr_bits[i])
        elif Memory.type_ == strings.memory_type_RoBaRaCoCh:
            request.addr_list[0], addr_int = config.slice_lower_bits(
                addr_int, Memory._addr_bits[0])
            request.addr_list[-1], addr_int = config.slice_lower_bits(
                addr_int, Memory._addr_bits[-1])
            for i in range(1, len(Memory._addr_bits) - 1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, Memory._addr_bits[i])
        else:
            raise Exception(Memory.type_)
        
        # enqueue the request and update the statistic
        if Memory.__ctrls[request.addr_list[0]].enqueue(request) is True:
            # request enqueued successfully
            Memory.flag_stall = False
            if type_ == Request.Type.read:
                if device not in Memory._num_reads_device.keys():
                    Memory._num_reads_device[device] = 1
                else:
                    Memory._num_reads_device[device] += 1
                
                idx_channel = request.addr_list[BaseSpec.level.channel.value]
                if device not in Memory._num_reads_channel.keys():
                    Memory._num_reads_channel[idx_channel] = 1
                else:
                    Memory._num_reads_channel[idx_channel] += 1
            elif type_ == Request.Type.write:
                if device not in Memory._num_writes_device.keys():
                    Memory._num_writes_device[device] = 1
                else:
                    Memory._num_writes_device[device] += 1
            else:
                raise Exception(type_)
        else:
            # failed to enqueue the request
            Memory.flag_stall = True
    
    @staticmethod
    def cycle():
        Memory._num_cycles.scalar += 1
        is_active = False
        for ctrl in Memory.__ctrls:
            is_active = is_active or ctrl.is_active()
            ctrl.cycle()
        if is_active is True:
            Memory._num_cycles_active.scalar += 1
    
    @staticmethod
    def finish():
        spec = Memory.__spec
        sz = spec.org_entry.count
        idx_channel = BaseSpec.level.channel.value
        Memory._max_bandwidth = \
            spec.speed_entry.rate * 1e6 * spec.channel_width * sz[idx_channel] / 8
        for ctrl in Memory.__ctrls:
            num_reads = Memory._num_reads_channel[ctrl.channel.id_]
            ctrl.finish(num_reads)
    
    @staticmethod
    def set_high_writeq_watermark(mark):
        for ctrl in Memory.__ctrls:
            ctrl.set_high_writeq_watermark(mark)
    
    @staticmethod
    def set_low_writeq_watermark(mark):
        for ctrl in Memory.__ctrls:
            ctrl.set_low_writeq_watermark(mark)
    
    @staticmethod
    def get_num_cycle():
        return Memory._num_cycles.scalar
    
    @staticmethod
    def get_num_pending_requests():
        num_reqs = 0
        for ctrl in Memory.__ctrls:
            num_reqs += (ctrl.queue_read.size() +
                         ctrl.queue_write.size() +
                         ctrl.queue_other.size() +
                         ctrl.queue_activate.size() +
                         ctrl.pending_reads.size())
        return num_reqs
    
    @staticmethod
    def print_internal_state():
        print('--------------')
        for i in range(len(Memory.__ctrls)):
            print('  controller {}:'.format(i))
            Memory.__ctrls[i].print_state()
        print('--------------')
