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

import Pipeline
import V4


def filterNull(value):
    if value == 4294967295:
        return None
    return value


class PartSummarizer(Pipeline.EventSource):
    FLAG_SYNTH = 0x80
    FLAG_FAIL = 0x08
    FLAG_UNKNOWN = 0x02
    FLAG_OVERALL = 0x01
    
    def __init__(self):
        self.prr = V4.Prr()
        self.pcr = V4.Pcr()
        Pipeline.EventSource.__init__(self, ['partSummaryReady'])
    
    def partSummaryReady(self, _):
        print '---------- Part Summary ----------'
        print self.overall
        for k, v in self.pcSummary.items():
            print k, v
    
    def getOverall(self):
        return self.overall
    
    def getSiteCounts(self):
        return self.pcSummary.values()
    
    def getSiteSynthCounts(self):
        for site, info in self.pcSynth.iteritems():
            partCnt, goodCnt, abortCnt = info
            yield [0, site, partCnt[0], None, abortCnt[0], goodCnt[0], None]
    
    def synthOverall(self):
        result = None
        for row in self.pcSummary.values():
            if result is None:
                result = [value for value in row]
            else:
                for i, value in enumerate(row):
                    if i > self.pcr.SITE_NUM and row[i] is not None:
                        if result[i] is None:
                            result[i] = row[i]
                        else:
                            result[i] += row[i]
        return result
    
    def before_begin(self, _):
        self.pcSynth = dict()
        self.pcSummary = dict()
        self.overall = None
    
    def before_complete(self, dataSource):
        self.partSummaryReady(dataSource)
    
    def before_send(self, _, record):
        if record.name == self.prr.name:
            self.onPrr(record.values)
        elif record.name == self.pcr.name:
            self.onPcr(record.values)
    
    def onPrr(self, row):
        partCnt, goodCnt, abortCnt = self.pcSynth.setdefault(row[self.prr.SITE_NUM], ([0], [0], [0]))
        partCnt[0] += 1
        if row[self.prr.PART_FLG] & 0x08 == 0:
            goodCnt[0] += 1
        if row[self.prr.PART_FLG] & 0x04 == 0:
            abortCnt[0] += 1
    
    def onPcr(self, row):
        if row[self.pcr.HEAD_NUM] == 255:
            self.overall = [filterNull(value) for value in row]
        else:
            self.pcSummary[row[self.pcr.SITE_NUM]] = [filterNull(value) for value in row]


# *******************************************************************************************************************
if __name__ == "__main__":
    from Parse import process_file
    import sys
    fn = r'../data/lot3.stdf'
    filename, = sys.argv[1:] or (fn,)
    ps = PartSummarizer()
    process_file(filename, [ps], breakCount=200)