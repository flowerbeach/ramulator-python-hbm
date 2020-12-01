str_spec_hbm = 'hbm'
str_spec_ddr4 = 'ddr4'
list_str_spec = [
    str_spec_hbm,
    str_spec_ddr4,
]

str_org_rank = 'rank'
str_org_channel = 'channel'
str_org_1Gb = '1Gb'
str_org_2Gb = '2Gb'
str_org_4Gb = '4Gb'
list_str_org_hbm = [
    str_org_1Gb, str_org_2Gb, str_org_4Gb
]

str_speed_1Gbps = '1Gbps'

str_req_type_read = 'read'
str_req_type_write = 'write'
str_req_type_refresh = 'refresh'
str_req_type_powerdown = 'powerdown'
str_req_type_selfrefresh = 'selfrefresh'
str_req_type_extension = 'extension'
list_str_type_all = [
    str_req_type_read,
    str_req_type_write,
    str_req_type_refresh,
    str_req_type_powerdown,
    str_req_type_selfrefresh,
    str_req_type_extension]

str_cmd_act = 'act'
str_cmd_pre = 'pre'
str_cmd_prea = 'prea'
str_cmd_rd = 'rd'
str_cmd_rda = 'rda'
str_cmd_wr = 'wr'
str_cmd_wra = 'wra'
str_cmd_ref = 'ref'
str_cmd_refsb = 'refsb'
str_cmd_pde = 'pde'
str_cmd_pdx = 'pdx'
str_cmd_sre = 'sre'
str_cmd_srx = 'srx'
list_str_cmd_hbm = [
    str_cmd_act,
    str_cmd_pre, str_cmd_prea,
    str_cmd_rd, str_cmd_rda,
    str_cmd_wr, str_cmd_wra,
    str_cmd_ref, str_cmd_refsb,
    str_cmd_pde, str_cmd_pdx,
    str_cmd_sre, str_cmd_srx]
dict_list_cmd_spec = {
    str_spec_hbm: list_str_cmd_hbm,
}

str_level_channel = 'channel'
str_level_rank = 'rank'
str_level_bankgroup = 'bankgroup'
str_level_bank = 'bank'
str_level_row = 'row'
str_level_column = 'column'
list_str_level_hbm = [
    str_level_channel,
    str_level_rank,
    str_level_bankgroup,
    str_level_bank,
    str_level_row,
    str_level_column]
dict_list_level_spec = {
    str_spec_hbm: list_str_level_hbm,
}

str_state_opened = 'opened'
str_state_closed = 'closed'
str_state_powerup = 'powerup'
str_state_actpowerdown = 'actpowerdown'
str_state_prepowerdown = 'prepowerdown'
str_state_selfrefresh = 'selfrefresh'
list_str_state_hbm = [
    str_state_opened,
    str_state_closed,
    str_state_powerup,
    str_state_actpowerdown,
    str_state_prepowerdown,
    str_state_selfrefresh]
dict_list_state_spec = {
    str_spec_hbm: list_str_state_hbm,
}
