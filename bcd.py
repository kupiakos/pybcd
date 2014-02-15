

from common import *
from hivenavigator import HiveNavigator
from bcdobject import BCDObject, knownguids
from bcdelement import BCDElement

from devicelocate import scan_devices



class BCD:
    _nav = None
    changed = False
    readonly = False
    _objects = None
    
    def __init__(self, src, readonly=True):
        '''TODO: docs'''
        self.changed = False
        self.readonly = readonly
        self._nav = HiveNavigator(src,)# write=(not readonly))
        self._nav.seek('/')

    def __getitem__(self, guid):
        guid = guid_bracket(guid)
        for o in self.objects:
            if o.guid == guid or knownguids.get(o.guid,[None])[0] == guid:
                return o
        else:
            raise KeyError('No guid ' + guid)
    
    def __iter__(self):
        return iter(self.objects)
    
    def __getattr__(self, guid):
        try:
            return self[guid_bracket(guid)]
        except KeyError:
            raise AttributeError('No guid ' + guid)
            
    def __contains__(self, guid):
        try:
            self[guid]
            return True
        except KeyError:
            return False

    def __hash__(self):
        return hash(frozenset((hash(o) for o in self.objects)))

    def _generate_objects(self):
        self._objects = tuple((BCDObject(self, guid) for guid in self._nav.subkeys('/Objects')))

    def guid_to_known(self, guid):
        guid = guid_bracket(guid)
        
        v = knownguids.get(guid)
        
        if v:
            return v[0]
            
        default = self.default
        
        if default and guid == default.guid:
            return '{default}'
        else:
            return guid

    @property
    @cacheresult
    def description(self):
        return self._nav.value('KeyName', '/Description')

    @property
    def objects(self):
        if self._objects is None:
            self._generate_objects()
        return self._objects
        
    @property
    def osloaders(self):
        return [i for i in self.objects 
                if i._type_info == (1,2,3) or 
                   i._type_info == (1,3,3)]


    @property
    def default(self):
        try:
            return self[self.bootmgr.default]
        except AttributeError:
            #import traceback
            #printerror('Error in default:\n', traceback.format_exc())
            return None

    def dump(self, tab='', verbose=False):
        scan_devices(verbose)
        for o in self.objects:
            o.dump(tab, verbose)

# END OF LINE.
