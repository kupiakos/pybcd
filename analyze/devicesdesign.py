
import os, sys, struct
sys.path.append('../test')

import bcd, functools, itertools

from objects import knownguids

store = bcd.BCD('BCDTest')
guids = [
    '{150e57bb-8333-11e3-a0d2-000c2994873a}',
    '{33238d8c-8333-11e3-a0d2-000c2994873a}',
    '{c66dfa6e-8332-11e3-a0d2-000c2994873a}',
    '{d99dfa6e-8442-22f3-b2d5-323c2953813d}',
    '{effdfa6e-8442-22f3-b2d5-323c2953814e}',
    '{fffdfa6e-8442-22f3-b2d5-323c2953814f}',
    ]

objs = []
for g in guids:
    objs.append(store[g].device)
    objs.append(store[g].osdevice)

boot, d1p1, d1p2, d1p22, d2p1, d2p2, \
      fboot, fd1p1, rboot, rd2p2, vloc, vd1p1 = objs

store2 = bcd.BCD('BCD2')

u1p1 = store2.bootmgr.device
u1p3 = store2.default.device

objs.extend((u1p1, u1p3))

objnames = ('boot\td1p1\td1p2\td1p22\td2p1\td2p2\tfboot\tfd1p1\t' +
      'rboot\trd2p2\tvloc\tvd1p1\tu1p1\tu1p3').split('\t')

rawhex = lambda x:', '.join([hex(int(i))[2:].rjust(2,'0') for i in x])

def promote(t):
	n = 0
	for j, i in enumerate(t):
		n += i << (j*8)
	return n
    
def guid_from(b):
    t = struct.unpack('IHH', b[:8]) + struct.unpack('>Q', b[8:])
    sizes = [8, 4, 4, 4, 12]
    l = []
    for s, r in zip(sizes, t):
        l.append(hex(r)[2:].lower().rjust(s, '0'))
    # l = list(map(lambda x:(hex(x)[2:].upper()), t))
    last = l[-1]
    l[-1] = last[:4]
    l.append(last[4:])
    return '{' + '-'.join(l) + '}'

# deviceentry

def _deviceentry_from(b):
    guid = None
    if any(b[:0x10]):
        guid = guid_from(b[:0x10])
        
    b = b[0x10:]
    return (b, guid)

def _packet_from(b):
    header = struct.unpack('IIII', b[:0x10])
    assert header[1] < 2
    #print(hex(header[2]))
    return (b[header[2]:],) + header + (b[0x10:header[2]],)

def _diskpartition_from(b):
    partid = b[:0x10]
    u3 = struct.unpack('I', b[0x10:0x14])[0]
    tabletype = struct.unpack('I', b[0x14:0x18])[0]
    diskid = b[0x18:0x28]
    u4 = struct.unpack('IIII', b[0x28:0x38])
    #print(rawhex(b))
    #print(rawhex(b[0x28:0x38]))
    #print(u4)
    assert not any(u4)
    assert u3 == 0
    
    if tabletype == 0: # gpt
        gpt = True
        partid = guid_from(partid)
        diskid = guid_from(diskid)
    elif tabletype == 1: # mbr
        gpt = False
        partid = promote(partid)
        diskid = promote(diskid)
    else:
        raise Exception('Unknown Disk Partition ID')

    return b[0x38:], partid, u3, gpt, diskid, u4

def _diskfile_from(b):
    dtype, u6, u7, u8 = struct.unpack('IIII', b[:0x10])
    b, ptype, u1, psize, u2, data = _packet_from(b[0x10:])
    pos = b.find(b'\x00\x00\x00')
    path = b[:pos+1].decode('utf-16')
    b = b[pos+3:]
    assert dtype in (0,5,6)
    return b, dtype, u6, u7, u8, ptype, data, path

def _ramdisk_from(b):
    u9 = struct.unpack('IIIIIIIII', b[:0x24])
    b = b[0x24:]
    
    assert u9[0] == 3
    assert not any(u9[1:5])
    assert u9[7] == len(b) + 12

    # the size is off by 4 in the "wrapping" packet...not sure why.
    # thorough investigation is needed.
    # packed using a "nonstandard" package for some reason.
    # the length in the packet is not the length of the whole packet. It's 4 off.
    # I'm not sure I get Microsoft sometimes...
    
    b, ptype, u1, psize, u2, data = _packet_from(b)
    #print(b.decode('utf-16'))
    #print(data)
    pos = b.find(b'\x00\x00\x00')
    path = b[:pos+1].decode('utf-16')
    b = b[pos+3:]
    
    return b, u9, ptype, data, path


