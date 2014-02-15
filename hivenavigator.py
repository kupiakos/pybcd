#######################################
# hivenavigator.py                    #
# Author:  Kevin Haroldsen (Kupiakos) #
# Version: 1.0                        #
# Date:    2014-01-02                 #
# ----------------------------------- #
# The perfect companion class to      #
# hivex, it's a HiveNavigator that    #
# allows simple parsing of a registry #
# hive.                               #
#######################################

################################################################################
# The MIT License (MIT)
# 
# Copyright (c) 2014 Kevin Haroldsen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################

import os
import hivex
import libhivexmod
import re

REG_NONE = 0
REG_SZ = 1
REG_EXPAND_SZ = 2
REG_BINARY = 3
REG_DWORD = 4
REG_DWORD_BIG_ENDIAN = 5
REG_LINK = 6
REG_MULTI_SZ = 7
REG_RESOURCE_LIST = 8
REG_FULL_RESOURCE_DESCRIPTIOR = 9
REG_RESOURCE_REQUIREMENTS_LISTS = 10
REG_QWORD = 11

# TODO: ADD WRITE SUPPORT



class HiveNavigator(object):
    hive = None
    _nav = None
    _root = None

    def __init__(self, hive):
        if (isinstance(hive, hivex.Hivex)):
            self.hive = hive
        elif isinstance(hive, str):
            if os.path.exists(hive):
                self.hive = self._load_hive(hive)
            else:
                raise FileNotFoundError('File "%s" does not exist!' % hive)
        elif isinstance(hive, self.__class__):
            self.seek(hive.tell())
        else:
            raise ValueError('hive must be a Hivex or str object')
        self._root = self.hive.root()
        self._nav = [self._root]

    def _load_hive(self, fname):
        # because hivex craps out with a bad file, but still tries to release in the
        # __del__ method, we first check here to see if it can all be loaded.
        try:
            h = libhivexmod.open(fname, 0)
            libhivexmod.close(h)
        except RuntimeError:
            raise IOError('Unable to load the registry hive "%s"!' % fname)
            sys.exit(2)
        return hivex.Hivex(fname)

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.tell())

    def __repr__(self):
        return str(self)

    @property
    def _cur(self):
        'The currently focused inode'
        return self._nav[-1]
    
    def get(self, path):
        'Get a new HiveNavigator class focused at path.'
        new = self.__class__(self.hive)
        new._nav = self._nav
        new.seek(path)
        return new

    def seek(self, path):
        'Seek to a new subkey. Inodes and paths are supported.'
        newnav = []
        if isinstance(path, int):
            try:
                while path != self._root:
                    newnav.append(path)
                    path = self.hive.node_parent(path)
                newnav.append(self._root)
                newnav.reverse()
            except RuntimeError:
                raise ValueError('Could not locate node %d' % path)
            
        elif isinstance(path, str):
            keypath = re.split(r'\\|/', path.rstrip('/\\'))
            
            if keypath:
                newnav = self._nav[:]
                for key in keypath:
                    if not key:
                        newnav = [self._root]
                    elif key == '.':
                        continue
                    elif key == '..':
                        if len(newnav) > 1:
                            newnav.pop()
                    else:
                        try:
                            child = self.hive.node_get_child(newnav[-1], key)
                            if not child:
                                raise RuntimeError
                            newnav.append(child)
                        except RuntimeError:
                            raise ValueError(
                                'Could not locate key "%s" in path "%s"' % (key, path))
            else:
                newnav = []
                
        else:
            raise ValueError('path must be a string or number')
        
        self._nav = newnav

    def exists(self, path):
        'Returns True if the given pathation (key) exists.'
        try:
            self.get(path)
            return True
        except RuntimeError:
            return False

    def key(self):
        'Returns the name of the current key.'
        return self.hive.node_name(self._cur)

    def tell(self):
        'Gives a path representation of the focus in the hive.'
        return '/' + '/'.join([self.hive.node_name(i) for i in self._nav][1:])

    def subkeys(self, path='.'):
        'Lists all subkeys of the current focused key or path.'
        return [self.hive.node_name(i) for i in self.hive.node_children(self.get(path)._cur)]

    def value(self, name, **kwargs):
        'Gets the value in a key-value pair in path. default can be used.'
        nav = self.get(kwargs['path']) if 'path' in kwargs else self
        v = None
        
        try:
            vn = nav.hive.node_get_value(nav._cur, name)
            t = nav.hive.value_type(vn)[0]

            if t == REG_SZ:
                v = nav.hive.value_string(vn)
            elif t == REG_MULTI_SZ:
                v = nav.hive.value_multiple_strings(vn)
            elif t == REG_DWORD:
                v = nav.hive.value_dword(vn)
            elif t == REG_QWORD:
                v = nav.hive.value_qword(vn)
            else:
                v = nav.hive.value_value(vn)[1]
                if t == REG_BINARY and isinstance(v, str):
                    v = v.encode()
                    
            if v is None:
                raise RuntimeError
            
        except RuntimeError:
            if 'default' in kwargs:
                return kwargs[default]
            else:
                raise KeyError('Value "%s" not found in key "%s"' % (name, nav.tell()))
            
        return v

    def values(self, path='.'):
        'Lists all values of this key or path.'
        return [self.hive.value_key(i) for i in self.hive.node_values(self.get(path)._cur)]

    def value_dict(self, path='.'):
        'Provides a dictionary of the key-value pairs in this registry key.'
        l = path
        return {k:self.value(k, path=l) for k in self.values(l)}

    def value_exists(self, name, path='.'):
        'Returns True if the value name exists in key path.'
        l = path
        nav = self.get(l) if l != '.' else self
        
        try:
            vn = nav.hive.node_get_value(nav._cur, name)
            return True
        except RuntimeError:
            return False

    def value_type(self, name, path='.'):
        'Returns the type of the value in path'
        nav = self.get(path) if path != '.' else self
        
        try:
            vn = nav.hive.node_get_value(nav._cur, name)
            return int(nav.hive.value_type(vn)[0])
        
        except RuntimeError:
            raise KeyError('Value "%s" not found in key "%s"' % (name, nav.tell()))
        

    def walk(self, path='.'):
        'Recurses through path and returns (focus, keys, value_dict) similar to os.walk'
        keys = self.subkeys(path)
        vals = self.value_dict(path)
        yield (path, keys, vals)
        for key in keys:
            newpath = path
            if not (path.endswith('/') or path.endswith('\\')):
                newpath += '/'
            newpath += key
            for i in self.walk(newpath):
                yield i
        


# END OF LINE.
