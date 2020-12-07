from enum import Enum, unique


@unique
class standard(Enum):
    hbm = 'hbm'
    aldram = 'aldram'


org_1Gb = '1Gb'
org_2Gb = '2Gb'
org_4Gb = '4Gb'
list_org_hbm = [
    org_1Gb, org_2Gb, org_4Gb
]

speed_1Gbps = '1Gbps'

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
    standard.hbm: list_state_hbm,
}

translation_none = 'none'
translation_random = 'random'
list_translation = [translation_random, translation_none]

memory_type_ChRaBaRoCo = 'ChRaBaRoCo'
memory_type_RoBaRaCoCh = 'RoBaRaCoCh'
list_memory_type = [memory_type_ChRaBaRoCo, memory_type_RoBaRaCoCh]
