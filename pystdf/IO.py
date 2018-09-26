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

from struct import calcsize, unpack_from, unpack, Struct, pack, error
import Types

_endian = '@'
_unpackHeader = Struct('@HBB').unpack
_packHeader = Struct('@HBB').pack

_stdf2struct = {
    "C1": "c",
    "B1": "B",
    "U1": "B",
    "U2": "H",
    "U4": "I",
    "U8": "Q",
    "I1": "b",
    "I2": "h",
    "I4": "i",
    "I8": "q",
    "R4": "f",
    "R8": "d",
}

stdf2unpack = {  # STDF format identifier to struct format identifier - updated with detectEndian
    "C1": (Struct("@c").unpack_from, calcsize("c")),
    "B1": (Struct("@B").unpack_from, calcsize("B")),
    "U1": (Struct("@B").unpack_from, calcsize("B")),
    "U2": (Struct("@H").unpack_from, calcsize("H")),
    "U4": (Struct("@I").unpack_from, calcsize("I")),
    "U8": (Struct("@Q").unpack_from, calcsize("Q")),
    "I1": (Struct("@b").unpack_from, calcsize("b")),
    "I2": (Struct("@h").unpack_from, calcsize("h")),
    "I4": (Struct("@i").unpack_from, calcsize("i")),
    "I8": (Struct("@q").unpack_from, calcsize("q")),
    "R4": (Struct("@f").unpack_from, calcsize("f")),
    "R8": (Struct("@d").unpack_from, calcsize("d")),
}

stdf2pack = {  # STDF format identifier to struct format identifier - updated with detectEndian
    "C1": (Struct("@c").pack, calcsize("c")),
    "B1": (Struct("@B").pack, calcsize("B")),
    "U1": (Struct("@B").pack, calcsize("B")),
    "U2": (Struct("@H").pack, calcsize("H")),
    "U4": (Struct("@I").pack, calcsize("I")),
    "U8": (Struct("@Q").pack, calcsize("Q")),
    "I1": (Struct("@b").pack, calcsize("b")),
    "I2": (Struct("@h").pack, calcsize("h")),
    "I4": (Struct("@i").pack, calcsize("i")),
    "I8": (Struct("@q").pack, calcsize("q")),
    "R4": (Struct("@f").pack, calcsize("f")),
    "R8": (Struct("@d").pack, calcsize("d")),
}

#**********************************************************************************************
def detectEndian(inp):
    location = inp.tell()
    inp.seek(0)
    global _endian, _unpackHeader, _packHeader
    _endian = '@'
    length, typ, sub, cpuType = unpack('@HBBB', inp.read(5))
    if typ != 0 and sub != 10:
        raise Types.InitialSequenceException()
    inp.seek(location)
    _endian = '<' if cpuType == 2 else '>'
    _unpackHeader = Struct('%sHBB' % _endian).unpack
    _packHeader = Struct('%sHBB' % _endian).pack
    for k, v in _stdf2struct.items():
        fmt = '%s%s' % (_endian, v)
        stdf2unpack[k] = (Struct(fmt).unpack_from, calcsize(v))
        stdf2pack[k] = (Struct(fmt).pack, calcsize(v))

#**********************************************************************************************
def readFieldDirect(endian, inp, stdfFmt):
    fmt = _stdf2struct[stdfFmt]
    buf = inp.read(calcsize(fmt))
    if not buf:
        raise Types.EofException()
    val, = unpack(endian + fmt, buf)
    return val

#**********************************************************************************************
def readHeader(inp, recordMap):
    try:
        buf = inp.read(4)
        length, typ, sub = _unpackHeader(buf)
        return Types.RecordHeader(length, typ, sub, recordMap)
    except Exception:
        raise Types.EofException()
    
#**********************************************************************************************
def readField(*args):
    buf, offset, stdfFmt = args[:3]
    sup, size = stdf2unpack[stdfFmt]
    val, = sup(buf, offset)
    return offset, val, offset + size

