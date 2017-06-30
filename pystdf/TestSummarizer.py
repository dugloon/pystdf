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

from Pipeline import EventSource
import V4


def filterNull(value):
    if value == 4294967295:
        return None
    return value


class TestSummarizer(EventSource):
    FLAG_SYNTH = 0x80
    FLAG_OVERALL = 0x01
    PTR_TEST_TXT = 0x00
    MPR_TEST_TXT = 0x01
    FTR_TEST_TXT = 0x02
    TSR_TEST_NAM = 0x03
    TSR_SEQ_NAME = 0x04
    TSR_TEST_LBL = 0x05
    
    def __init__(self):
        self.ptr = V4.Ptr()
        self.mpr = V4.Mpr()
        self.ftr = V4.Ftr()
        self.tsr = V4.Tsr()
        EventSource.__init__(self, ['testSummaryReady'])
    
    def testSummaryReady(self, dataSource):
        print '---------- Test Summary ----------'
    
    def getOverallTsrs(self):
        return self.overallTsrs.values()
    
    def getSiteTsrs(self):
        return self.summaryTsrs.values()
    
    def getSiteSynthTsrs(self):
        for siteTest, execCnt in self.testExecs.iteritems():
            site, test = siteTest
            tsrRow = [0, site, ' ', test,
                      execCnt[0],
                      self.testFails.get(siteTest, [0])[0],
                      self.testInvalid.get(siteTest, [0])[0],
                      None, None, None]
            yield tsrRow
    
    def before_begin(self, _):
        self.testExecs = dict()
        self.testFails = dict()
        self.testInvalid = dict()
        self.summaryTsrs = dict()
        self.overallTsrs = dict()
        
        # Map of all test numbers to test names
        self.testAliasMap = dict()
        self.unitsMap = dict()
        self.limitsMap = dict()
        
        # Functional summary information
        self.cyclCntMap = dict()
        self.relVadrMap = dict()
        self.failPinMap = dict()
    
    def before_complete(self, dataSource):
        testKeys = set(self.testFails.keys())
        summaryTsrKeys = set(self.summaryTsrs.keys())
        
        # Determine which summary bin records need to be synthed
        # from part records.
        self.synthSummaryTsrKeys = testKeys - summaryTsrKeys
        
        # Determine which overall bin records need to be synthed
        #    for siteTest, row in self.summaryTsrs.iteritems():
        #      if not self.overallTsrs.has_key(siteTest[1]):
        #        overallCount = self.synthOverallTsrs.setdefault(siteTest[1], [0])
        #        overallCount[0] += row[tsr.FAIL_CNT]
        #    for siteTest, partCount in self.testFails.iteritems():
        #      if not self.overallTsrs.has_key(siteTest[1]):
        #        overallCount = self.synthOverallTsrs.setdefault(siteTest[1], [0])
        #        overallCount[0] += partCount[0]
        self.testSummaryReady(dataSource)
    
    def before_send(self, _, record):
        if record.name == self.ptr.name:
            self.onPtr(record.values)
        elif record.name == self.mpr.name:
            self.onMpr(record.values)
        elif record.name == self.ftr.name:
            self.onFtr(record.values)
        elif record.name == self.tsr.name:
            self.onTsr(record.values)
    
    def onPtr(self, row):
        execCount = self.testExecs.setdefault(
            (row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM]), [0])
        execCount[0] += 1
        if row[self.ptr.TEST_FLG] & 0x80 > 0:
            failCount = self.testFails.setdefault(
                (row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM]), [0])
            failCount[0] += 1
        if row[self.ptr.TEST_FLG] & 0x41 > 0:
            invalidCount = self.testInvalid.setdefault(
                (row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM]), [0])
            invalidCount[0] += 1
        aliases = self.testAliasMap.setdefault(row[self.ptr.TEST_NUM], set())
        aliases.add((row[self.ptr.TEST_TXT], self.PTR_TEST_TXT))
        if self.ptr.UNITS < len(row) and row[self.ptr.UNITS]:
            units = self.unitsMap.setdefault(row[self.ptr.TEST_NUM], [None])
            units[0] = row[self.ptr.UNITS]
        if row[self.ptr.OPT_FLAG] is not None and row[self.ptr.OPT_FLAG] & 0x40 == 0:
            loLimit = row[self.ptr.LO_LIMIT]
        else:
            loLimit = None
        if row[self.ptr.OPT_FLAG] is not None and row[self.ptr.OPT_FLAG] & 0x80 == 0:
            hiLimit = row[self.ptr.HI_LIMIT]
        else:
            hiLimit = None
        if loLimit is not None or hiLimit is not None:
            limits = self.limitsMap.setdefault(row[self.ptr.TEST_NUM], set())
            limits.add((loLimit, hiLimit))
    
    def onMpr(self, row):
        if row[self.mpr.TEST_FLG] & 0x80 > 0:
            failCount = self.testFails.setdefault(
                (row[self.mpr.SITE_NUM], row[self.mpr.TEST_NUM]), [0])
            failCount[0] += 1
        if row[self.ptr.TEST_FLG] & 0x41 > 0:
            invalidCount = self.testInvalid.setdefault(
                (row[self.ptr.SITE_NUM], row[self.ptr.TEST_NUM]), [0])
            invalidCount[0] += 1
        aliases = self.testAliasMap.setdefault(row[self.mpr.TEST_NUM], set())
        aliases.add((row[self.mpr.TEST_TXT], self.MPR_TEST_TXT))
        if self.mpr.UNITS < len(row) and row[self.mpr.UNITS]:
            units = self.unitsMap.setdefault(row[self.mpr.TEST_NUM], [None])
            units[0] = row[self.mpr.UNITS]
        if row[self.mpr.OPT_FLAG] is not None and row[self.mpr.OPT_FLAG] & 0x40 == 0:
            loLimit = row[self.mpr.LO_LIMIT]
        else:
            loLimit = None
        if row[self.mpr.OPT_FLAG] is not None and row[self.mpr.OPT_FLAG] & 0x80 == 0:
            hiLimit = row[self.mpr.HI_LIMIT]
        else:
            hiLimit = None
        if loLimit is not None or hiLimit is not None:
            limits = self.limitsMap.setdefault(row[self.mpr.TEST_NUM], set())
            limits.add((loLimit, hiLimit))
    
    def onFtr(self, row):
        if row[self.ftr.TEST_FLG] & 0x80 > 0:
            countList = self.testFails.setdefault(
                (row[self.ftr.SITE_NUM], row[self.ftr.TEST_NUM]), [0])
            countList[0] += 1
        
        if row[self.ftr.OPT_FLAG] is not None:
            if row[self.ftr.OPT_FLAG] & 0x01 > 0:
                countList = self.cyclCntMap.setdefault((row[self.ftr.TEST_NUM], row[self.ftr.CYCL_CNT]), [0])
                countList[0] += 1
            if row[self.ftr.OPT_FLAG] & 0x02 > 0:
                countList = self.relVadrMap.setdefault((row[self.ftr.TEST_NUM], row[self.ftr.REL_VADR]), [0])
                countList[0] += 1
            if self.ftr.RTN_STAT < len(row) and self.ftr.RTN_INDX < len(row) \
                    and row[self.ftr.RTN_STAT] and row[self.ftr.RTN_INDX]:
                for i, rtnStat in enumerate(row[self.ftr.RTN_STAT]):
                    if rtnStat > 4 and i < len(row[self.ftr.RTN_INDX]):  # A failing return state...
                        pmrIndx = row[self.ftr.RTN_INDX][i]
                        countList = self.failPinMap.setdefault((row[self.ftr.TEST_NUM], pmrIndx), [0])
                        countList[0] += 1
        
        aliases = self.testAliasMap.setdefault(row[self.ftr.TEST_NUM], set())
        aliases.add((row[self.ftr.TEST_TXT], self.FTR_TEST_TXT))
    
    def onTsr(self, row):
        if row[self.tsr.HEAD_NUM] == 255:
            self.overallTsrs[row[self.tsr.TEST_NUM]] = [filterNull(value) for value in row]
        else:
            self.summaryTsrs[(row[self.tsr.SITE_NUM], row[self.tsr.TEST_NUM])] = [filterNull(value) for value in row]
        aliases = self.testAliasMap.setdefault(row[self.tsr.TEST_NUM], set())
        aliases.add((row[self.tsr.TEST_NAM], self.TSR_TEST_NAM))
        aliases.add((row[self.tsr.SEQ_NAME], self.TSR_SEQ_NAME))
        aliases.add((row[self.tsr.TEST_LBL], self.TSR_TEST_LBL))


# *******************************************************************************************************************
if __name__ == "__main__":
    from Parse import process_file
    import sys
    fn = r'../data/lot3.stdf'
    filename, = sys.argv[1:] or (fn,)
    ts = TestSummarizer()
    process_file(filename, [ts], breakCount=200)