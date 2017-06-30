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
from collections import defaultdict, namedtuple
import re


# **************************************************************************************************
# **************************************************************************************************
class RecordHeader:
    def __init__(self, length, typ, sub, recordMap=None):
        self.len = length
        self.typ = typ
        self.sub = sub
        cls = recordMap.get((self.typ, self.sub))
        self.name = 'Unknown' if not cls else cls.name
    
    # ==============================================================================================
    def __repr__(self):
        return "<STDF Header, NAME=%s REC_LEN=%d>" % (self.name, self.len)


# **************************************************************************************************
# **************************************************************************************************
class RecordType(object):
    name, typ, sub, fieldMap, sizeMap = '', None, None, (), {}
    arrayMatch = re.compile('k(\d+)([A-Z][a-z0-9]+)')
    Field = namedtuple('Field', 'name format missing index value arrayFmt arrayNdx arrayCnt itemNdx itemSiz')
    
    # ==============================================================================================
    def __init__(self, header=None, parser=None, **kwargs):
        self.parser = parser
        self.header = header
        self.length = 0
        self.buffer = ''
        self.values = list()
        if header and parser:
            self.offset = parser.inp.tell()
            self.buffer = parser.inp.read(header.len)
            if self.buffer is None or len(self.buffer) != header.len:
                raise EofException()
        self.original = defaultdict(str)
        self.setFieldMap(**kwargs)
    
    # ==============================================================================================
    def setFieldMap(self, fieldMap=None, **kwargs):
        if fieldMap:
            self.fieldMap = fieldMap
        self.values = list()
        for ndx, fld in enumerate(self.fieldMap):
            setattr(self, fld[0], ndx)
            self.values.append(kwargs.get(fld[0]))
    
    # ==============================================================================================
    def update(self, **kwargs):
        for name, value in kwargs:
            self.values[getattr(self, name)] = value
    
    # ==============================================================================================
    def valuesMap(self):
        vd = dict()
        for ndx, fld in enumerate(self.fieldMap):
            vd[fld[0]] = self.values[ndx]
        return vd
    
    # ==============================================================================================
    def __str__(self):
        s = "%s " % self.name
        s += str([fld[:2] for fld in self.fieldMap])
        return s
    
    # ==============================================================================================
    def __repr__(self):
        s = "%s: (%02d, %02d)" % (self.name, self.typ, self.sub)
        for field in self.fields():
            s += "\n    %s" % repr(field)
        return s
    
    # ==============================================================================================
    def checkReadLength(self, size):
        if self.length + size > self.header.len:
            raise EndOfRecordException()
        return size
    
    # ==============================================================================================
    def verify(self, name, fmt, data):
        offset = 4 if fmt == 'Dn' else 0  # use slice to skip the bit count since we round on the way out
        if data[offset:] != self.original[name][offset:]:
            msg = '\nField %s (%s)\n    original : %s\n    processed: %s\n\n' % (
            name, fmt, hexlify(self.original[name]), hexlify(data))
            raise MismatchException(msg + repr(self))
    
    # ==============================================================================================
    def bufferFromOffset(self, name, size):
        buf = self.buffer[self.length:self.length + size]
        if not buf or len(buf) != size:
            raise EndOfRecordException()
        self.original[name] += buf  # hold onto the original packed data for verification
        self.length += size
        return buf
    
    # ==============================================================================================
    def field(self, nameOrIndex):
        arrayFmt, arrayNdx, arrayCnt, itemNdx, itemSiz = None, None, None, None, None
        ndx = getattr(self, nameOrIndex) if hasattr(nameOrIndex, 'upper') else nameOrIndex
        name, fmt, missing = self.fieldMap[ndx][:3]
        if fmt[0] == 'k':
            arrayNdx, arrayFmt = self.arrayMatch.match(fmt).groups()
            arrayNdx = int(arrayNdx)
            arrayCnt = self.values[arrayNdx]
        if name in self.sizeMap:
            itemNdx = self.sizeMap[name]
            itemSiz = self.values[getattr(self, itemNdx)]
        return RecordType.Field(name=name,
                                format=fmt,
                                missing=missing,
                                index=ndx,
                                value=self.values[ndx],
                                arrayFmt=arrayFmt,
                                arrayNdx=arrayNdx,
                                arrayCnt=arrayCnt,
                                itemNdx=itemNdx,
                                itemSiz=itemSiz)
    
    # ==============================================================================================
    def fields(self):
        for ndx, fld in enumerate(self.fieldMap):
            yield self.field(ndx)
        raise StopIteration


# **************************************************************************************************
# **************************************************************************************************
class UnknownRecord(RecordType):
    def __init__(self, typ, sub):
        super(UnknownRecord, self).__init__()
        self.typ = typ
        self.sub = sub
        self.name = 'UnknownRecord'


# **************************************************************************************************
# **************************************************************************************************
class EofException(Exception): pass


class EndOfRecordException(Exception): pass


class InitialSequenceException(Exception): pass


class MismatchException(Exception): pass