#**********************************************************************************************
def readCf(*args):
    """
    Variable length character string:
    string length is stored in another field
    """
    buf, offset, size = args[:3]
    if not size:
        return offset, '', offset + 1
    val, = unpack_from('%s%ds' % (_endian, size), buf, offset)
    return offset, val, offset + size

#**********************************************************************************************
def readCn(*args):
    """
    Variable length character string:
    first byte = unsigned count of bytes to follow (maximum of 255 bytes)
    """
    buf, offset = args[:2]
    size, = unpack_from('B', buf, offset)
    if not size:
        return offset, '', offset + 1
    val, = unpack_from('%s%ds' % (_endian, size), buf, offset+1)
    return offset, val, offset + 1 + size

#**********************************************************************************************
def readSn(*args):
    """
    Variable length character string:
    first two bytes = unsigned count of bytes to follow (maximum of 65535 bytes)
    """
    buf, offset = args[:2]
    size, = unpack_from('H', buf, offset)
    if not size:
        return offset, '', offset + 2
    val, = unpack_from('%s%ds' % (_endian, size), buf, offset+2)
    return offset, val, offset + 2 + size

#**********************************************************************************************
def readBn(*args):
    """
    Variable length bit-encoded field:
    First byte = unsigned count of bytes to follow (maximum of 255 bytes).
    First data item in least significant bit of the second byte of the array (first byte is count.)
    """
    buf, offset = args[:2]
    size, = unpack_from('B', buf, offset)
    bn = unpack_from('%s%s' % (_endian, 'B' * size), buf, offset+1)
    return offset, bn, offset + 1 + size

#**********************************************************************************************
def readDn(*args):
    """
    Variable length bit-encoded field:
    First two bytes = unsigned count of bits to follow (maximum of 65,535 bits).
    First data item in least significant bit of the third byte of the array (first two bytes are count).
    Unused bits at the high order end of the last byte must be zero.
    """
    buf, offset = args[:2]
    bits, = unpack_from('H', buf, offset)
    size = bits / 8
    if bits % 8 > 0:
        size += 1
    dn = unpack_from('%s%s' % (_endian, 'B' * size), buf, offset+2)
    return offset, dn, offset + 2 + size

#**********************************************************************************************
vnReadMap = {
     #0: ('B0', lambda *args: (args[1], record.parser.inp.read(1), args[1]+1)),
     1: ('U1', readField),
     2: ('U2', readField),
     3: ('U4', readField),
     4: ('I1', readField),
     5: ('I2', readField),
     6: ('I4', readField),
     7: ('R4', readField),
     8: ('R8', readField),
    10: ('Cn', readCn),
    11: ('Bn', readBn),
    12: ('Dn', readDn),
    13: ('N1', lambda *args: readField(args[0], args[1], 'U1'))
}

GEN_DATA_ = 'GEN_DATA_'

def readVn(record, verify):
    offset, buf = 0, record.buffer
    if verify:
        record.original['FLD_CNT'] = (offset, 2)
    _, vln, offset = readField(buf, offset, 'U2')      # extracts the data field count FLD_CNT
    fm = [None] * (vln+1)
    fm[0] =('FLD_CNT', 'U2', None)
    vn = [vln] * (vln+1)
    b0Pad = ('B0', lambda *args: (args[1], record.parser.inp.read(1), args[1]+1))
    for i in range(vln):
        rln, fldType, offset = readField(buf, offset, 'B1')
        fmt, fieldReader = vnReadMap.get(fldType, b0Pad)
        _, genData, offset = fieldReader(buf, offset, fmt)
        if fmt == 'B0':
            continue
        vName = '%s_%d' % (GEN_DATA_, i)
        if verify:
            record.original[vName] = (rln, offset-rln)
        fm[i+1] = (vName, fmt, None)
        vn[i+1] = genData
    record.setFieldMap(fm)            # replace the field map dynamically
    record.values = vn

