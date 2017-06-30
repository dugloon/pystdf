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

import struct
import Types

stdf2struct = {  # STDF format identifier to struct format identifier
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
    "R8": "d"
}


# **********************************************************************************************
def readFieldDirect(endian, inp, stdfFmt):
    fmt = stdf2struct[stdfFmt]
    buf = inp.read(struct.calcsize(fmt))
    if not buf:
        raise Types.EofException()
    val, = struct.unpack(endian + fmt, buf)
    return val


# **********************************************************************************************
def readHeader(endian, inp, recordMap):
    l = readFieldDirect(endian, inp, 'U2')
    t = readFieldDirect(endian, inp, 'U1')
    s = readFieldDirect(endian, inp, 'U1')
    return Types.RecordHeader(l, t, s, recordMap)


# **********************************************************************************************
def detectEndian(inp):
    location = inp.tell()
    inp.seek(0)
    endian = '@'
    readFieldDirect(endian, inp, 'U2')
    typ = readFieldDirect(endian, inp, 'U1')
    sub = readFieldDirect(endian, inp, 'U1')
    if typ != 0 and sub != 10:
        raise Types.InitialSequenceException()
    cpuType = readFieldDirect(endian, inp, 'U1')
    inp.seek(location)
    return '<' if cpuType == 2 else '>'


# **********************************************************************************************
def readField(record, name, stdfFmt):
    fmt = stdf2struct[stdfFmt]
    size = record.checkReadLength(struct.calcsize(fmt))
    buf = record.bufferFromOffset(name, size)
    val, = struct.unpack(record.parser.endian + fmt, buf)
    return val


# **********************************************************************************************
def readCf(record, name, siz):
    """
    Variable length character string:
    string length is stored in another field
    """
    sln = record.checkReadLength(siz)
    if sln == 0:
        return ''
    buf = record.bufferFromOffset(name, sln)
    fmt = '%s%ds' % (record.parser.endian, sln)
    val, = struct.unpack(fmt, buf)
    return val


# **********************************************************************************************
def readCn(record, name):
    """
    Variable length character string:
    first byte = unsigned count of bytes to follow (maximum of 255 bytes)
    """
    byteCount = readField(record, name, 'U1')
    sln = record.checkReadLength(byteCount)
    if sln == 0:
        return ''
    buf = record.bufferFromOffset(name, sln)
    fmt = '%s%ds' % (record.parser.endian, sln)
    val, = struct.unpack(fmt, buf)
    return val


# **********************************************************************************************
def readSn(record, name):
    """
    Variable length character string:
    first two bytes = unsigned count of bytes to follow (maximum of 65535 bytes)
    """
    byteCount = readField(record, name, 'U2')
    sln = record.checkReadLength(byteCount)
    if sln == 0:
        return ''
    buf = record.bufferFromOffset(name, sln)
    fmt = '%s%ds' % (record.parser.endian, sln)
    val, = struct.unpack(fmt, buf)
    return val


# **********************************************************************************************
def readBn(record, name):
    """
    Variable length bit-encoded field:
    First byte = unsigned count of bytes to follow (maximum of 255 bytes).
    First data item in least significant bit of the second byte of the array (first byte is count.)
    """
    bln = readField(record, name, 'U1')
    bn = []
    for i in range(bln):
        bn.append(readField(record, name, 'B1'))
    return bn


# **********************************************************************************************
def readDn(record, name):
    """
    Variable length bit-encoded field:
    First two bytes = unsigned count of bits to follow (maximum of 65,535 bits).
    First data item in least significant bit of the third byte of the array (first two bytes are count).
    Unused bits at the high order end of the last byte must be zero.
    """
    dBitLen = readField(record, name, 'U2')
    dByteLen = dBitLen / 8
    if dBitLen % 8 > 0:
        dByteLen += 1
    dn = []
    for i in range(dByteLen):
        dn.append(readField(record, name, 'B1'))
    return dn


# **********************************************************************************************
vnReadMap = {
    0: ('B0', lambda record, name: record.parser.inp.read(1)),
    1: ('U1', lambda record, name: readField(record, name, 'U1')),
    2: ('U2', lambda record, name: readField(record, name, 'U2')),
    3: ('U4', lambda record, name: readField(record, name, 'U4')),
    4: ('I1', lambda record, name: readField(record, name, 'I1')),
    5: ('I2', lambda record, name: readField(record, name, 'I2')),
    6: ('I4', lambda record, name: readField(record, name, 'I4')),
    7: ('R4', lambda record, name: readField(record, name, 'R4')),
    8: ('R8', lambda record, name: readField(record, name, 'R8')),
    10: ('Cn', lambda record, name: readCn(record, name)),
    11: ('Bn', lambda record, name: readBn(record, name)),
    12: ('Dn', lambda record, name: readDn(record, name)),
    13: ('N1', lambda record, name: readField(record, name, 'U1'))
}

GEN_DATA_ = 'GEN_DATA_'


