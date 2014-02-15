
import os, sys, struct
sys.path.append('../test')

import bcd, functools, itertools

b = bcd.BCD('BCDTest')
guids = [
    '{150e57bb-8333-11e3-a0d2-000c2994873a}',
    '{33238d8c-8333-11e3-a0d2-000c2994873a}',
    '{c66dfa6e-8332-11e3-a0d2-000c2994873a}',
    '{d99dfa6e-8442-22f3-b2d5-323c2953813d}',
    '{effdfa6e-8442-22f3-b2d5-323c2953814e}',
    '{fffdfa6e-8442-22f3-b2d5-323c2953814f}',
    ]

raw = lambda x:[int(i) for i in x]

objs = []
for g in guids:
    objs.append(b[g].device._raw)
    objs.append(b[g].osdevice._raw)

boot, d1p1, d1p2, d1p22, d2p1, d2p2, \
      fboot, fd1p1, rboot, rd2p2, vloc, vd1p1 = objs
                                
def guid(b):
    t = struct.unpack('IHH', b[:8]) + struct.unpack('>Q', b[8:])
    l = list(map(lambda x:(hex(x)[2:].upper()), t))
    last = l[-1]
    l[-1] = last[:4]
    l.append(last[4:])
    return '{' + '-'.join(l) + '}'

def promote(t):
	n = 0
	for j, i in enumerate(t):
		n += i << (j*8)
	return n

# return ((type, u1, size, u2), contents, nextpos)
def readpacket(s, p):
    header = struct.unpack_from('IIII', s, p)
    d = s[p+16:p+header[2]]
    return (header, d, p + header[2])

b2 = bcd.BCD('BCD2')

u1p1 = b2.bootmgr.device._raw
u1p3 = b2.default.device._raw

print('offset\tboot\td1p1\td1p2\td1p22\td2p1\td2p2\tfboot\tfd1p1\t' +
      'rboot\trd2p2\tvloc\tvd1p1\tu1p1\tu1p3')
n = 0

objs.append(u1p1)
objs.append(u1p3)

for i in itertools.zip_longest(
        range(max((len(d) for d in objs))),
        *objs):
    print(*map(lambda x:(hex(x)[2:].upper() if isinstance(x, int) else '~'), i),
          sep='\t')
    #n += 1
    #if n % 2 == 0:
    #    print()

# END OF LINE.