#**********************************************************************************************
unpackMap = {
    "C1": readField,
    "B1": readField,
    "U1": readField,
    "U2": readField,
    "U4": readField,
    "U8": readField,
    "I1": readField,
    "I2": readField,
    "I4": readField,
    "I8": readField,
    "R4": readField,
    "R8": readField,
    "N1": readField,
    "Cf": readCf,
    "Cn": readCn,
    "Sn": readSn,
    "Bn": readBn,
    "Dn": readDn,
}

# **********************************************************************************************
def readArray(buf, offset, arrayCnt, arrayFmt, itemNdx, itemSize):
    """
    """
    rln = offset
    if itemNdx is None:
        fieldReader = unpackMap[arrayFmt]
    else:
        arrayFmt = 'U%d' % itemSize if arrayFmt[0] == 'U' else itemSize  # Uf -> U1 | U2 | U4 | U8
        fieldReader = unpackMap.get(arrayFmt, readCf)  # Cf is passed itemSize in last parameter
    arr = [None] * arrayCnt
    for i in range(arrayCnt):
        _, arr[i], offset = fieldReader(buf, offset, arrayFmt)
    return rln, arr, offset

# **********************************************************************************************
def readNibbleArray(buf, offset, arrayCnt, arrayFmt):
    """
    """
    rln = offset
    numReads = arrayCnt / 2 + arrayCnt % 2
    arr = []
    fieldReader = unpackMap[arrayFmt]
    for i in range(numReads):
        _, val, offset = fieldReader(buf, offset, 'U1')
        arr.append(val & 0xF)
        if len(arr) < arrayCnt:
            arr.append(val >> 4)
    return rln, arr, offset

#**********************************************************************************************
def decodeValues(record, verify=False):
    try:
        oft, mxLen, buf, vals, orig = 0, len(record.buffer), record.buffer, record.values, record.original
        for name, fmt, missing, index, arrayFmt, arrayNdx, itemNdx in record.fields():
            if oft >= mxLen:
                vals[index] = missing
                continue
            if fmt == 'Vn':
                readVn(record, verify)
                continue
            rln = oft
            if arrayFmt:
                if arrayFmt == 'N1':
                    _, vals[index], oft = readNibbleArray(buf, oft, vals[arrayNdx], arrayFmt)
                else:
                    _, vals[index], oft = readArray(buf, oft, vals[arrayNdx], arrayFmt, itemNdx, vals[itemNdx or 0])
            elif fmt == 'Cn':
                size = stdf2unpack['U1'][0](buf, oft)[0]     # inline of readCn
                vals[index] = unpack_from('%s%ds' % (_endian, size), buf, oft+1)[0] if size else ''
                oft += (size + 1)
            elif fmt[-1] in 'nf':
                _, vals[index], oft = unpackMap[fmt](buf, oft, fmt)
            else:
                sup, size = stdf2unpack[fmt]        # inline of readField
                vals[index] = sup(buf, oft)[0]
                oft += size
            if verify:
                orig[name] = (rln, oft - rln)
    except Types.EndOfRecordException:
        pass
    except error, err:
        print err
        print record
    except:
        raise

#**********************************************************************************************
#**********************************************************************************************
#**********************************************************************************************
#**********************************************************************************************
def packRecord(record, encodedValues):
    packedValues = ''.join(encodedValues)
    return _packHeader(len(packedValues), record.typ, record.sub) + packedValues

