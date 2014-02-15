
from common import *
from objects import *
from bcdelement import BCDElement

class BCDObject:
    rootnode = -1
    bcd = None
    _nav = None
    _guid = None
    _type = None
    _type_info = None
    title = None
    _elements = None
    changed = False
    apptype = None
    
    def __init__(self, bcd, guid=None):
        self.bcd = bcd
        self._guid = guid_bracket(guid)
        self._nav = self.bcd._nav.get('/Objects/' + self._guid)
        self._type = self._nav.value('Type', path='Description')
        self._type_info = object_info(self._type)
        self.apptype = self._type_info[2]
        
        if self._guid in knownguids:
            self.title = knownguids[self._guid][1]
        else:
            self.title = object_info_str(self._type)
            
        self.changed = False

    def __str__(self):
        return 'BCDObject%s' % self.identifier

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(frozenset((hash(e) for e in self.elements)))

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, identifier):
        for e in self.elements:
            if e.identifier == identifier or e._type == identifier:
                return e.value
        else:
            raise KeyError('Element "%s" not found' % identifier)
    
    def __contains__(self, identifier):
        try:
            self[identifier]
            return True
        except KeyError:
            return False
    
    def __setitem__(self, identifier, value):
        for e in self.elements:
            if e.identifier == identifier or e._type == identifier:
                pass
    
    def __getattr__(self, identifier):
        try:
            return self[identifier]
        except KeyError:
            raise AttributeError('Element "%s" not found' % identifier)
    
    def _generate_elements(self):
        self._elements = tuple((BCDElement(self, entry) for entry in self._nav.subkeys('Elements')))
    
    
    @property
    def guid(self):
        return self._guid

    @property
    def identifier(self):
        try:
            return self.bcd.guid_to_known(self.guid)
        except Exception:
            import traceback
            printerror('Error in bcdobject.identifier:', traceback.format_exc())

    @property
    def elements(self):
        if self._elements is None:
            self._generate_elements()
        return self._elements
    
    def dump(self, tab='', verbose=False):
        t = ''
        title = self.title
        if verbose:
            title += ' - %x' % (self._type)
        
        printheader('{0}{1}'.format(tab, title))
        printgreen('{0}{1}'.format(tab, '-' * len(title)))
        identifier = self.identifier if not verbose else self.guid
        printelementname(tab + 'identifier'.ljust(DUMP_SPACING + int(verbose)*10), end='')
        print(identifier)
        for e in self.elements:
            e.dump(tab + t, verbose)
        print()
    
   


