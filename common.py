

import re


from colors import *

# how many characters are reserved for an element name when dumping
DUMP_SPACING = 24


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = {value: key for key, value in enums.items()}
    enumsl = {key.lower():value for key, value in enums.items()}
    def cast(self, x):
        if isinstance(x, str):
            v = enumsl.get(x.lower())
            if v:
                return v
            else:
                raise KeyError(x + ' is not a valid enum value')
        else:
            return x
        
    enums['reverse_mapping'] = reverse
    enums['__new__'] = cast
    return type('Enum', (), enums)

def guid_bracket(val, strict=False):
    if (not strict) or isguid(val):
        if val.startswith('{'):
            return val
        else:
            return '{' + val + '}'
    else:
        raise ValueError('"%s" is not a valid guid' % val)

def guid_unbracket(val, strict=True):
    if (not strict) or isguid(val):
        if val.startswith('{'):
            return val[1:-1]
        else:
            return val
    else:
        raise ValueError('"%s" is not a valid guid' % val)
            

def isguid(val):
    val = str(val)
    if (val.count('{') ^ val.count('}')) or val.count('{') > 1:
        return False
    exp = r'^\{?[0-9A-Fa-f]{8}-([0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}\}?$'
    return bool(re.match(exp, val))

def isint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

def cacheresult(func):
    name = '_' + func.__name__
    def load(self):
        if hasattr(self, name):
            return getattr(self, name)
        else:
            val = func(self)
            setattr(self, name, val)
            return val
    return load
    
    

class callbacklist(list):
	'A list that calls a function when changed'
	callback = None
	def _call(self):
		if callable(self.callback):
			self.callback()
	def __init__(self, *args, **kwargs):
		list.__init__(self, *args, **kwargs)
		for i in ('append', 'clear', 'extend',
			  'insert', 'pop', 'remove',
			  'reverse', 'sort'):
			def repl(func):
				def newfunc(*args, **kwargs):
					v = func(*args, **kwargs)
					self._call()
					return v
				return newfunc
			setattr(self, i, repl(getattr(self, i)))

identity = lambda x:x

# END OF LINE
