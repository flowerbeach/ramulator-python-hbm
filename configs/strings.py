spec_hbm = 'hbm'
list_spec = [
    spec_hbm,
]

org_rank = 'rank'
org_channel = 'channel'
org_1Gb = '1Gb'
org_2Gb = '2Gb'
org_4Gb = '4Gb'
list_org_hbm = [
    org_1Gb, org_2Gb, org_4Gb
]

speed_1Gbps = '1Gbps'

req_type_read = 'read'
req_type_write = 'write'
req_type_refresh = 'refresh'
req_type_powerdown = 'powerdown'
req_type_selfrefresh = 'selfrefresh'
req_type_extension = 'extension'
list_req_type_all = [
    req_type_read,
    req_type_write,
    req_type_refresh,
    req_type_powerdown,
    req_type_selfrefresh,
    req_type_extension]

cmd_act = 'act'
cmd_pre = 'pre'
cmd_prea = 'prea'
cmd_rd = 'rd'
cmd_rda = 'rda'
cmd_wr = 'wr'
cmd_wra = 'wra'
cmd_ref = 'ref'
cmd_refsb = 'refsb'
cmd_pde = 'pde'
cmd_pdx = 'pdx'
cmd_sre = 'sre'
cmd_srx = 'srx'
list_cmd_hbm = [
    cmd_act,
    cmd_pre, cmd_prea,
    cmd_rd, cmd_rda,
    cmd_wr, cmd_wra,
    cmd_ref, cmd_refsb,
    cmd_pde, cmd_pdx,
    cmd_sre, cmd_srx]
dict_list_cmd_spec = {
    spec_hbm: list_cmd_hbm,
}

level_channel = 'channel'
level_rank = 'rank'
level_bankgroup = 'bankgroup'
level_bank = 'bank'
level_row = 'row'
level_column = 'column'
list_level_hbm = [
    level_channel,
    level_rank,
    level_bankgroup,
    level_bank,
    level_row,
    level_column]
dict_list_level_spec = {
    spec_hbm: list_level_hbm}
dict_idx_level_hbm = {
    level_channel: 0,
    level_rank: 1,
    level_bankgroup: 2,
    level_bank: 3,
    level_row: 4,
    level_column: 5}
dict_dict_idx_level_spec = {
    spec_hbm: dict_idx_level_hbm}

state_opened = 'opened'
state_closed = 'closed'
state_powerup = 'powerup'
state_actpowerdown = 'actpowerdown'
state_prepowerdown = 'prepowerdown'
state_selfrefresh = 'selfrefresh'
list_state_hbm = [
    state_opened,
    state_closed,
    state_powerup,
    state_actpowerdown,
    state_prepowerdown,
    state_selfrefresh]
dict_list_state_spec = {
    spec_hbm: list_state_hbm,
}

translation_none = 'none'
translation_random = 'random'
list_translation = [translation_random, translation_none]

memory_type_ChRaBaRoCo = 'ChRaBaRoCo'
memory_type_RoBaRaCoCh = 'RoBaRaCoCh'
list_memory_type = [memory_type_ChRaBaRoCo, memory_type_RoBaRaCoCh]
