#
# PySTDF - The Pythonic STDF Parser
# Copyright (C) 2006 Casey Marshall
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from binascii import hexlify
from collections import namedtuple
import re

#**************************************************************************************************
#**************************************************************************************************
class RecordHeader(object):
    __slots__ = ['len', 'typ', 'sub', 'name']
    def __init__(self, length, typ, sub, recordMap=None):
        self.len = length
        self.typ = typ
        self.sub = sub
        cls = recordMap.get((self.typ, self.sub))
        self.name = 'Unknown' if not cls else cls.name

    #==============================================================================================
    def __repr__(self):
        return "<STDF Header, NAME=%s REC_LEN=%d>" % (self.name, self.len)

#**************************************************************************************************
#**************************************************************************************************
class RecordType(object):
    name, typ, sub, fieldMap, sizeMap, _fields = '', None, None, (), {}, []
    arrayMatch = re.compile('k(\d+)([A-Z][a-z0-9]+)')
    Field = namedtuple('Field', 'name format missing index arrayFmt arrayNdx itemNdx')
    __slots__ = ['parser', 'header', 'buffer', 'original', 'values']
    #==============================================================================================
    def __init__(self, header=None, parser=None, **kwargs):
        self.parser = parser
        self.header = header
        self.buffer = ''
        if header and parser:
            self.buffer = parser.inp.read(header.len)
            if self.buffer is None or len(self.buffer) != header.len:
                raise EofException()
        self.original = dict()
        self.values = [None] * len(self.fieldMap)
        if kwargs:
            self.setValues(**kwargs)
    
    #==============================================================================================
    def setFieldMap(self, fieldMap):
        """
        Used to dynamically update a field map spec for Generic Data Records (they can be anything)
        """
        self.fieldMap = fieldMap
        self.values = [None] * len(fieldMap)
        self._fields = [None] * len(fieldMap)
        for ndx, fld in enumerate(self.fieldMap):
            setattr(self, fld[0], ndx)
            arrayFmt, arrayNdx, itemNdx  = None, None, None
            name, fmt, missing = fld[:3]
            if fmt[0] == 'k':
                arrayNdx, arrayFmt = RecordType.arrayMatch.match(fmt).groups()
                arrayNdx = int(arrayNdx)
            if name in RecordType.sizeMap:
                itemNdx = RecordType.sizeMap[name]
            self._fields[ndx] = RecordType.Field(name=name,
                                    format=fmt,
                                    missing=missing,
                                    index=ndx,
                                    arrayFmt=arrayFmt,
                                    arrayNdx=arrayNdx,
                                    itemNdx=itemNdx)
    
    #==============================================================================================
    def setValues(self, **kwargs):
        """
        """
        for fld, val in kwargs.items():
            ndx = getattr(self, fld)
            self.values[ndx] = val

    #==============================================================================================
    def update(self, **kwargs):
        for name, value in kwargs:
            self.values[getattr(self, name)] = value

    #==============================================================================================
    def valuesMap(self):
        vd = dict()
        for ndx, fld in enumerate(self.fieldMap):
            vd[fld[0]] = self.values[ndx]
        return vd

    #==============================================================================================
    def __str__(self):
        s = "%s " % self.name
        s += str([fld[:2] for fld in self.fieldMap])
        return s

    #==============================================================================================
    def __repr__(self):
        s = "%s: (%02d, %02d)" % (self.name, self.typ, self.sub)
        for field in self.fields():
            s += "\n    %s" % repr(field)
        return s

    #==============================================================================================
    def verify(self, name, fmt, data):
        offset = 2 if fmt == 'Dn' else 0  # use slice to skip the bit count since we round on the way out
        bufset, size = self.original[name]
        original = self.buffer[bufset+offset:bufset+size]
        processed = data[offset:]
        if original != processed:
            msg = '\nField %s (%s)\n    original : %s\n    processed: %s\n\n' % (name, fmt, hexlify(original), hexlify(processed))
            raise MismatchException(msg+repr(self))

    #==============================================================================================
    def field(self, nameOrIndex):
        try:
            return self._fields[nameOrIndex]
        except:
            nameOrIndex = getattr(self, nameOrIndex)
            return self._fields[nameOrIndex]
    
    #==============================================================================================
    def fields(self):
        return self._fields

#**************************************************************************************************
#**************************************************************************************************
class UnknownRecord(RecordType):
    def __init__(self, typ, sub):
        super(UnknownRecord, self).__init__()
        self.typ = typ
        self.sub = sub
        self.name = 'UnknownRecord'

#**************************************************************************************************
#**************************************************************************************************
class EofException(Exception): pass

class EndOfRecordException(Exception): pass

class InitialSequenceException(Exception): pass

class MismatchException(Exception): pass
