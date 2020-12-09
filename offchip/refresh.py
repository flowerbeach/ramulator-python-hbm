from offchip.data_structure import Request


class Refresh(object):
    from offchip.controller import Controller
    from offchip.standard import BaseSpec as t_spec
    
    def __init__(self, ctrl, ):
        self.ctrl = ctrl  # type: Refresh.Controller
        
        self.cycle_last_refreshed = 0
        self.cycle_current = 0
        self.cnt_max_rank = len(self.ctrl.channel.children)
        self.cnt_max_bank = self.ctrl.channel.t_spec.org_entry.count[Refresh.t_spec.level.bank.value]
        
        self.bank_ref_counters = []
        self.__bank_refresh_backlog = []
        for i in range(self.cnt_max_rank):
            self.bank_ref_counters.append(0)
            self.__bank_refresh_backlog.append([0 for _ in range(self.cnt_max_bank)])
        
        self.__backlog_max = 8
        self.__backlog_min = -8
        self.__backlog_early_pull_threshold = -6
        self.__ctrl_write_mode = False
        
        self.level_channel = Refresh.t_spec.level.channel.value
        self.level_rank = Refresh.t_spec.level.rank.value
        self.level_bank = Refresh.t_spec.level.bank.value
        self.level_sa = -1
    
    def cycle(self):
        self.cycle_current += 1
        
        refresh_interval = self.ctrl.channel.t_spec.speed_entry.nREFI
        
        if self.cycle_current - self.cycle_last_refreshed >= refresh_interval:
            self._inject_refresh(True)
    
    def _inject_refresh(self, b_ref_rank: bool):
        if b_ref_rank is True:  # Rank-level refresh
            for rank in self.ctrl.channel.children:
                self._refresh_target(self.ctrl, rank.id_, -1, -1)
        else:  # Bank-level refresh
            # Simultaneously issue to all ranks
            for rank in self.ctrl.channel.children:
                self._refresh_target(self.ctrl, rank.id_, self.bank_ref_counters[rank.id_], -1)
        self.cycle_last_refreshed = self.cycle_current
    
    @staticmethod
    def _refresh_target(ctrl: Controller, rank: int, bank: int, sa: int):
        addr_list = [-1 for _ in range(len(Refresh.t_spec.level))]
        addr_list[0] = ctrl.channel.id_
        addr_list[1] = rank
        addr_list[2] = bank
        addr_list[3] = sa
        
        req = Request(addr_list, Request.Type.refresh, None)
        res = ctrl.enqueue(req)
        assert res is True
