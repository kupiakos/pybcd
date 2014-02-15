
import struct

from common import *
from objects import ObjectAppType
from bcddevice import BCDDevice


# element types:
# X     X ???? XX
# class format subtype

# class:
# 1 = Library
# 2 = Application
# 3 = Device

# format:
# 0 = Unknown
# 1 = Device
# 2 = String
# 3 = Object
# 4 = Object List
# 5 = Integer
# 6 = Boolean
# 7 = IntegerList

ElementClass = enum(Library=0x1, 
                    Application=0x2, 
                    Device=0x3, 
                    Hidden=0x4)
                    
ElementFormat = enum(Unknown=0, 
                     Device=1, 
                     String=2, 
                     Object=3,
                     ObjectList=4,
                     Integer=5, 
                     Boolean=6, 
                     IntegerList=7)



# based on both my personal findings and on this website:
# http://www.geoffchappell.com/notes/windows/boot/bcd/elements.htm?tx=5

_library = {
    0x01: (1, 'device'),
    0x02: (2, 'path'),
    0x04: (2, 'description'),
    0x05: (2, 'locale'),
    0x06: (4, 'inherit'),
    0x07: (5, 'truncatememory'),
    0x08: (4, 'recoverysequence'),
    0x09: (6, 'recoveryenabled'),
    0x0A: (7, 'badmemorylist'),
    0x0B: (6, 'badmemoryaccess'),
    0x0C: (5, 'firstmegabytepolicy', enum('UseNone','UseAll','UsePrivate')),
    0x0D: (5, 'relocatephysical'),
    0x0E: (5, 'avoidlowmemory'),
    0x0F: (6, 'traditionalksegmappings'),
    0x10: (6, 'bootdebug'),
    0x11: (5, 'debugtype', enum('Serial','1394','USB')),
    0x12: (5, 'debugaddress'),
    0x13: (5, 'debugport'),
    0x14: (5, 'baudrate'),
    0x15: (5, 'channel'),
    0x16: (2, 'targetname'),
    0x17: (6, 'noumex'),
    0x18: (5, 'debugstart', enum('Active', 'AutoEnable', 'Disable')),
    0x19: (2, 'busparams'),
    0x20: (6, 'bootems'),
    0x22: (5, 'emsport'),
    0x23: (5, 'emsbaudrate'),
    0x30: (2, 'loadoptions'),
    0x31: (6, 'attemptnonbcdstart'),
    0x40: (6, 'advancedoptions'),
    0x41: (6, 'optionsedit'),
    0x42: (5, 'keyringaddress'),
    # no alias
    0x43: (1, 'bootstatusdatalogdevice'), 
    # no alias
    0x44: (2, 'bootstatusdatalogfile'),   
    # no alias
    0x45: (6, 'bootstatusdatalogappend'), 
    0x46: (6, 'graphicsmodedisabled'),
    0x47: (5, 'configaccesspolicy', enum('Default', 'DisallowMmConfig')),
    0x48: (6, 'nointegritychecks'),
    0x49: (6, 'testsigning'),
    0x4A: (2, 'fontpath'),
    # seems to be wrong in the table?
    0x4B: (5, 'integrityservices'), 
    0x50: (6, 'extendedinput'),
    0x51: (5, 'initialconsoleinput'),
    # not in table
    0x60: (6, 'isolatedcontext'), 
    # not in table
    0x65: (5, 'displaymessage', enum('Default','Resume','HyperV', 'Recovery','StartupRepair', 'SystemImageRecovery','CommandPrompt', 'SystemRestore', 'PushButtonReset')),
    # not in table
    0x77: (7, 'allowedinmemorysettings'), 
}

_bootmgr = {
    0x01: (4, 'displayorder'),
    0x02: (4, 'bootsequence'),
    0x03: (3, 'default'),
    0x04: (5, 'timeout'),
    0x05: (6, 'resume'),
    0x06: (3, 'resumeobject'),
    0x10: (4, 'toolsdisplayorder'),
    0x20: (6, 'displaybootmenu'),
    0x21: (6, 'noerrordisplay'),
    0x22: (1, 'bcddevice'),
    0x23: (2, 'bcdfilepath'),
    0x30: (7, 'customactions'),
}

