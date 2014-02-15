
import pyudev

def scan_devices():
    context = pyudev.Context()
    d = {}
    
    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        devname = device.get('DEVNAME')
        gpt = device.get('ID_PART_ENTRY_SCHEME') == 'gpt'
        diskid = device.get('ID_PART_TABLE_UUID')
        
        if gpt:
            partid = device.get('ID_PART_ENTRY_UUID')
        else:
            diskid = int(diskid,16)
            partid = int(device.get('ID_PART_ENTRY_OFFSET'))*512
            
        d[(gpt, diskid, partid)] = (devname,)
    return d
