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

from SummaryStatistics import SummaryStatistics
import V4
from Pipeline import EventSource

class ParametricSummarizer(EventSource):
    def __init__(self):
        self.ptr = V4.Ptr()
        self.mpr = V4.Mpr()
        EventSource.__init__(self, ['parametricSummaryReady'])

    def parametricSummaryReady(self, _):
        print '---------- Parametric Summary ----------'
        for k, v in self.summaryMap.items():
            print k, v

    def getAllRows(self):
        return self.summaryMap.iteritems()

    def before_begin(self, _):
        self.rawMap = dict()
        self.summaryMap = None

    def before_complete(self, dataSource):
        self.summaryMap = dict()
        for key, values in self.rawMap.iteritems():
            values.sort()
            self.summaryMap[key] = SummaryStatistics(values)
        self.parametricSummaryReady(dataSource)

    def before_send(self, _, record):
        if record.name == 'Ptr':
            self.onPtr(record.values)
        elif record.name == 'Mpr':
            self.onMpr(record.values)

    def onPtr(self, row):
        values = self.rawMap.setdefault((row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM], 0), [])
        values.append(row[self.ptr.RESULT])

    def onMpr(self, row):
        for i in xrange(row[self.mpr.RSLT_CNT]):
            values = self.rawMap.setdefault((row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM], i), [])
            values.append(row[self.mpr.RTN_RSLT][i])

#*******************************************************************************************************************
if __name__ == "__main__":
    from Parse import process_file
    import sys
    fn = r'../data/lot3.stdf'
    #fn = r'/path/to/log.stdf.gz'
    filename, = sys.argv[1:] or (fn,)
    ps = ParametricSummarizer()
    process_file(filename, [ps], breakCount=20)