_osloader = {
    0x001: (1, 'osdevice'),
    0x002: (2, 'systemroot'),
    0x003: (3, 'resumeobject'),
    0x004: (6, 'stampdisks'),
    0x010: (6, 'detecthal'),
    0x011: (2, 'kernel'),
    0x012: (2, 'hal'),
    0x013: (2, 'dbgtransport'),
    0x020: (5, 'nx', enum('OptIn', 'OptOut', 'AlwaysOff', 'AlwaysOn')),
    0x021: (5, 'pae', enum('Default', 'ForceEnable', 'ForceDisable')),
    0x022: (6, 'winpe'),
    0x024: (6, 'nocrashautoreboot'),
    0x025: (6, 'lastknowngood'),
    0x026: (6, 'oslnointegritychecks'),
    0x027: (6, 'osltestsigning'),
    0x030: (6, 'nolowmem'),
    0x031: (5, 'removememory'),
    0x032: (5, 'increaseuserva'),
    0x033: (5, 'perfmem'),
    0x040: (6, 'vga'),
    0x041: (6, 'quietboot'),
    0x042: (6, 'novesa'),
    0x050: (5, 'clustermodeaddressing'),
    0x051: (6, 'usephysicaldestination'),
    0x052: (5, 'restrictapiccluster'),
    0x053: (2, 'evstore'),
    0x054: (6, 'uselegacyapicmode'),
    0x060: (6, 'onecpu'),
    0x061: (5, 'numproc'),
    0x062: (6, 'maxproc'),
    0x063: (5, 'configflags'),
    0x064: (6, 'maxgroup'),
    0x065: (6, 'groupaware'),
    0x066: (5, 'groupsize'),
    0x070: (6, 'usefirmwarepcisettings'),
    0x071: (5, 'msi', enum('Default', 'ForceDisable')),
    0x072: (5, 'pciexpress', enum('Default', 'ForceDisable')),
    0x080: (5, 'safeboot', enum('Minimal', 'Network', 'DsRepair')),
    0x081: (6, 'safebootalternateshell'),
    0x090: (6, 'bootlog'),
    0x091: (6, 'sos'),
    0x0A0: (6, 'debug'),
    0x0A1: (6, 'halbreakpoint'),
    0x0A2: (6, 'useplatformclock'),
    0x0B0: (6, 'ems'),
    # no alias
    0x0C0: (5, 'forcefailure', enum('Load', 'Hive', 'Acpi', 'General')),
    0x0C1: (5, 'driverloadfailurepolicy', enum('Fatal', 'UseErrorControl')),
    # not in table
    0x0C2: (5, 'bootmenupolicy', enum('TODO0', 'Standard', 'TODO2', 'TODO3')),
    0x0E0: (5, 'bootstatuspolicy', enum('DisplayAllFailures', 'IgnoreAllFailures', 'IgnoreShutdownFailures', 'IgnoreBootFailures')),
    0x0F0: (5, 'hypervisorlaunchtype', enum('Off', 'Auto')),
    0x0F1: (2, 'hypervisorpath'),
    0x0F2: (6, 'hypervisordebug'),
    0x0F3: (5, 'hypervisordebugtype', enum('Serial', '1394')),
    0x0F4: (5, 'hypervisordebugport'),
    0x0F5: (5, 'hypervisorbaudrate'),
    0x0F6: (5, 'hypervisorchannel'),
    # not a lot known
    0x0F7: (5, 'bootuxpolicy'),
    0x0F8: (6, 'hypervisordisableslat'),
    0x100: (5, 'tpmbootentropy', enum('Default', 'ForceDisable', 'ForceEnable')),
    0x120: (5, 'xsavepolicy'),
    0x121: (5, 'xsaveaddfeature0'),
    0x122: (5, 'xsaveaddfeature1'),
    0x123: (5, 'xsaveaddfeature2'),
    0x124: (5, 'xsaveaddfeature3'),
    0x125: (5, 'xsaveaddfeature4'),
    0x126: (5, 'xsaveaddfeature5'),
    0x127: (5, 'xsaveaddfeature6'),
    0x128: (5, 'xsaveaddfeature7'),
    0x129: (5, 'xsaveremovefeature'),
    0x12A: (5, 'xsaveprocessorsmask'),
    0x12B: (5, 'xsavedisable'),
}

_resume = {
    0x01: (1, 'filedevice'),
    0x02: (2, 'filepath'),
    0x03: (6, 'customsettings'),
    0x04: (6, 'pae'),
    0x05: (1, 'associatedosdevice'),
    0x06: (6, 'debugoptionenabled'),
    0x07: (5, 'bootux', enum('Disabled', 'Basic', 'Standard')),
    # not in table
    0x08: (5, 'bootmenupolicy', enum('TODO0', 'Standard', 'TODO2', 'TODO3')),
}

