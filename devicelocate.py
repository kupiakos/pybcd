
import sys

from common import *

_devices = {}

if 'windows' in sys.platform:
    from devicelocatewin import scan_devices as _scan
else:
    from devicelocatelinux import scan_devices as _scan
    

def _scan_devices_linux():
    import pyudev
    context = pyudev.Context()
    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        print(device.get('DEVNAME'))
        print(int(device.get('ID_PART_ENTRY_OFFSET'))*512)
        print(hex(int(device.get('ID_PART_TABLE_UUID'), 16)))
        print()

def scan_devices(verbose=False):
    global _devices
    if verbose:
        printdebug('Scanning Devices...')
    _devices = _scan()
    if verbose:
        from pprint import pprint
        print(COLOR_DEBUG, end='')
        print('Devices Found:')
        pprint(_devices)
        print(COLOR_RESET, end='')

def entry_to_friendly(gpt, diskid, partid):
    return _devices.get((gpt, diskid, partid), ())


# END OF LINE.
