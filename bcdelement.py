
from common import *
from elements import *
from bcddevice import BCDDevice
        
class BCDElement:
    obj = None
    _type = None
    _changed = False
    _identifier = None
    _enum = None
    _value = None
    fmt = None
    
    def __init__(self, obj, type):
        self.obj = obj
        self._type = type
        self._type_info = element_info(self._type)
        self.fmt = self._type_info[1]
        self._enum = None
        self._value = None

    def __hash__(self):
        return hash((self._type, tuple(self.value)))

    def __str__(self):
        return 'BCDElement<%s=%s>' % (self.identifier, str(self.value))

    def __repr__(self):
        return str(self)

    def _find_identifier(self):
        self._identifier = None
        self._enum = None
        
        cls, fmt, subtype = self._type_info
        
        v = None
        
        if cls == ElementClass.Application:
            v = alias_dict[cls][self.obj._type_info[2]].get(subtype)
        else:
            v = alias_dict[cls].get(subtype)
        
        if v is None:
            v = (fmt, 'custom:%x' % int(self._type, 16))
        elif len(v) == 3:
            self._enum = v[2]
        
        self._identifier = v[1]
 
    def _load_value(self):
        self._value = self.obj._nav.value('Element', path='Elements/' + self._type)

    @property
    def identifier(self):
        if self._identifier is None:
            self._find_identifier()
        return self._identifier

    @property
    def value(self):
        if self._value is None:
            self._load_value()
        
        return element_transform[self._type_info[1]][1](self._value)

                                                             
    @value.setter
    def value(self, val):
        raise NotImplementedError('value setting not done yet')
        if self.name in element_transform:
            v = element_transform[self.name][0](self, val)
        else:
            v = val
        self._value = v

    def dump(self, tab='', verbose=False):
        p = print
        if self.identifier.startswith('custom:'):
            p = printwarn
        
        iv = self.value
        if self._enum:
            if iv not in self._enum.reverse_mapping:
                p = printwarn
            else:
                iv = self._enum.reverse_mapping[iv]
        
        v = element_transform_str.get(self.fmt, identity)(iv)
        
        vl = None # the value list, if it exists
        # handle the first of an objectlist
        if isinstance(iv, list) and len(v) > 0:
            vl = v[1:]
            v = v[0]
        
        # test if the guid exists
        if isguid(v):
            import random
            if v not in self.obj.bcd:
                p = printerror
            if not verbose:
                v = self.obj.bcd.guid_to_known(v)
        
        identifier = self.identifier 
        if verbose:
            identifier = '%s<%s>' % (self.identifier, self._type)
        
        # print the identifier
        (printelementname if p is print else p)(
            tab + identifier.ljust(DUMP_SPACING + int(verbose)*10),
            end='')
            
        if isinstance(v, BCDDevice):
            v = v.friendly(verbose)
        # print the value (or first value if we're a list)
        (p)(v)
        
        if vl:
            # do listy stuff
            for g in vl:
                p = print
                if isguid(g):
                    if g in self.obj.bcd:
                        if not verbose:
                            g = self.obj.bcd.guid_to_known(g)
                    else:
                        p = printerror
                
                p(tab + ' ' * (DUMP_SPACING + int(verbose)*10) + g)



# END OF LINE.