_memdiag = {
    0x01: (5, 'passcount'),
    0x02: (5, 'testmix', enum('Basic', 'Extended')),
    0x03: (5, 'failurecount'),
    0x04: (5, 'testtofail', enum('Stride', 'Mats', 'InverseCoupling', 'RandomPattern', 'Checkerboard')),
    0x05: (6, 'cacheenable'),
}

_ntldr = {
    0x01: (2, 'bpbstring'),
}

_startup = {
    0x01: (6, 'pxesoftreboot'),
    0x02: (2, 'applicationname'),
}

_device = {
    0x01: (5, 'ramdiskimageoffset'),
    0x02: (5, 'ramdiskftpclientport'),
    0x03: (1, 'ramdisksdidevice'),
    0x04: (2, 'ramdisksdipath'),
    0x05: (5, 'ramdiskimagelength'),
    0x06: (6, 'exportascd'),
    0x07: (5, 'ramdisktftpblocksize'),
    0x08: (5, 'ramdisktftpwindowsize'),
    0x09: (6, 'ramdiskmcenabled'),
    0x0A: (6, 'ramdiskmctftpfallback'),
}

# All of these are hidden during a bcdedit /enum all command
# I design good software, so I'll show it even if bcdedit doesn't.
_setup = {
    0x01: (1, 'devicetype'),
    0x02: (2, 'applicationrelativepath'),
    0x03: (2, 'ramdiskdevicerelativepath'),
    0x04: (6, 'omitosloaderelements'),
    0x10: (6, 'recoveryos'),
}

alias_dict = {
    # applies to all object types
    ElementClass.Library: _library,

    # these depend on the application
    ElementClass.Application: {
        #objectapptype
        0: {},
        ObjectAppType.FirmwareMgr: _bootmgr,
        ObjectAppType.WinBootMgr:  _bootmgr,
        ObjectAppType.WinBootLdr:  _osloader,
        ObjectAppType.WinResume:   _resume,
        ObjectAppType.WinMemTest:  _memdiag,
        ObjectAppType.Ntldr:       _ntldr,
        ObjectAppType.Setupldr:    _ntldr,
        ObjectAppType.BootSect:    {},
        ObjectAppType.Startup:     _startup,
    },

    # only works for devices
    ElementClass.Device : _device,

    # setup template elements
    ElementClass.Hidden: _setup,
    
}

def element_info(type):
    if isinstance(type, str):
        type = int(type, 16)
    return ((0xF0000000 & type) >> 28,
            (0x0F000000 & type) >> 24,
             0x00FFFFFF & type)
             
# transformation functions from the BCD raw format to Python.
# tuple of to/from functions
_bcdqword = (lambda v:struct.pack('Q', v),
            lambda v:struct.unpack('Q', v)[0])
            
_bcdqwordlist = (lambda v:b''.join((struct.pack('Q', v) for v in l)),
                 lambda v:list((struct.unpack('Q', bytes(j))[0] 
                                for j in zip(*[v[i::8] 
                                               for i in range(8)]))))

_bcdtodo  = (lambda v:'TODO',
            lambda v:'TODO')

_bcdraw = (identity, identity)
_bcdobj = _bcdraw
_bcdobjlist = _bcdraw

# different ways to express booleans
_boolnames = {'0'    : False,
             '1'    : True,
             'on'   : True,
             'off'  : False,
             'true' : True,
             'false': False,
             'yes'  : True,
             'no'   : False}

_bcdbool  = (lambda v: bytes([int(_boolnames.get(v.lower(), v)
                                   if isinstance(v,str) else v)]),
            lambda v: bool(v[0]),
            lambda v: ('No', 'Yes')[int(v)])

_bcddevice = (None, lambda v:BCDDevice(v))

# Match transformation functions to ElementFormats.
element_transform = {
    ElementFormat.Device:      _bcddevice,#_bcdtodo,
    ElementFormat.String:      _bcdraw,
    ElementFormat.Object:      _bcdobj,
    ElementFormat.ObjectList:  _bcdobjlist,
    ElementFormat.Integer:     _bcdqword,
    ElementFormat.Boolean:     _bcdbool,
    ElementFormat.IntegerList: _bcdqwordlist,
}

element_transform_str = {
    ElementFormat.IntegerList: lambda v:[hex(i) for i in v],
}

# END OF LINE.
