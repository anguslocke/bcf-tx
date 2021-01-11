import argparse, os

from tx81z_map import PARAM

'''
Big thanks to the BC Manager application
(https://mountainutilities.eu/bcmanager)

This module is intended to generate its .bcf files, which appear to be
a fairly straightforward text format.

'''

DEFAULT_CHANNEL = 4

class LED_MODE():
    ONEDOT = '1dot'
    ONEDOT_ZERO_OFF = '1dot/off'
    PAN = 'pan'

class TX81Z_Controller(object):
    '''Not meant to be used directly, but by subclasses'''
    def __init__(self, param, extra_data=None, channel=DEFAULT_CHANNEL, type=None):
        self.type = type
        self.param = param
        self.extra_data = extra_data if extra_data is not None else {}
        self.channel = channel

    def sysex(self):
        # Sysex is: standard bookend, Yamaha ID, 0x10 plus channel,
        #   group (+subgroup), parameter, value, standard bookend.
        return [0xf0, 0x43, 0x10 + ((self.channel - 1) & 0xf),
                self.param.group, self.param.parameter, 'val', 0xf7]

    def dump(self, index):
        key = self.type if self.type is not None else 'PLACEHOLDER'
        dump = ['${} {} ;{}\n'.format(key, index, self.param.name)]
        def hex_format(v):
            if isinstance(v, int): return '${:02X}'.format(v)
            else: return v
        params = {'showvalue': 'on',
                  'minmax': '{} {}'.format(self.param.min, self.param.max),
                  'tx': ' '.join([hex_format(v) for v in self.sysex()])}
        # The BC Manager software doesn't care about the order of these items
        params.update(self.extra_data)
        dump += ['  .{} {}\n'.format(key, value) for key, value in params.items()]
        return ''.join(dump)

class TX81Z_Encoder(TX81Z_Controller):
    def __init__(self, param, channel=DEFAULT_CHANNEL):
        extra_data = {'mode': LED_MODE.ONEDOT if param.center is None
                      else LED_MODE.PAN,
                      'resolution': ' '.join([str(param.resolution)] * 4)}
        super().__init__(param, extra_data, type='encoder')

class TX81Z_Fader(TX81Z_Controller):
    def __init__(self, param, channel=DEFAULT_CHANNEL):
        extra_data = {'motor': 'on',
                      'override': 'move',
                      'keyoverride': 'off'}
        super().__init__(param, extra_data, type='fader')

class TX81Z_Button(TX81Z_Controller):
    def __init__(self, param, channel=DEFAULT_CHANNEL, mode='down'):
        extra_data = {'mode': mode}
        super().__init__(param, extra_data, type='button')

class BCF_Preset(object):
    def __init__(self, name, lock=False):
        self.name = name
        self.lock = lock
        self.encoders = {}
        self.buttons = {}
        self.faders = {}

    def dump_encoders(self):
        return ''.join([self.encoders[i].dump(i) for i in self.encoders])

    def dump_buttons(self):
        return ''.join([self.buttons[i].dump(i) for i in self.buttons])

    def dump_faders(self):
        return ''.join([self.faders[i].dump(i) for i in self.faders])

    def dump(self):
        # First, the preset preamble.
        dump = ['$preset\n']
        # Not sure if the space-padding is essential, but whatever.
        params = {'name': "'{:<24}'".format(self.name),
                  'snapshot': 'off',
                  'request': 'off',
                  'egroups': 4,
                  'fkeys': 'on',
                  'lock': 'off',
                  'init': None}
        dump += ['  .{} {}\n'.format(key, value)
                 if value is not None else '  .{}\n'.format(key)
                 for key, value in params.items()]
        dump = ''.join(dump)
        dump += self.dump_encoders()
        dump += self.dump_buttons()
        dump += self.dump_faders()
        return dump

class BCF_Config(object):
    def __init__(self, rev='F1', firmware='1.10', version='4.1.1'):
        self.rev = rev
        self.firmware = firmware
        self.version = version
        self.set_global_config()
        self.presets = {}

    def set_global_config(self, params=None, **kwargs):
        defaults = {'midimode': 'U-1',
                    'startup': 'last',
                    'footsw': 'auto',
                    'rxch': 'off',
                    'txinterval': 100,
                    'deadtime': 100}
        if params is None:
            params = defaults
        params.update(kwargs)
        self.global_config = params

    def dump_global_config(self):
        dump = ['$global\n']
        dump += ['  .{} {}\n'.format(key, value)
                 for key, value in self.global_config.items()]
        return ''.join(dump)

    def dump_presets(self):
        dump = ''
        for i in range(1, 33):
            dump += self.presets.get(i, BCF_Preset('')).dump()
            dump += '$store {}\n'.format(i)
        # The working "preset 0" appears to just show up at the end.
        if 0 in self.presets:
            dump += self.presets[0].dump()
        else:
            dump += self.presets[1].dump()
        # With no "$store" line
        return dump

    def dump(self):
        dump = '$rev {} ; Firmware {}; BC Manager {}\n'
        dump = dump.format(self.rev, self.firmware, self.version)
        dump += self.dump_global_config()
        dump += self.dump_presets()
        dump += '$end\n'
        return dump

def super_config_1(path='/tmp/test.bcf'):
    # Construct a .bcf save with a TX81Z mapping.
    c = BCF_Config()
    p = BCF_Preset('Page 1')
    c.presets[1] = p

    encoder_map = {}
    for i in range(4):
        o = i + 1
        g = 8 * i
        operator_encoders = {
            g + 1: PARAM.OP[o].AR,
            g + 2: PARAM.OP[o].D1R,
            g + 3: PARAM.OP[o].D2R,
            g + 4: PARAM.OP[o].RR,
            g + 6: PARAM.OP[o].OSW,
            g + 7: PARAM.OP[o].CRS,
            g + 8: PARAM.OP[o].FIN,
        }
        encoder_map.update(operator_encoders)
    p.encoders = {k:TX81Z_Encoder(v) for k, v in encoder_map.items()}

    fader_map = {}
    for o in range(1, 5):
        fader_map[o] = PARAM.OP[o].D1L
    for o in range(1, 5):
        fader_map[4 + o] = PARAM.OP[o].OUT
    p.faders = {k:TX81Z_Fader(v) for k, v in fader_map.items()}

    button_map = {}
    p.buttons = {k:TX81Z_Button(v) for k, v in button_map.items()}

    path = os.path.expanduser(path)
    if os.path.isdir(path):
        path = os.path.join(path, 'config.bcf')
    if os.path.splitext(path)[1] != '.bcf':
        path += '.bcf'
    with open(path, 'w+') as f:
        f.write(c.dump())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export a TX81Z BCF2000 map')
    parser.add_argument('path', nargs='?',
                        default='TX81Z_ch{}_map'.format(DEFAULT_CHANNEL))
    args = parser.parse_args()

    super_config_1(args.path)
