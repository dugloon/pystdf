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

from pprint import pprint
from Pipeline import EventSource
from Parse import process_file
import V4


class BinSummarizer(EventSource):
    FLAG_SYNTH = 0x80
    FLAG_FAIL = 0x08
    FLAG_UNKNOWN = 0x02
    FLAG_OVERALL = 0x01
    
    def __init__(self):
        self.hbr = V4.Hbr()  # TODO can we use the passed in record below instead?
        self.sbr = V4.Sbr()
        self.prr = V4.Prr()
        super(BinSummarizer, self).__init__(['binSummaryReady'])
    
    def binSummaryReady(self, _):
        print '---------- Bin Summary ----------'
        pprint(self.hbinParts)
        pprint(self.sbinParts)
        pprint(self.summaryHbrs)
        pprint(self.summarySbrs)
        pprint(self.overallHbrs)
        pprint(self.overallSbrs)
    
    def getHPfFlags(self, row):
        flag = 0
        if row[self.hbr.HBIN_PF] == 'F':
            flag |= self.FLAG_FAIL
        elif row[self.hbr.HBIN_PF] != 'P':
            flag |= self.FLAG_UNKNOWN
        return flag
    
    def getSPfFlags(self, row):
        flag = 0
        if row[self.sbr.SBIN_PF] == 'F':
            flag |= self.FLAG_FAIL
        elif row[self.sbr.SBIN_PF] != 'P':
            flag |= self.FLAG_UNKNOWN
        return flag
    
    def getOverallHbins(self):
        return self.overallHbrs.values()
    
    def getSiteHbins(self):
        return self.summaryHbrs.values()
    
    def getSiteSynthHbins(self):
        for siteBin, info in self.hbinParts.iteritems():
            site, bn = siteBin
            partCount, isPass = info
            pf = 'P' if isPass[0] else 'F'
            row = [0, site, bn, partCount[0], pf, None]
            yield row
    
    def getOverallSbins(self):
        return self.overallSbrs.values()
    
    def getSiteSbins(self):
        return self.summarySbrs.values()
    
    def getSiteSynthSbins(self):
        for siteBin, info in self.sbinParts.iteritems():
            site, bn = siteBin
            partCount, isPass = info
            pf = 'P' if isPass[0] else 'F'
            row = [0, site, bn, partCount[0], pf, None]
            yield row
    
    def before_begin(self, _):
        self.hbinParts = dict()
        self.sbinParts = dict()
        self.summaryHbrs = dict()
        self.summarySbrs = dict()
        self.overallHbrs = dict()
        self.overallSbrs = dict()
    
    def before_complete(self, dataSource):
        self.binSummaryReady(dataSource)
    
    def before_send(self, _, record):
        if record.name == self.prr.name:
            self.onPrr(record.values)
        elif record.name == self.hbr.name:
            self.onHbr(record.values)
        elif record.name == self.sbr.name:
            self.onSbr(record.values)
    
    def onPrr(self, row):
        countList, passList = self.hbinParts.setdefault((row[self.prr.SITE_NUM], row[self.prr.HARD_BIN]), ([0], [None]))
        countList[0] += 1
        passing = 'P' if row[self.prr.PART_FLG] & 0x08 == 0 else 'F'
        if passList[0] is None:
            passList[0] = passing
        elif passList[0] != ' ':
            if passList[0] != passing:
                passList[0] = ' '
        
        countList, passList = self.sbinParts.setdefault((row[self.prr.SITE_NUM], row[self.prr.SOFT_BIN]), ([0], [False]))
        countList[0] += 1
        if passList[0] is None:
            passList[0] = passing
        elif passList[0] != ' ':
            if passList[0] != passing:
                passList[0] = ' '
    
    def onHbr(self, row):
        if row[self.hbr.HEAD_NUM] == 255:
            self.overallHbrs[row[self.hbr.HBIN_NUM]] = row
        else:
            self.summaryHbrs[(row[self.hbr.SITE_NUM], row[self.hbr.HBIN_NUM])] = row
    
    def onSbr(self, row):
        if row[self.sbr.HEAD_NUM] == 255:
            self.overallSbrs[row[self.sbr.SBIN_NUM]] = row
        else:
            self.summarySbrs[(row[self.sbr.SITE_NUM], row[self.sbr.SBIN_NUM])] = row


# *******************************************************************************************************************
if __name__ == "__main__":
    filename = r'../data/lot2.stdf'
    process_file(filename, [BinSummarizer()])