def _vhddisk_from(b):
    u10, locatecustom, u11, u12 = struct.unpack('IIIH', b[:0x0E])
    b, ptype, u1, psize, u2, data = _packet_from(b[0x0E:])

    assert u10 == 0
    assert u11 == 0x1E
    assert u12 == 0
    
    return b, locatecustom, ptype, data

def _vhddiskfile_from(b):
    u13 = struct.unpack('I', b[:0x04])[0]
    u14 = struct.unpack('IIIII', b[0x04:0x18])

    assert u13 == 6
    assert not any(u14)

    b, ptype, u1, psize, u2, data = _packet_from(b[0x18:])

    return b, ptype, data
    

class BCDDevice:
    type = None # a string for now
    diskid = None
    gpt = None
    partid = None
    disk = None
    _raw = None

    def __init__(self, data=None):
        self._raw = data
        if data:
            self.frombin(data)

    def __repr__(self):
        return 'BCDDevice<' + self.friendly() + '>'

    @property
    def partoffset(self):
        if not self.gpt:
            return self.partid

    @partoffset.setter
    def partoffset(self, value):
        if not self.gpt:
            self.partid = value
    
    def friendly(self, locatedevices=False):
        s = ''
        if self.type == 'boot':
            s += 'boot'
        elif self.type in ('partition', 'ramdisk', 'file', 'vhd'):
            s += self.type + '='

            if self.type != 'partition':
                s += '['

            if self.disk == 'partition':
                if self.gpt:
                    diskid = self.diskid
                    partid = self.partid
                else:
                    diskid = hex(self.diskid)[2:]
                    partid = hex(self.partoffset)
                    
                s += '{diskid=%s,part%s=%s}' % (str(diskid),
                                                 'id' if self.gpt else 'offset',
                                                 str(partid))
            else:
                s += self.disk
            
            if self.type != 'partition':
                s += ']' + self.path

            if self.type == 'ramdisk' and self.optionsid:
                optionsid = self.optionsid
                if self.optionsid in knownguids:
                    optionsid = knownguids[self.optionsid.lower()][0]
                s += ',' + optionsid

            if self.type == 'vhd' and self.locatecustom != 0x12000002:
                s += ',locate=custom:' + hex(self.locatecustom)[2:]
        else:
            raise Exception('"%s" is not a valid BCDDevice type' % self.type)
        return s

    def frombin(self, b):
        'Load data from BCD binary device entry'
        # decided to go with linear instead of recursion this time
        b, self.optionsid = _deviceentry_from(b)
        _, ptype, u1, psize, u2, b = _packet_from(b)
        
        if ptype == 0: # file
            if u1 == 0:
                self.type = 'file'
                _, u5, u6, u7, u8, ptype, b, self.path = \
                   _diskfile_from(b)
                if ptype == 5:
                    self.disk = 'boot'
                else:
                    self.disk = 'partition'
                    b, self.partid, u3, self.gpt, self.diskid, u4 = \
                       _diskpartition_from(b)
            else:
                self.type = 'ramdisk'
                _, u9, ptype, b, self.path = \
                   _ramdisk_from(b)
                if ptype == 5:
                    self.disk = 'boot'
                else:
                    self.disk = 'partition'
                    b, self.partid, u3, self.gpt, self.diskid, u4 = \
                       _diskpartition_from(b)
                
        elif ptype == 5: # boot
            self.type = 'boot'
            self.disk = 'boot'
            return
        elif ptype == 6: # partition
            self.type = 'partition'
            self.disk = 'partition'
            b, self.partid, u3, self.gpt, self.diskid, u4 = \
               _diskpartition_from(b)
        elif ptype == 8: # vhd/locate
            self.type = 'vhd'
            _, self.locatecustom, ptype, b = \
               _vhddisk_from(b)
            _, ptype, b = \
               _vhddiskfile_from(b)
            _, u5, u6, u7, u8, ptype, b, self.path = \
               _diskfile_from(b)
            if ptype == 5:
                self.disk = 'boot'
            elif ptype == 8:
                self.disk = 'locate'
            else:
                self.disk = 'partition'
                b, self.partid, u3, self.gpt, self.diskid, u4 = \
                    _diskpartition_from(b)
            
        else:
            raise Exception('Unknown packet type %d' % ptype)
        
        
devs = []
for i, oraw in zip(objnames, objs):
    print(i)
    obj = BCDDevice(oraw)
    devs.append(obj)
    locals()[i] = obj
for b in devs:
    print(b.friendly())

# END OF LINE.  
