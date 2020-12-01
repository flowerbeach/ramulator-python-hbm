# coding=utf-8
import os
from tap import Tap
from configs import strings, sim_help


class ArgumentParser(Tap):
    name_spec: str = strings.str_spec_hbm
    org: str = ''
    speed: str = ''
    mapping: str = 'defaultmapping'
    display: str = 'more'  # more, less
    ideal: int = 0  # ideal experiment
    
    num_ranks = -1
    num_channels = -1
    num_subarrays = -1
    cpu_tick = -1
    mem_tick = -1
    warmup_insts = 0
    expected_limit_insts = 0


def parse_config(args_):
    filename = 'offchip/standard/{}-config.txt'.format(args_.name_spec.upper())
    if not os.path.exists(filename):
        raise Exception('Bad config file')
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for i in range(len(lines)):
        line = lines[i].strip()
        if line == '':
            continue
        if line.startswith('#'):
            continue
        assert '=' in line
        
        items = line.split('=')
        items[0] = items[0].strip()
        items[1] = items[1].strip()
        if items[0] == 'channels':
            args_.num_channels = int(items[1])
        elif items[0] == 'ranks':
            args_.num_ranks = int(items[1])
        elif items[0] == 'subarrays':
            args_.num_subarrays = int(items[1])
        elif items[0] == 'cpu_tick':
            args_.cpu_tick = int(items[1])
        elif items[0] == 'mem_tick':
            args_.mem_tick = int(items[1])
        elif items[0] == 'expected_limit_insts':
            args_.expected_limit_insts = int(items[1])
        elif items[0] == 'warmup_insts':
            args_.warmup_insts = int(items[1])
        elif items[0] == 'org':
            args_.org = items[1].split('_')[1]
        elif items[0] == 'speed':
            args_.speed = items[1].split('_')[1]

    return args_


class Argument(object):
    args = parse_config(
        ArgumentParser(description='simulation - dram_spec').parse_args())


from offchip.dram_spec.spec_base import BaseSpec
from offchip.memory_data_structure import Request, Trace


def main(args_, spec_: BaseSpec, trace_: Trace):
    from offchip.memory_access_handler import MemoryAccessHandler as MAH
    from offchip.memory_controller import Controller
    from offchip.memory_module import DRAM
    ctrls = []
    for i in range(args_.num_channels):
        channel = DRAM(spec_, strings.str_org_channel, 0, i)
        ctrl = Controller(args_, channel)
        ctrls.append(ctrl)
    MAH.initialize(args_, ctrls)
    
    flag_end, ptr_addr, type_request = False, 0, strings.str_req_type_read
    while flag_end is False or MAH.get_num_pending_requests() > 0:
        if flag_end is False and MAH.flag_stall is False:
            flag_end, ptr_addr, type_request = trace_.get_trace_request()
            request = Request(ptr_addr, type_request)
            MAH.send(request)
        
        if flag_end is True:
            # make sure that all write requests in the write queue are drained
            MAH.set_high_writeq_watermark(0.0)
        
        MAH.cycle()
    
    MAH.finish()
    sim_help.print_statistics(args_)


if __name__ == '__main__':
    print(Argument.args)
    print()
    
    # DRAM trace
    trace_file = 'dram.trace'
    
    name_spec = Argument.args.name_spec
    if name_spec == strings.str_spec_hbm:
        Standard = BaseSpec
    else:
        raise Exception(name_spec)
    
    standard = Standard(Argument.args)
    trace = Trace(trace_file)
    main(Argument.args, standard, trace)