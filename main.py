# coding=utf-8

from tap import Tap
from configs import strings, sim_help


class ArgumentParser(Tap):
    name_standard: str = strings.str_standard_HBM
    organization: str = ''
    mapping: str = 'defaultmapping'
    speed: int = 1
    display: str = 'more'  # more, less
    ideal: int = 0  # ideal experiment
    
    num_ranks = -1
    num_channels = -1


def parse_config(args_):
    pass


args = ArgumentParser(description='simulation - dram').parse_args()
parse_config(args)

from offchip.memory_access_handler import MemoryAccessHandler as MAH
from offchip.standard.standard_base import BaseStandard
from offchip.memory_data_structure import Request, Trace


def main(args_, standard_: BaseStandard, trace_: Trace):
    from offchip.memory_controller import Controller
    from offchip.memory_dram import DRAM
    ctrls = []
    for i in range(args_.num_channels):
        channel = DRAM(standard_, strings.str_org_channel, i)
        ctrl = Controller(args_, channel)
        ctrls.append(ctrl)
    MAH.initialize(args_, ctrls)
    
    ptr_addr = 0
    type_request = strings.str_req_type_read
    while (MAH.flag_end is False) or (MAH.have_pending_requests()):
        if MAH.flag_end is False and MAH.flag_stall is False:
            MAH.flag_end, ptr_addr, type_request = trace_.get_trace_request()
        
        if MAH.flag_end is False:
            request = Request(ptr_addr, type_request, MAH.read_complele)
            request.ptr_addr = ptr_addr
            request.type_request = type_request
            MAH.flag_stall = MAH.send(request)
            if MAH.flag_stall is False:
                if type_request == strings.str_req_type_read:
                    MAH.num_reads += 1
                elif type_request == strings.str_req_type_write:
                    MAH.num_writes += 1
                else:
                    raise Exception(type_request)
        else:
            # make sure that all write requests in the write queue are drained
            MAH.set_high_writeq_watermark(0)
        
        MAH.cycle()
        MAH.num_cycles += 1
    
    MAH.finish()
    sim_help.print_statistics(args_)


if __name__ == '__main__':
    # DRAM trace
    trace_file = 'dram.trace'
    
    name_standard = args.name_standard
    if name_standard == strings.str_standard_HBM:
        Standard = BaseStandard
    else:
        raise Exception(name_standard)
    
    standard = Standard(args)
    trace = Trace(trace_file)
    main(args, standard, trace)
