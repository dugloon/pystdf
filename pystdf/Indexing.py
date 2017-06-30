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

from OoHelpers import abstract
import V4


class StreamIndexer(object):
    def before_header(self, dataSource, header):
        self.position = dataSource.inp.tell() - 4
        self.header = header


class SessionIndexer(object):
    def getSessionID(self):
        return self.sessionId
    
    def before_begin(self, _):
        self.sessionId = self.createSessionID()
    
    def createSessionID(self): abstract()


class DemoSessionIndexer(SessionIndexer):
    def createSessionID(self): return 0


class RecordIndexer(object):
    def getRecID(self):
        return self.recordId
    
    def before_begin(self, _):
        self.recordId = 0
    
    def before_send(self, _, record):
        self.recordId += 1


class MaterialIndexer(object):
    def __init__(self):
        self.prr = V4.Prr()
        self.pir = V4.Pir()
    
    def getCurrentWafer(self, head):
        return self.currentWafer.get(head, 0)
    
    def getCurrentInsertion(self, head):
        return self.currentInsertion.get(head, 0)
    
    def getCurrentPart(self, head, site):
        return self.currentPart.get((head, site), 0)
    
    def before_begin(self, dataSource):
        self.currentPart = dict()
        self.currentInsertion = dict()
        self.closingInsertion = False
        self.currentWafer = dict()
        self.lastPart = 0
        self.lastInsertion = 0
        self.lastWafer = 0
    
    def before_send(self, dataSource, record):
        if not record.name == 'Prr' and self.closingInsertion:
            for head in self.currentInsertion.keys():
                self.currentInsertion[head] = 0
            self.closingInsertion = False
        
        if record.name == 'Pir':
            headSite = (record.values[self.pir.HEAD_NUM], record.values[self.pir.SITE_NUM])
            self.onPir(headSite)
        elif record.name == 'Wir':
            headSite = (record.values[self.pir.HEAD_NUM], record.values[self.pir.SITE_NUM])
            self.onWir(headSite)
    
    def after_send(self, _, record):
        if record.name == 'Prr':
            headSite = (record.values[self.prr.HEAD_NUM], record.values[self.prr.SITE_NUM])
            self.onPrr(headSite)
    
    def onPir(self, headSite):
        # Increment part count per site
        self.lastPart += 1
        self.currentPart[headSite] = self.lastPart
        
        # Increment insertion count once per head
        if self.currentInsertion.get(headSite[0], 0) == 0:
            self.lastInsertion += 1
            self.currentInsertion[headSite[0]] = self.lastInsertion
    
    def onPrr(self, headSite):
        self.currentPart[headSite] = 0
        self.closingInsertion = True
    
    def onWir(self, headSite):
        if self.currentWafer.get(headSite[0], 0) == 0:
            self.lastWafer += 1
            self.currentWafer[headSite[0]] = self.lastWafer