#**********************************************************************************************
def packField(value, stdfFmt):
    try:
        return stdf2pack[stdfFmt][0](value)
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
def packCf(value, siz):
    """
    Variable length character string: count of bytes stored in another field
    """
    try:
        fmt = 'B%ds' % siz
        pad = '%%-%ds' % siz        # left-justify and pad with trailing spaces
        return pack(fmt, siz, pad % value[:siz])
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
def packCn(value):
    """
    Variable length character string:
    first byte = unsigned count of bytes to follow (maximum of 255 bytes)
    """
    try:
        siz = len(value)
        return pack('B%ds' % siz, siz, value)
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
def packSn(value):
    """
    Variable length character string:
    first two bytes = unsigned count of bytes to follow (maximum of 65535 bytes)
    """
    try:
        siz = len(value)
        return pack('H%ds' % siz, siz, value)
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
def packBn(value):
    """
    Variable length bit-encoded field:
    First byte = unsigned count of bytes to follow (maximum of 255 bytes).
    First data item in least significant bit of the second byte of the array (first byte is count.)
    """
    try:
        siz = len(value)
        return pack('B%dB' % siz, siz, *value)
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
def packDn(value):
    """
    Variable length bit-encoded field:
    First two bytes = unsigned count of bits to follow (maximum of 65,535 bits).
    First data item in least significant bit of the third byte of the array (first two bytes are count).
    Unused bits at the high order end of the last byte must be zero.
    """
    try:
        siz = len(value)
        return pack('H%dB' % siz, siz * 8, *value)       # the size is in bits, so 8x bytes
    except Exception, err:
        raise Types.EndOfRecordException('%s' % err)

#**********************************************************************************************
vnPackMap = {
    'B0': ( 1, lambda value: packField(value, 'U1')),
    'U1': ( 1, lambda value: packField(value, 'U1')),
    'U2': ( 2, lambda value: packField(value, 'U2')),
    'U4': ( 3, lambda value: packField(value, 'U4')),
    'I1': ( 4, lambda value: packField(value, 'I1')),
    'I2': ( 5, lambda value: packField(value, 'I2')),
    'I4': ( 6, lambda value: packField(value, 'I4')),
    'R4': ( 7, lambda value: packField(value, 'R4')),
    'R8': ( 8, lambda value: packField(value, 'R8')),
    'Cn': (10, lambda value: packCn(value)),
    'Bn': (11, lambda value: packBn(value)),
    'Dn': (12, lambda value: packDn(value)),
    'N1': (13, lambda value: packField(value, 'U1'))
}

# **********************************************************************************************
def packVn(value, stdfFmt):
    vnFmt, fieldPacker = vnPackMap[stdfFmt]
    genData = packField(vnFmt, 'B1')
    genData += fieldPacker(value)
    return genData

#**********************************************************************************************
packMap = {
    'C1': packField,
    'B1': packField,
    'U1': packField,
    'U2': packField,
    'U4': packField,
    'U8': packField,
    'I1': packField,
    'I2': packField,
    'I4': packField,
    'I8': packField,
    'R4': packField,
    'R8': packField,
    'N1': lambda value, fmt: packField(value, 'U1'),
    'Cf': packCf,
    'Cn': lambda value, fmt: packCn(value),
    'Sn': lambda value, fmt: packSn(value),
    'Bn': lambda value, fmt: packBn(value),
    'Dn': lambda value, fmt: packDn(value),
    'Vn': packVn,
}

# **********************************************************************************************
def packArray(record, index, arrayFmt, itemNdx):
    """
    """
    if itemNdx is None:
        fieldPacker = packMap[arrayFmt]
    else:
        itemSize = record.values[itemNdx]
        arrayFmt = 'U%d' % itemSize if arrayFmt[0] == 'U' else itemSize  # Uf -> U1 | U2 | U4 | U8
        fieldPacker = packMap.get(arrayFmt, packCf)  # Cf is passed itemSize in last parameter
    values = record.values[index]
    arr = [''] * len(values)
    for i, value in enumerate(values):
        arr[i] = fieldPacker(value, arrayFmt)
    return ''.join(arr), len(arr)

# **********************************************************************************************
def packNibbleArray(record, index, arrayFmt):
    """
    """
    values = record.values[index]
    numValues = len(values)
    arr = []
    fieldPacker = packMap[arrayFmt]
    for i in range(0, numValues, 2):
        val = values[i] & 0xF
        if i + 1 < numValues:
            val |= values[i + 1] << 4
        d = fieldPacker(val, arrayFmt)
        arr.append(d)
    return ''.join(arr), numValues