def readVn(record):
    vln = readField(record, 'FLD_CNT', 'U2')  # extracts the data field count FLD_CNT
    fm, vn = [('FLD_CNT', 'U2', None)], {'FLD_CNT': vln}
    for i in range(vln):
        vName = '%s_%d' % (GEN_DATA_, i)
        fldType = readField(record, vName, 'B1')
        fmt, fieldReader = vnReadMap[fldType]
        genData = fieldReader(record, vName)
        fm.append((vName, fmt, None))
        vn[vName] = genData
    record.setFieldMap(fm, **vn)  # replace the field map dynamically


# **********************************************************************************************
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
    "N1": lambda record, name, fmt: readField(record, name, 'U1'),
    "Cf": lambda record, name, siz: readCf(record, name, siz),
    "Cn": lambda record, name, fmt: readCn(record, name),
    "Sn": lambda record, name, fmt: readSn(record, name),
    "Bn": lambda record, name, fmt: readBn(record, name),
    "Dn": lambda record, name, fmt: readDn(record, name),
}


def readArray(record, field):
    """
    """
    arr, fmt = [], field.arrayFmt
    if field.itemNdx is None:
        fieldReader = unpackMap[fmt]
    else:
        fmt = 'U%d' % field.itemSiz if fmt[0] == 'U' else field.itemSiz  # Uf -> U1 | U2 | U4 | U8
        fieldReader = unpackMap.get(fmt, unpackMap['Cf'])  # Cf is passed the size in third parameter
    for i in range(field.arrayCnt):
        arr.append(fieldReader(record, field.name, fmt))
    return arr


def readNibbleArray(record, field):
    """
    """
    numReads = field.arrayCnt / 2 + field.arrayCnt % 2
    arr = []
    fieldReader = unpackMap[field.arrayFmt]
    for i in range(numReads):
        val = fieldReader(record, field.name, field.arrayFmt)
        arr.append(val & 0xF)
        if len(arr) < field.arrayCnt:
            arr.append(val >> 4)
    return arr


# **********************************************************************************************
def decodeValues(record):
    try:
        for field in record.fields():
            if field.arrayFmt:
                if field.arrayFmt == 'N1':
                    record.values[field.index] = readNibbleArray(record, field)
                else:
                    record.values[field.index] = readArray(record, field)
            elif field.format == 'Vn':
                readVn(record)
            else:
                fieldReader = unpackMap[field.format]
                record.values[field.index] = fieldReader(record, field.name, field.format)
    except Types.EndOfRecordException:
        pass


# **********************************************************************************************
# **********************************************************************************************
# **********************************************************************************************
# **********************************************************************************************
def checkWriteLength(fmtSize, buf):
    bufSize = len(buf)
    if fmtSize != bufSize:
        raise Types.EndOfRecordException('buf size (%d) != format size (%d)' % (bufSize, fmtSize))


# **********************************************************************************************
def packRecord(endian, record, encodedValues):
    packedValues = ''.join(encodedValues)
    fmt = '%sHBB' % endian
    buf = struct.pack(fmt, len(packedValues), record.typ, record.sub)
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf + packedValues


# **********************************************************************************************
def packField(endian, value, stdfFmt):
    fmt = '%s%s' % (endian, stdf2struct[stdfFmt])
    buf = struct.pack(fmt, value)
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
def packCf(endian, value, siz):
    """
    Variable length character string: count of bytes stored in another field
    """
    fmt = stdf2struct['U1']
    fmt = '%s%s%ds' % (endian, fmt, siz)
    pad = '%%-%ds' % siz  # left-justify and pad with trailing spaces
    buf = struct.pack(fmt, siz, pad % value[:siz])
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
def packCn(endian, value):
    """
    Variable length character string:
    first byte = unsigned count of bytes to follow (maximum of 255 bytes)
    """
    fmt = stdf2struct['U1']
    siz = len(value)
    fmt = '%s%s%ds' % (endian, fmt, siz)
    buf = struct.pack(fmt, siz, value)
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
def packSn(endian, value):
    """
    Variable length character string:
    first two bytes = unsigned count of bytes to follow (maximum of 65535 bytes)
    """
    fmt = stdf2struct['U2']
    siz = len(value)
    fmt = '%s%s%ds' % (endian, fmt, siz)
    buf = struct.pack(fmt, siz, value)
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
def packBn(endian, value):
    """
    Variable length bit-encoded field:
    First byte = unsigned count of bytes to follow (maximum of 255 bytes).
    First data item in least significant bit of the second byte of the array (first byte is count.)
    """
    fmt = stdf2struct['U1']
    siz = len(value)
    fmt = '%s%s%dB' % (endian, fmt, siz)
    buf = struct.pack(fmt, siz, *value)
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
def packDn(endian, value):
    """
    Variable length bit-encoded field:
    First two bytes = unsigned count of bits to follow (maximum of 65,535 bits).
    First data item in least significant bit of the third byte of the array (first two bytes are count).
    Unused bits at the high order end of the last byte must be zero.
    """
    fmt = stdf2struct['U2']
    siz = len(value)
    fmt = '%s%s%dB' % (endian, fmt, siz)
    buf = struct.pack(fmt, siz * 8, *value)  # the size is in bits, so 8x bytes
    checkWriteLength(struct.calcsize(fmt), buf)
    return buf


