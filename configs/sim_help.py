def print_state_periodically(memory, start, interval=1000, do_print_state=False):
    num_cycle = memory.get_num_cycle()
    if num_cycle > start:
        if num_cycle % interval == 0:
            if do_print_state is True:
                memory.print_internal_state()
            else:
                print(num_cycle, end='  ')
                if num_cycle % (interval * 10) == 0:
                    print()


def early_termination(memory, end, args):
    if memory.get_num_cycle() > end:
        print_statistics(memory, args)
        print('The number of cycle larger than', end)
        exit(886)


def print_statistics(memory, args):
    # MAH.print_internal_state()
    print('#cycle: {}'.format(memory.get_num_cycle()))
