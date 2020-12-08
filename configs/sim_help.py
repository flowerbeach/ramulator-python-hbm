from offchip.memory import Memory as MAH


def print_state_periodically(start, interval=1000, do_print_state=False):
    num_cycle = MAH.get_num_cycle()
    if num_cycle > start:
        if num_cycle % interval == 0:
            if do_print_state is True:
                MAH.print_internal_state()
            else:
                print(num_cycle, end='  ')
                if num_cycle % (interval * 10) == 0:
                    print()


def early_termination(end, args):
    if MAH.get_num_cycle() > end:
        MAH.print_internal_state()
        print_statistics(args)
        print('The number of cycle larger than', end)
        exit(886)


def print_statistics(args):
    print('TODO: print_statistics')
