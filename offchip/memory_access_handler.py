import copy
from typing import List
from configs import strings, config
from offchip.dram_spec import BaseSpec
from configs.stat_data_structure import ScalarStatistic
from offchip.memory_data_structure import Request
from offchip.memory_controller import Controller
from main import ArgumentParser


# MemoryAccessHandler
class MemAccHan(object):
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
    
    list_level_spec = []
    dict_idx_level_spec = []
    
    @staticmethod
    def initialize(args_: ArgumentParser, ctrls: List[Controller]):
        assert MemAccHan.__initialized == False
        MemAccHan.__initialized = True
        
        MemAccHan.__ctrls = ctrls
        MemAccHan.__spec = ctrls[0].spec
        assert args_.name_spec == MemAccHan.__spec.name_spec
        MemAccHan.list_level_spec = strings.dict_list_level_spec[MemAccHan.__spec.name_spec]
        MemAccHan.dict_idx_level_spec = strings.dict_dict_idx_level_spec[MemAccHan.__spec.name_spec]
        
        sz = MemAccHan.__spec.org_entry.count
        assert (sz[0] & (sz[0] - 1)) == 0
        assert (sz[1] & (sz[1] - 1)) == 0
        
        tx = MemAccHan.__spec.prefetch_size * MemAccHan.__spec.channel_width / 8
        MemAccHan.tx_bits = config.calc_log2(int(tx))
        assert (1 << MemAccHan.tx_bits) == tx
        
        MemAccHan._max_address = MemAccHan.__spec.channel_width / 8
        len_level = len(MemAccHan.list_level_spec)
        for level_i in range(len_level):
            MemAccHan._addr_bits.append(config.calc_log2(sz[level_i]))
            if sz[level_i] != 0:
                MemAccHan._max_address *= sz[level_i]
        MemAccHan._addr_bits[-1] -= config.calc_log2(MemAccHan.__spec.prefetch_size)
        MemAccHan._max_address = None
        
        if args_.translation != strings.translation_none:
            raise Exception('TODO: translation not none')
        
        MemAccHan._initialize_statistics()
    
    @staticmethod
    def _initialize_statistics():
        MemAccHan._num_cycles \
            .set_name('num_cycles') \
            .set_desc('The number of DRAM cycles simulated')
        MemAccHan._num_cycles_active \
            .set_name('num_cycles_active') \
            .set_desc('The number of cycles that the DRAM is active (serving R/W)')
    
    @staticmethod
    def send(request: Request):
        type_ = request.type
        device = request.device
        addr_int = copy.deepcopy(request.addr_int)
        
        addr_int = config.clear_lower_bits(addr_int, MemAccHan.tx_bits)
        
        # separate the address according to the level
        for i in range(len(MemAccHan._addr_bits)):
            request.addr_list.append(None)
        if MemAccHan.type_ == strings.memory_type_ChRaBaRoCo:
            for i in range(len(MemAccHan._addr_bits) - 1, -1, -1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, MemAccHan._addr_bits[i])
        elif MemAccHan.type_ == strings.memory_type_RoBaRaCoCh:
            request.addr_list[0], addr_int = config.slice_lower_bits(
                addr_int, MemAccHan._addr_bits[0])
            request.addr_list[-1], addr_int = config.slice_lower_bits(
                addr_int, MemAccHan._addr_bits[-1])
            for i in range(1, len(MemAccHan._addr_bits) - 1):
                request.addr_list[i], addr_int = config.slice_lower_bits(
                    addr_int, MemAccHan._addr_bits[i])
        else:
            raise Exception(MemAccHan.type_)
        
        # enqueue the request and update the statistic
        if MemAccHan.__ctrls[request.addr_list[0]].enqueue(request) is True:
            # request enqueued successfully
            MemAccHan.flag_stall = False
            if type_ == strings.req_type_read:
                if device not in MemAccHan._num_reads_device.keys():
                    MemAccHan._num_reads_device[device] = 1
                else:
                    MemAccHan._num_reads_device[device] += 1
                
                idx_channel = request.addr_list[
                    MemAccHan.list_level_spec.index(strings.level_channel)]
                if device not in MemAccHan._num_reads_channel.keys():
                    MemAccHan._num_reads_channel[idx_channel] = 1
                else:
                    MemAccHan._num_reads_channel[idx_channel] += 1
            elif type_ == strings.req_type_write:
                if device not in MemAccHan._num_writes_device.keys():
                    MemAccHan._num_writes_device[device] = 1
                else:
                    MemAccHan._num_writes_device[device] += 1
            
            else:
                raise Exception(type_)
        else:
            # failed to enqueue the request
            MemAccHan.flag_stall = True
    
    @staticmethod
    def cycle():
        MemAccHan._num_cycles.scalar += 1
        is_active = False
        for ctrl in MemAccHan.__ctrls:
            is_active = is_active or ctrl.is_active()
            ctrl.cycle()
        if is_active is True:
            MemAccHan._num_cycles_active.scalar += 1
    
    @staticmethod
    def finish():
        spec = MemAccHan.__spec
        sz = spec.org_entry.count
        idx_channel = MemAccHan.list_level_spec.index(strings.level_channel)
        MemAccHan._max_bandwidth = \
            spec.speed_entry.rate * 1e6 * spec.channel_width * sz[idx_channel] / 8
        for ctrl in MemAccHan.__ctrls:
            num_reads = MemAccHan._num_reads_channel[ctrl.channel.id_]
            ctrl.finish(num_reads)
    
    @staticmethod
    def set_high_writeq_watermark(mark):
        for ctrl in MemAccHan.__ctrls:
            ctrl.set_high_writeq_watermark(mark)
    
    @staticmethod
    def set_low_writeq_watermark(mark):
        for ctrl in MemAccHan.__ctrls:
            ctrl.set_low_writeq_watermark(mark)
    
    @staticmethod
    def get_num_cycle():
        return MemAccHan._num_cycles.scalar
    
    @staticmethod
    def get_num_pending_requests():
        num_reqs = 0
        for ctrl in MemAccHan.__ctrls:
            num_reqs += (ctrl.queue_read.size() +
                         ctrl.queue_write.size() +
                         ctrl.queue_other.size() +
                         ctrl.queue_activate.size() +
                         ctrl.pending_reads.size())
        return num_reqs
    
    @staticmethod
    def print_internal_state():
        print('--------------')
        for i in range(len(MemAccHan.__ctrls)):
            print('  controller {}:'.format(i))
            MemAccHan.__ctrls[i].print_state()
        print('--------------')
