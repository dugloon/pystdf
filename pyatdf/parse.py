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
import A4

from pystdf.Pipeline import DataSource

#**************************************************************************************************
#**************************************************************************************************
class Parser(DataSource):

    #**********************************************************************************************
    def parse(self, count=0):
        self.begin()
        try:
            self.parse_records(count)
            self.complete()
        except Exception, exception:
            self.cancel(exception)
            raise

    #**********************************************************************************************
    def parse_records(self, count=0):
        i, line = 0, self.inp.readline()
        while line:
            line = line.strip()
            nextLine = self.inp.readline()
            while nextLine and nextLine[0] == ' ': # line continuations allowed if first char is ' '
                line += nextLine.strip()
                nextLine = self.inp.readline()
            recordType, recordData = line[:3], line[4:]
            recordType = recordType.title()
            if self.recordMap.has_key(recordType):
                recType = self.recordMap[recordType]
                fields = self.recordParser(recordData, recType)
                if len(fields) < recType.fieldCount:
                    fields += [None] * (recType.fieldCount - len(fields))
                self.send((recType, fields))
            if count:
                i += 1
                if i >= count: break
            line = nextLine

    #**********************************************************************************************
    @staticmethod
    def recordParser(line, recType, sep='|'):
        values = line.split(sep)
        for i, value in enumerate(values):       # GDR has fieldCount == 1 but unlimited fields
            name, caster = recType.fieldTuple[i] if i < recType.fieldCount else recType.fieldTuple[0]
            if value and caster:
                values[i] = caster(value)
        return values

    #**********************************************************************************************
    def __init__(self, recTypes=A4.records, inp=sys.stdin):
        DataSource.__init__(self, [])
        self.recTypes = set(recTypes)
        self.inp = inp
        self.recordMap = dict([(recType.__class__.__name__, recType ) for recType in recTypes])
