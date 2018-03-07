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

_author = 'dugloon'

import sys
from time import time, strftime, localtime
import Parse
import IO
import V4

#*******************************************************************************************************************
class AtdfWriter(object):
    @staticmethod
    def format_by_type(value, field_type):
        if field_type in ('B1', 'N1'):
            return '%02X' % value
        return str(value)

    @staticmethod
    def format(record, field):
        value = record.values[field.index]
        if value is None:
            return ''
        if field.arrayFmt: # An Array of some other type
            return ','.join([AtdfWriter.format_by_type(v, field.arrayFmt) for v in value])
        if record.name in ('Mir', 'Mrr'):
            if field.name.endswith('_T'): # A Date-Time in an MIR/MRR
                return strftime('%H:%M:%S %d-%b-%Y', localtime(value))
            return str(value)
        return str(value)

    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def after_send(self, _, record):
        processedData = []
        for field in record.fields():
            processedData.append(self.format(record, field))
        processedData = '|'.join(processedData)
        line = '%s:%s\n' % (record.name, processedData)
        self.stream.write(line)

    def after_complete(self, _):
        self.stream.flush()

#*******************************************************************************************************************
class StdfWriter(object):
    """
    """
    # =============================================================================================
    def __init__(self, stream=sys.stdout):
        self.stream = stream

    # =============================================================================================
    def writeRecord(self, record):
        encodedValues = IO.encodeRecord(record)
        packedRecord = IO.packRecord(record, encodedValues)
        self.stream.write(packedRecord)

    # =============================================================================================
    def after_send(self, dataSource, record):
        self.writeRecord(record)

    # =============================================================================================
    def after_complete(self, _):
        self.stream.flush()

#*******************************************************************************************************************
class StdfModifier(StdfWriter):
    """
    """
    # =============================================================================================
    def after_send(self, dataSource, record):
        """
        Adding the version 2007 marker and an Audit Trail Record
        """
        if record.name == 'Mir':
            self.writeRecord(V4.Atr(MOD_TIM=time(), CMD_LINE='pack'))
            self.writeRecord(V4.Vur(UPD_CNT=1, UPD_NAM=['Scan:2007.1']))
        super(StdfModifier, self).after_send(dataSource, record)

#*******************************************************************************************************************
class StdfVerify(object):
    """
    """
    @staticmethod
    # =============================================================================================
    def after_send(_, record):
        processedData = IO.encodeRecord(record)
        for field in record.fields():
            record.verify(field.name, field.format, processedData[field.index])

#*******************************************************************************************************************
if __name__ == "__main__":
    fn = r'../data/tfile.std'
    obj = StdfVerify()
    Parse.process_file(fn, [obj], verify=True)
    obj = AtdfWriter()
    Parse.process_file(fn, [obj])
    obj = StdfModifier()
    Parse.process_file(fn, [obj])
    obj = StdfWriter()
    Parse.process_file(fn, [obj])
