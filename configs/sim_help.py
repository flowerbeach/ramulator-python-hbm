def print_state_periodically(dram, start, interval=1000, do_print_state=False):
    if dram.num_cycle > start:
        if dram.num_cycle % interval == 0:
            if do_print_state is True:
                dram.print_internal_state()
            else:
                print(dram.num_cycle, end='  ')
                if dram.num_cycle % (interval * 10) == 0:
                    print()


def print_state_every_cycle(dram, start, end=None):
    if start <= dram.num_cycle:
        if end is None or dram.num_cycle <= end:
            dram.print_internal_state()


def early_termination(dram, end, args):
    if dram.num_cycle > end:
        dram.print_internal_state()
        print_statistics(args)
        print('The number of cycle larger than', end)
        exit(886)


def print_statistics(args):
    from offchip.memory_access_handler import MemoryAccessHandler as MAH
