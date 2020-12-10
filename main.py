# coding=utf-8
import os
from tap import Tap
from configs import strings, sim_help


class ArgumentParser(Tap):
    name_spec: str = strings.standard.hbm
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
    translation = strings.translation_none


def parse_config(args_):
    filename = 'offchip/configs/{}-config.txt'.format(args_.name_spec.value.upper())
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
        elif items[0] == 'translation':
            args_.translation = items[1].lower()
            assert args_.translation in strings.list_translation
    
    return args_


class Global(object):
    args = parse_config(
        ArgumentParser(description='simulation - DRAM').parse_args()
    )  # type: ArgumentParser


from offchip.data_structure import Request, Trace


def main(args_, spec_, trace_: Trace):
    from offchip.standard.spec_base import BaseSpec
    from offchip.controller import Controller
    from offchip.dram_module import DRAM
    spec_: BaseSpec
    ctrls = []
    for i in range(args_.num_channels):
        channel = DRAM(spec_, BaseSpec.level.channel, i)
        ctrl = Controller(spec_, channel)
        ctrls.append(ctrl)
    from offchip.memory import Memory
    memory = Memory(args_, ctrls)
    
    flag_end = False
    request = None  # type: Request
    while flag_end is False or memory.get_num_pending_requests() > 0:
        if flag_end is False and memory.flag_stall is False:
            flag_end, request = trace_.get_trace_request()
        
        if flag_end is False:
            memory.send(request)
        
        if flag_end is True:
            # make sure that all write requests in the write queue are drained
            memory.set_high_writeq_watermark(0.0)
        
        sim_help.print_state_periodically(memory, start=0, interval=1000, do_print_state=False)
        # sim_help.print_state_periodically(start=0, interval=100, do_print_state=True)
        sim_help.early_termination(memory, end=1000000, args=args_)
        
        memory.cycle()
    
    memory.finish()
    sim_help.print_statistics(memory, args_)


if __name__ == '__main__':
    print(Global.args)
    print()
    
    # DRAM trace
    trace_file = 'dram.trace'
    
    name_spec = Global.args.name_spec
    if name_spec == strings.standard.hbm:
        from offchip.standard.spec_base import BaseSpec
        Standard = BaseSpec
    else:
        raise Exception(name_spec)
    
    standard = Standard.initialize()
    trace = Trace(trace_file)
    main(Global.args, Standard, trace)
