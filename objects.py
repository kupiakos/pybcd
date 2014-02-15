
from common import *

# object type format for bcd:
# 1 ? X   ????   X
# app imagetype  apptype

# 2   ?   1  ?????
# inherit any

# 2   ?   2  ????  X
# inherit app     apptype

# 2   ?   3  ?????
# inherit device

# 3 ???????
# device

ObjectType = enum(Application=0x1, Inheritable=0x2, Device=0x3)
ObjectImageType = enum(Firmware=0x1, Boot=0x2, Ntldr=0x3, Realmode=0x4)
ObjectAppType = enum(FirmwareMgr=0x1,
                     WinBootMgr=0x2,
                     WinBootLdr=0x3,
                     WinResume=0x4,
                     WinMemTest=0x5,
                     Ntldr=0x6,
                     Setupldr=0x7,
                     BootSect=0x8,
                     Startup=0x9)
ObjectInheritClass = enum(Library=0x1, Application=0x2, Device=0x3)


# known guids matching with the aliases and titles
knownguids = {
    # Application Objects
        '9dea862c-5cdd-4e70-acc1-f32b344d4795': ('bootmgr',
                                                 'Windows Boot Manager'),
        'a5a30fa2-3d06-4e9f-b5f4-a01df9d1fcba': ('fwbootmgr',
                                                 'Firmware Boot Manager'),
        'b2721d73-1db4-4c62-bf78-c548a880142d': ('memdiag',
                                                 'Windows Memory Tester'),
        '147aa509-0358-4473-b83b-d950dda00615': ('resume', # Why no alias, Microsoft?
                                                 'Windows Resume Application'),
        '466f5a88-0af2-4f76-9038-095b170dc21c': ('ntldr',
                                                 'Legacy windows Loader'),
        'fa926493-6f1c-4193-a414-58f0b2456d1e': ('current',
                                                 'Current Boot Entry'),
    # {default} is handled custom in the code
        
    # Inheritable Objects
        '5189b25c-5558-4bf2-bca4-289b11bd29e2': ('badmemory',
                                                 'RAM Defects'),
        '6efb52bf-1766-41db-a6b3-0ee5eff72bd7': ('bootloadersettings',
                                                 'Boot Loader Settings'),
        '4636856e-540f-4170-a130-a84776f4c654': ('dbgsettings',
                                                 'Debug Settings'),
        '0ce4991b-e6b3-4b16-b23c-5e0d9250e5d9': ('emssettings',
                                                 'Windows EMS Settings'),
        '7ea2e1ac-2e61-4728-aaa3-896d9d0a9f0e': ('globalsettings',
                                                 'Global Settings'),
        '1afa9c49-16ab-4a5c-901b-212802da9460': ('resumeloadersettings',
                                                 'Resume Loader Settings'),
        '7ff607e0-4395-11db-b0de-0800200c9a66': ('hypervisorsettings',
                                                 'Hypervisor Settings'),
        'ae5534e0-a924-466c-b836-758539a3ee3a': ('ramdiskoptions',
                                                 'Ramdisk Options')
    }
knownguids = {guid_bracket(k):(guid_bracket(v[0]), v[1])
              for k,v in knownguids.items()}

# for the objects that have no well known guid, but still need a title.
# probably because you can have more than one.
extratitles = {
    (1, 2, 3): 'Windows Boot Loader',
    (1, 1, 3): 'Windows Firmware Boot Loader',
    (1, 1, 0xFFFFF): 'Firmware Application',
    (1, 2, 4): 'Resume from Hibernate'
    }


def object_info(type):
    if isinstance(type, str):
        type = int(type, 16)
    #print(hex(type))
    return ((0xF0000000 & type) >> 28,
            (0x00F00000 & type) >> 20,
             0x000FFFFF & type)

def object_info_str(type):
    'Create a description based on the object type'
    #print(info)
    if isinstance(type, int):
        info = object_info(type)
    else:
        info = type
        type = info_to_objecttype(info)

    if info in extratitles:
        return extratitles[info]
    
    if info[0] == ObjectType.Application:
        return '%s-based %s Application (%s)' % \
               (ObjectImageType.reverse_mapping.get(info[1], str(info[1])),
                ObjectAppType.reverse_mapping.get(info[2], str(info[2])),
                hex(type)[2:])
    elif info[0] == ObjectType.Inheritable:
        return 'Inheritable for %s Applications (%s)' % (ObjectApptype, hex(type)[2:])
    elif info[0] == ObjectType.Device:
        if info[1:] == (0, 0):
            return 'Device options'
        return 'Unknown Device (%s)' % hex(type)[2:]

def info_to_objecttype(info):
    return (info[0] << 28 | 
            info[1] << 20 |
            info[2])

# END OF LINE.
