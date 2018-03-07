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

__author__ = 'dugloon'

import sys
import collections

from Parse import process_file

#*******************************************************************************************************************
def dpatLimits(passingValues, lowerThreshold, upperThreshold):
    '''
    http://ams/productEng/processors/Shared Documents/AEC Documents/AEC_Q001_Rev_D.pdf
    '''
    passingValues.sort()
    length = len(passingValues)
    if length < 30:
        raise ValueError, "DPAT is invalid on less than 30 values"
    n = length // 2
    mean = passingValues[n] if length % 2 != 0 else (passingValues[n] + passingValues[n-1]) / 2.0
    q1, q3 = float(passingValues[length / 4]), float(passingValues[length * 3 / 4])
    sigma = 6.0 * (q3 - q1) / 1.35
    return max(lowerThreshold, mean - sigma), min(upperThreshold, mean + sigma)

#*******************************************************************************************************************
class DpatSink(object):
    def __init__(self):
        self.defaults = None
        self.parts = None
        self.touchDown = None
        self.ndx2Chan = None

    def before_begin(self, dataSrc): pass
    def after_begin(self, _):
        self.defaults = dict()
        self.parts = collections.defaultdict(dict)
        self.touchDown = collections.defaultdict(dict)
        self.ndx2Chan = dict()

    def before_send(self, _, record):
        valMap = record.valuesMap()
        if record.name == 'Prr' and valMap['HARD_BIN']:  # final bookend after a touchDown for each head-site
            headSiteKey = valMap['HEAD_NUM'], valMap['SITE_NUM']
            partKey = '%s (%s, %s)' % (valMap['PART_ID'], valMap['X_COORD'], valMap['Y_COORD'])
            self.parts[partKey] = self.touchDown[headSiteKey].copy()
            self.touchDown[headSiteKey].clear()
        if record.name == 'Pmr':
            self.ndx2Chan[valMap['PMR_INDX']] = valMap['CHAN_NAM']  # PMRs are located prior to any touchdown record

    def after_send(self, _, record):
        valMap = record.valuesMap()
        paramAttrSet = ['TEST_NUM', 'TEST_TXT', 'LO_LIMIT', 'HI_LIMIT', 'RTN_RSLT', 'RTN_INDX']
        paramAttrSet = set(paramAttrSet)
        fieldSet = set([field.name for field in record.fields()])
        if paramAttrSet.issubset(fieldSet):     # any DPAT candidate record will have these attributes
            testNum = valMap['TEST_NUM']
            headSiteKey = valMap['HEAD_NUM'], valMap['SITE_NUM']
            # first record of each type contains defaults
            if testNum not in self.defaults:
                ndx2chan = list()
                for ndx in valMap['RTN_INDX']:        # use the PMR records to give names to channel indices
                    ndx2chan.append(self.ndx2Chan[ndx])
                self.defaults[testNum] = dict(TEST_NUM=testNum,
                                              TEST_TXT=valMap['TEST_TXT'],
                                              LO_LIMIT=valMap['LO_LIMIT'],
                                              HI_LIMIT=valMap['HI_LIMIT'],
                                              NDX2CHAN=ndx2chan)
            lst = valMap['RTN_RSLT'] if hasattr(valMap['RTN_RSLT'], 'sort') else [valMap['RTN_RSLT']]
            self.touchDown[headSiteKey][testNum] = lst  # make sure we have an iterable for later, do not sort yet

    ### The 'complete' event methods get called after a successful STDF parse completes.

    def before_complete(self, _):
        for testNum, testDict in self.defaults.items():
            allResults = list()                             # to apply DPAT across all channels for a test
            padResults = collections.defaultdict(list)      # to apply DPAT across one channel per test
            for partId, partDict in self.parts.items():
                results = partDict.get(testNum, [])
                allResults += results
                for i, result in enumerate(results):
                    pad = testDict['NDX2CHAN'][i]   # this array was built in order with the defaults block earlier
                    padResults[pad].append(result)
            print 'DPAT for %s: %d values' % (testDict['TEST_TXT'], len(allResults))
            loLimit, hiLimit = dpatLimits(allResults, testDict['LO_LIMIT'], testDict['HI_LIMIT'])
            testDict['NEW_LOW'] = loLimit
            testDict['NEW_HIGH'] = hiLimit
            for pad, results in padResults.items():
                loLimit, hiLimit = dpatLimits(results, testDict['LO_LIMIT'], testDict['HI_LIMIT'])
                testDict['%s_LOW' % pad] = loLimit
                testDict['%s_HIGH' % pad] = hiLimit

    def after_complete(self, _):
        fmt = '%(LO_LIMIT)s \t%(NEW_LOW)s \t%(HI_LIMIT)s \t%(NEW_HIGH)s \t%(TEST_NUM)s-%(TEST_TXT)s'
        print '\n'
        print 'OLD_LOW \tNEW_LOW \tOLD_HIGH \tNEW_HIGH \tTEST'
        for testNum, testDict in self.defaults.items():
            print fmt % testDict
        print '\n\n'
        for testNum, testDict in self.defaults.items():
            pads = testDict['NDX2CHAN']
            print '----- test %s - %s' % (testNum, testDict['TEST_TXT'])
            print 'PAD \tPAD_LOW \tPAD_HIGH'
            for pad in pads:
                fmt = '%s \t%%(%s_LOW)s \t%%(%s_HIGH)s' % (pad, pad, pad)
                print fmt % testDict
            print '\n'
        print '\n'
        for testNum, testDict in self.defaults.items():
            pads = testDict['NDX2CHAN']
            #newLT, newUT = testDict['NEW_LOW'], testDict['NEW_HIGH']
            print '\n ------------- DPAT fails for ', testDict['TEST_TXT']
            print '#\tpart\tpads_lo\tpads_hi'
            p = 0
            for partId, partDict in self.parts.items():
                lo, hi = [], []
                for i, result in enumerate(partDict.get(testNum, [])):
                    pad = pads[i]
                    newLT, newUT = testDict['%s_LOW' % pad], testDict['%s_HIGH' % pad]
                    if newLT <= result <= newUT:
                        continue
                    pad = testDict['NDX2CHAN'][i]
                    if newLT > result:
                        lo.append(pad)
                    if result > newUT:
                        hi.append(pad)
                if lo or hi:
                    p +=1
                    print '%s\t%s\t%s\t%s' % (p, partId, lo, hi)

    ### The 'cancel' event methods are called after an error in the STDF parse.
    ### The unhandled exception is passed as the second 'exc' argument.
    def before_cancel(self, src, exc):
        pass
    def after_cancel(self, snk, exc):
        pass

#*******************************************************************************************************************
if __name__ == "__main__":
    if len(sys.argv) < 2:
        process_file(r'../data/lot3.stdf', [DpatSink()])
    else:
        process_file(sys.argv[1], [DpatSink()])