# **********************************************************************************************
def encodeMissingField(record, name, fmt, missing, index, arrayFmt, processedData):
    if missing is None:
        raise Types.EndOfRecordException('Required data missing from %s.%s' % (record.name, name))
    if isinstance(missing, tuple):
        flagField, mask = missing
        flagField = record.field(flagField)
        record.values[index] = [] if arrayFmt else defaultDataMap[fmt]
        record.values[flagField.index] |= (flagField.missing ^ mask)
        processedData[flagField.index] = val = packMap[flagField.format](record.values[flagField.index], flagField.format)
    else:
        record.values[index] = val = str(missing)
    return val

# **********************************************************************************************
def encodeArrayField(record, index, arrayFmt, arrayNdx, itemNdx, processedData):
    if arrayFmt == 'N1':
        val, newCount = packNibbleArray(record, index, arrayFmt)
    else:
        val, newCount = packArray(record, index, arrayFmt, itemNdx)
    arrayCnt = record.values[arrayNdx]
    if arrayCnt != newCount:
        record.values[arrayNdx] = newCount
        raField = record.field(arrayNdx)
        processedData[arrayNdx] = packMap[raField.format](newCount, raField.format)
    processedData[index] = val
    
#**********************************************************************************************
def encodeRecord(record):
    """
    Returns the original buffer if present and all values are None
    """
    if record.buffer and reduce(lambda x, y: x or y, record.values) is None:
        return record.buffer
    processedData = [None] * len(record.fieldMap)
    vals = record.values
    for name, fmt, missing, index, arrayFmt, arrayNdx, itemNdx in record.fields():
        try:
            val = vals[index]
            if val is None:
                processedData[index] = encodeMissingField(record, name, fmt, missing, index, arrayFmt, processedData)
                continue
            if arrayFmt:
                encodeArrayField(record, index, arrayFmt, arrayNdx, itemNdx, processedData)
                continue
            if name.startswith(GEN_DATA_):
                processedData[index] = packVn(val, fmt)
                continue
            if fmt == 'Cn':
                siz = len(val)
                processedData[index] = pack('B%ds' % siz, siz, val)
            elif fmt[-1] in 'nf':
                processedData[index] = packMap[fmt](val, fmt)
            else:
                processedData[index] = stdf2pack[fmt][0](val)
        except Exception, err:
            raise Types.EndOfRecordException('%s: %s-%s' % (err, name, index))
            
    return processedData

'''
The specification of each STDF record has a column labelled Missing/Invalid Data Flag.
An entry in this column means that the field is optional, and that the value shown is the way to flag the
field's data as missing or invalid. If the column does not have an entry, the field is required.
Each data type has a standard way of indicating missing or invalid data, as the following table shows:

   Data Type                           Missing/Invalid Data Flag
Variable-length string              Set the length byte to 0.
Fixed-length character string       Fill the field with spaces.
Fixed-length binary string          Set a flag bit in an Optional Data byte.
Time and date fields                Use a binary 0.
Integers and floating point values  Use the indicated reserved value or set a flag bit in an Optional Data byte.
'''

#**********************************************************************************************
defaultDataMap = {
    'C1': ' ',
    'B1': 0xff,
    'U1': 0xff,
    'U2': 0xffff,
    'U4': 0xffffffff,
    'U8': 0xffffffffffffffff,
    'I1': -128,
    'I2': -32768,
    'I4': -2147483648,
    'I8': -9223372036854775808,
    'R4': -1e300,
    'R8': -1e300,
    'N1': 0xf,
    'Cn': '',
    'Sn': '',
    'Bn': [],
    'Dn': [],
}

#**********************************************************************************************
def missingFlag(record, index, missing):
    """
    Returns true if data matches default value or if optional bit is set
    Assumes the flagField.missing value is all 1s
    """
    if isinstance(missing, tuple):
        flagField, mask = missing
        flagField = record.field(flagField)
        return record.values[flagField.index] | mask == flagField.missing
    return record.values[index] == missing
    