# **********************************************************************************************
vnPackMap = {
    'B0': (1, lambda endian, value: packField(endian, value, 'U1')),
    'U1': (1, lambda endian, value: packField(endian, value, 'U1')),
    'U2': (2, lambda endian, value: packField(endian, value, 'U2')),
    'U4': (3, lambda endian, value: packField(endian, value, 'U4')),
    'I1': (4, lambda endian, value: packField(endian, value, 'I1')),
    'I2': (5, lambda endian, value: packField(endian, value, 'I2')),
    'I4': (6, lambda endian, value: packField(endian, value, 'I4')),
    'R4': (7, lambda endian, value: packField(endian, value, 'R4')),
    'R8': (8, lambda endian, value: packField(endian, value, 'R8')),
    'Cn': (10, lambda endian, value: packCn(endian, value)),
    'Bn': (11, lambda endian, value: packBn(endian, value)),
    'Dn': (12, lambda endian, value: packDn(endian, value)),
    'N1': (13, lambda endian, value: packField(endian, value, 'U1'))
}


def packVn(endian, value, stdfFmt):
    vnFmt, fieldPacker = vnPackMap[stdfFmt]
    genData = packField(endian, vnFmt, 'B1')
    genData += fieldPacker(endian, value)
    return genData


# **********************************************************************************************
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
    'N1': lambda endian, value, fmt: packField(endian, value, 'U1'),
    'Cf': lambda endian, value, siz: packCf(endian, value, siz),
    'Cn': lambda endian, value, fmt: packCn(endian, value),
    'Sn': lambda endian, value, fmt: packSn(endian, value),
    'Bn': lambda endian, value, fmt: packBn(endian, value),
    'Dn': lambda endian, value, fmt: packDn(endian, value),
    # 'Vn': packVn,
}


def packArray(endian, field):
    """
    """
    arr, fmt = [], field.arrayFmt
    if field.itemNdx is None:
        fieldPacker = packMap[field.arrayFmt]
    else:
        fmt = 'U%d' % field.itemSiz if fmt[0] == 'U' else field.itemSiz  # Uf -> U1 | U2 | U4 | U8
        fieldPacker = packMap.get(fmt, packMap['Cf'])  # Cf is passed the size in third parameter
    for i, value in enumerate(field.value):
        d = fieldPacker(endian, value, field.arrayFmt)
        arr.append(d)
    return ''.join(arr), len(arr)


def packNibbleArray(endian, field):
    """
    """
    numValues = len(field.value)
    arr = []
    fieldPacker = packMap[field.arrayFmt]
    for i in range(0, numValues, 2):
        val = field.value[i] & 0xF
        if i + 1 < numValues:
            val |= field.value[i + 1] << 4
        d = fieldPacker(endian, val, field.arrayFmt)
        arr.append(d)
    return ''.join(arr), numValues


# **********************************************************************************************
def encodeMissingField(endian, record, field, processedData):
    if field.missing is None:
        raise Types.EndOfRecordException('Required data missing from %s.%s' % (record.name, field.name))
    if isinstance(field.missing, tuple):
        flagField, mask = field.missing
        flagField = record.field(flagField)
        record.values[field.index] = [] if field.arrayFmt else defaultDataMap[field.format]
        record.values[flagField.index] |= (flagField.missing ^ mask)
        processedData[flagField.index] = packMap[flagField.format](endian, record.values[flagField.index],
                                                                   flagField.format)
    else:
        record.values[field.index] = field.missing


# **********************************************************************************************
def encodeArrayField(endian, record, field, processedData):
    if field.arrayFmt == 'N1':
        val, newCount = packNibbleArray(endian, field)
    else:
        val, newCount = packArray(endian, field)
    if field.arrayCnt != newCount:
        record.values[field.arrayNdx] = newCount
        raField = record.field(field.arrayNdx)
        processedData[field.arrayNdx] = packMap[raField.format](endian, newCount, raField.format)
    processedData += [val]


# **********************************************************************************************
def encodeRecord(endian, record):
    """
    Returns the original buffer if present and all values are None
    """
    if record.buffer and reduce(lambda x, y: x or y, record.values) is None:
        return record.buffer
    processedData = list()
    for field in record.fields():
        if field.value is None:
            encodeMissingField(endian, record, field, processedData)
        if field.arrayFmt:
            encodeArrayField(endian, record, field, processedData)
        else:
            fieldPacker = packVn if field.name.startswith(GEN_DATA_) else packMap[field.format]
            val = fieldPacker(endian, field.value, field.format)
            processedData += [val]
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

# **********************************************************************************************
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


# **********************************************************************************************
def missingFlag(record, field):
    """
    Returns true if data matches default value or if optional bit is set
    Assumes the flagField.missing value is all 1s
    """
    if isinstance(field.missing, tuple):
        flagField, mask = field.missing
        flagField = record.field(flagField)
        return flagField.value | mask == flagField.missing
    return field.value == field.missing

