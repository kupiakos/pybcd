
from struct import unpack_from
from uuid import UUID
import ctypes
import re


kernel32 = ctypes.windll.kernel32

FindFirstVolume                   = kernel32.FindFirstVolumeW
FindNextVolume                    = kernel32.FindNextVolumeW
FindVolumeClose                   = kernel32.FindVolumeClose

CreateFile                        = kernel32.CreateFileW
CloseHandle                       = kernel32.CloseHandle
DeviceIoControl                   = kernel32.DeviceIoControl

GetLastError                      = kernel32.GetLastError

QueryDosDevice                    = kernel32.QueryDosDeviceW
GetVolumePathNamesForVolumeName   = kernel32.GetVolumePathNamesForVolumeNameW
GateVolumeNameForVolumeMountPoint = kernel32.GetVolumeNameForVolumeMountPointW

OPEN_EXISTING                        = 0x00000003
IOCTL_DISK_GET_DRIVE_LAYOUT_EX       = 0x00070050
IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS = 0x00560000



splitchunks = lambda b,l:[b[i:i+l]
                          for i in range(0, len(b), l)]

def isguid(val):
    val = str(val)
    if (val.count('{') ^ val.count('}')) or val.count('{') > 1:
        return False
    exp = r'^\{?[0-9A-Fa-f]{8}-([0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}\}?$'
    return bool(re.match(exp, val))

def list_drives():
    buffer = (ctypes.c_wchar * 256)()
    for d in range(255):
        s = 'PhysicalDrive%d' % d
        if not QueryDosDevice(s, buffer, len(buffer)):
            break
        yield s

def list_volumeguids():
    buffer = (ctypes.c_wchar * 50)()
    try:
        handle = FindFirstVolume(buffer, len(buffer))
        # do not include the nulls, path designator, or last backslash
        yield [i for i in buffer.value.split('\x00') if i][0][10:-1]
        while FindNextVolume(handle, buffer, len(buffer)):
            yield [i for i in buffer.value.split('\x00') if i][0][10:-1]
    except Exception:
        pass
    finally:
        try:
            FindVolumeClose(handle)
        except Exception:
            pass

def get_driveletter(volumeguid):
    buffer = (ctypes.c_wchar * 256)()
    numout = ctypes.c_int(0)
    if (volumeguid.startswith('\\\\?\\Volume') and
        not volumeguid.endswith('\\')):
        volumeguid += '\\'
    if isguid(volumeguid):
        volumeguid = '\\\\?\\Volume%s\\'
    if volumeguid.startswith('Volume'):
        volumeguid = '\\\\?\\%s\\' % volumeguid
    if not GetVolumePathNamesForVolumeName(volumeguid,
                                           buffer,
                                           len(buffer),
                                           ctypes.pointer(numout)):
        return ''
    l = filter(None, buffer.value.split('\x00'))
    for mnt in l:
        if len(mnt) == 3 and ord('A') <= ord(mnt[0]) <= ord('Z'):
            return mnt[:2]
    return ''

def get_volumedevice(volume):
    'Get Device Volume name (e.g. \\Device\\HarddiskVolume1) from C: or GUID'
    volume = volume.strip('\x00').strip('\\').strip('.').strip('?').strip('\\')
    if isguid(volume):
        volume = 'Volume' + volume
    buffer = (ctypes.c_wchar * 256)()
    l = QueryDosDevice(volume, buffer, len(buffer))
    return buffer[:l].strip('\x00')

def get_volumeguid(devicename):
    'Get Volume GUID from Volume Device Name (HarddiskVolume1)'
    if (devicename[1] == ':' and
        ord('A') <= ord(devicename[0].upper()) <= ord('Z')):
        devicename = devicename[0] + ':\\'
    else:
        devicename = '\\\\.\\' + \
                 devicename.lstrip('\\Device\\').rstrip('\\') + \
                 '\\'
    buffer = (ctypes.c_wchar * 50)
    if GetVolumeNameForVolumeMountPoint(devicename, buffer, len(buffer)):
        return buffer.value[10:-1]
    else:
        return ''

def get_volumespan(volume):
    'Return (drive number, partition offset) for a volume'
    
    volume = '\\\\.\\%s%s' % (
                'Volume' if 'Volume{' in volume or isguid(volume) else '',
                volume.strip('\\').strip('.'
                    ).strip('?').strip('\\').strip('Volume')
                )
    buffer = bytes(1024 * 16)
    numret = ctypes.c_int(0)
    f = CreateFile(volume, 0, 0, None, OPEN_EXISTING, 0, None)
    DeviceIoControl(f, IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS,
                        None, 1, buffer, len(buffer),
                        ctypes.pointer(numret), None)
    CloseHandle(f)
    d = buffer[:numret.value]
    return unpack_from('IQ', d, 8)

def scan_volumes():
    'Yield (drive number, partition offset, partition guid) for each volume'
    for guid in list_volumeguids():
        try:
            num, offset = get_volumespan(guid)
            yield (num, offset, guid)
        except Exception:
            pass

def scan_drive(deviceid):
    deviceid = '\\\\.\\%s' % (
        deviceid.strip('\\').strip('?').strip('.').strip('\\'))
    
    f = CreateFile(deviceid, 0,0, None, OPEN_EXISTING, 0, None)
    buffer = bytes(1024 * 16)
    numret = ctypes.c_int(0)
    if not DeviceIoControl(f, IOCTL_DISK_GET_DRIVE_LAYOUT_EX, None, 1,
                        buffer, len(buffer),
                        ctypes.pointer(numret), None):
        raise Exception('Could not scan the drive', deviceid)
    CloseHandle(f)
    
    d = buffer[:numret.value]
    gpt = bool(unpack_from('I', d[:4])[0])

    if gpt:
        diskid = '{' + str(UUID(bytes_le=d[8:24])) + '}'
    else:
        diskid = unpack_from('I', d[8:12])[0]

    partitions = splitchunks(d[48:], 144)
    partids = []

    for part in partitions:
        letter = None
        if not part[37]:
            break
        if gpt:
            partid = '{' + str(UUID(bytes_le=part[48:64])) + '}'
        else:
            partid = unpack_from('Q', part, 8)[0]
            #for i in c:
                #if i

        partids.append(partid)

    return (gpt, diskid, partids)
        
    
def scan_drives():
    for deviceid in list_drives():
        yield scan_drive(deviceid)


def scan_devices():
    d = {}
    volumes = list(scan_volumes())
    for disknum, (gpt, diskid, partids) in enumerate(scan_drives()):
        for partid in partids:
            partguid = None
            if gpt:
                for n, off, guid in volumes:
                    if (n, guid) == (disknum, partid):
                        partguid = partid
                        break
                else:
                    continue # we probably have a hidden volume
            else:
                for n, off, guid in volumes:
                    if (n, off) == (disknum, partid):
                        partguid = guid
                        break
                else:
                    continue # no volume found matching the partition
            partguid = 'Volume' + partguid
            driveletter = get_driveletter(partguid)
            devicename = get_volumedevice(partguid)
            names = []
            if driveletter:
                names.append(driveletter)
            names.append(devicename)
            names.append(partguid)
            names = tuple(names)
            d[(gpt, diskid, partid)] = names
    return d
            
                    

#scan_drives()

