
'''
This module enumerates the SysEx-controllable parameters on the TX81Z.
(See "SYSTEM EXCLUSIVE DATA FORMAT" in the TX81Z manual)

Usage is, e.g.:
  PARAM.ALG
  PARAM.OP[2].OSW

Enumerated names are based on the "LCD" text (what it's called on-screen),
with some self-explanatory exceptions.

Each parameter is defined with its group/parameter values for SysEx access,
its minimum/maximum values (and a center value if applicable),
and a name for convenience.
'''

class GROUP(object):
    VCED   = 0b0010010  # Voice parameters compatible with DX21/27/100
    ACED   = 0b0010011  # Additional voice parameters for TX81Z
    PCED   = 0b0010011  # Performance parameters
    REMOTE = 0b0010011  # For effectively pushing front panel buttons

class TX81Z_Param(object):
    def __init__(self, group, parameter, min, max, name, center=None):
        self.group = group
        self.parameter = parameter
        self.min = min
        self.max = max
        self.center = center
        self.name = name

    def __repr__(self):
        params = (self.group, self.parameter, self.min, self.max,
                  self.name, self.center)
        return 'TX81Z_Param({:x}, {:x}, {}, {}, {!r}, {})'.format(*params)

class VCED_Param(TX81Z_Param):
    def __init__(self, parameter, min, max, name, center=None):
        super().__init__(GROUP.VCED, parameter, min, max, name, center=None)

class ACED_Param(TX81Z_Param):
    def __init__(self, parameter, min, max, name, center=None):
        super().__init__(GROUP.ACED, parameter, min, max, name, center=None)

class PCED_Param(TX81Z_Param):
    def __init__(self, parameter, min, max, name, center=None):
        super().__init__(GROUP.PCED, parameter, min, max, name, center=None)

class REMOTE_Param(TX81Z_Param):
    def __init__(self, parameter, name):
        super().__init__(GROUP.REMOTE, parameter, 0, 0x7f, name)

class OperatorParams(object):
    def __init__(self, operator):
        self.operator = operator
        self.name = 'OP{}'.format(operator)
        n = self.name + ' '
        # Normal voice parameters group
        p = (4 - operator) * 13
        self.AR  = VCED_Param(p + 0, 0, 31, n + 'Attack Rate')
        self.D1R = VCED_Param(p + 1, 0, 31, n + 'Decay 1 Rate')
        self.D2R = VCED_Param(p + 2, 0, 31, n + 'Decay 2 Rate')
        self.RR  = VCED_Param(p + 3, 1, 15, n + 'Release Rate')
        self.D1L = VCED_Param(p + 4, 0, 15, n + 'Decay 1 Level')
        self.LS  = VCED_Param(p + 5, 0, 99, n + 'Level Scaling')
        self.RS  = VCED_Param(p + 6, 0,  3, n + 'Rate Scaling')
        self.EBS = VCED_Param(p + 7, 0,  7, n + 'EG Bias Sens')
        self.AME = VCED_Param(p + 8, 0,  1, n + 'Amp Mod Enable')
        self.KVS = VCED_Param(p + 9, 0,  7, n + 'Key Vel Sens')
        self.OUT = VCED_Param(p +10, 0, 99, n + 'Output Level')
        self.CRS = VCED_Param(p +11, 0, 63, n + 'Coarse Freq')
        self.DET = VCED_Param(p +12, 0,  6, n + 'Detune', 3)
        # Additional voice parameters
        p = (4 - operator) * 5
        self.FIX       = ACED_Param(p + 0, 0, 1, n + 'Ratio/Fixed')
        self.FIX_RANGE = ACED_Param(p + 1, 0, 7, n + 'Fixed Range')
        self.FIN       = ACED_Param(p + 2, 0, 15, n + 'Fine Freq')
        self.OSW       = ACED_Param(p + 3, 0,  7, n + 'Waveform')
        self.SHFT      = ACED_Param(p + 4, 0,  3, n + 'EG Shift')

    def __repr__(self):
        return 'OperatorParams({})'.format(self.operator)

class PARAM(object):
    # Parameters are organized here by section/pagination in TX81Z manual table.
    OP = {op:OperatorParams(op) for op in [1, 2, 3, 4]}

    ALG         = VCED_Param(52, 0,  7, 'Algorithm')
    FEEDBACK    = VCED_Param(53, 0,  7, 'OP4 Feedback')
    LFO_SPEED   = VCED_Param(54, 0, 99, 'LFO Speed')
    LFO_DELAY   = VCED_Param(55, 0, 99, 'LFO_Delay')
    P_MOD_DEPTH = VCED_Param(56, 0, 99, 'Pitch Mod Depth')
    A_MOD_DEPTH = VCED_Param(57, 0, 99, 'Amp Mod Depth')
    LFO_SYNC    = VCED_Param(58, 0,  1, 'LFO Sync')
    LFO_WAVE    = VCED_Param(59, 0,  3, 'LFO Wave')
    P_MOD_SENS  = VCED_Param(60, 0,  3, 'Pitch Mod Sens')
    AMS         = VCED_Param(61, 0,  3, 'Amp Mod Sens')
    TRANSPOSE   = VCED_Param(62, 0, 48, 'Transpose', 24)

    POLY         = VCED_Param(63, 0,  1, 'Poly/Mono')
    P_BEND_RANGE = VCED_Param(64, 0, 12, 'Pitchbend Range')
    PORTA_MODE   = VCED_Param(65, 0,  1, 'Portamento Mode')
    PORTA_TIME   = VCED_Param(66, 0, 99, 'Portamento Time')
    FC_VOL       = VCED_Param(67, 0, 99, 'Foot Control Volume')
    # Unclear what the next three are.
    SUSTAIN      = VCED_Param(68, 0,  1, 'Sustain')
    PORTAMENTO   = VCED_Param(69, 0,  1, 'Portamento')
    CHORUS       = VCED_Param(70, 0,  1, 'Chorus')
    MW_PITCH     = VCED_Param(71, 0, 99, 'Mod Wheel Pitch')
    MW_AMP       = VCED_Param(72, 0, 99, 'Mod Wheel Amp')
    BC_PITCH     = VCED_Param(73, 0, 99, 'Breath Control Pitch')
    BC_AMP       = VCED_Param(74, 0, 99, 'Breath Control Amp')

    BC_PITCH_BIAS = VCED_Param(75, 0, 99, 'Breath Control Pitch Bias', 50)
    BC_EG_BIAS    = VCED_Param(76, 0, 99, 'Breath Control EG Bias')
    NAME = [VCED_Param(77 + i, 32, 127, 'Name char {}'.format(i+1))
            for i in range(10)]

    # Performance parameters are not implemented yet.

    # Remote control parameters are not implemented yet.
