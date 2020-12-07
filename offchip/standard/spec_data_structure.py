class OrgEntry(object):
    def __init__(self, size, dq, count: list):
        self.size = size
        self.dq = dq
        self.count = count


class SpeedEntry(object):
    def __init__(self, rate,
                 freq: float, tCK: float,
                 nBL, nCCDS, nCCDL,
                 nCL, nRCDR, nRCDW, nRP, nCWL,
                 nRAS, nRC,
                 nRTP, nWTRS, nWTRL, nWR,
                 nRRDS, nRRDL, nFAW,
                 nRFC, nREFI, nREFI1B,
                 nPD, nXP,
                 nCKESR, nXS,
                 ):
        self.rate = rate
        self.freq = freq
        self.tCK = tCK
        self.nBL = nBL
        self.nCCDS = nCCDS
        self.nCCDL = nCCDL
        self.nCL = nCL
        self.nRCDR = nRCDR
        self.nRCDW = nRCDW
        self.nRP = nRP
        self.nCWL = nCWL
        self.nRAS = nRAS
        self.nRC = nRC
        self.nRTP = nRTP
        self.nWTRS = nWTRS
        self.nWTRL = nWTRL
        self.nWR = nWR
        self.nRRDS = nRRDS
        self.nRRDL = nRRDL
        self.nFAW = nFAW
        self.nRFC = nRFC
        self.nREFI = nREFI
        self.nREFI1B = nREFI1B
        self.nPD = nPD
        self.nXP = nXP
        self.nCKESR = nCKESR
        self.nXS = nXS


class TimingEntry(object):
    def __init__(self, cmd, dist, val, sibling=None):
        self.cmd = cmd
        self.dist = dist
        self.val = val
        self.sibling = sibling
