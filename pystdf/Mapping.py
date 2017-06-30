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

from Indexing import StreamIndexer, MaterialIndexer
import V4

class StreamMapper(StreamIndexer):
    def __init__(self):
        self.indexes = []
        self.records = []

    def before_header(self, dataSource, header):
        super(StreamMapper, self).before_header(dataSource, header)
        self.indexes.append(self.position)
        rec = V4.recordByType(self.header.typ, self.header.sub)
        self.records.append(rec)

class MaterialMapper(MaterialIndexer):
    indexed = {'Wir', 'Wrr', 'Pir', 'Prr', 'Ptr', 'Mpr', 'Ftr'}
    perPart = {'Pir', 'Prr', 'Ptr', 'Mpr', 'Ftr'}

    def before_begin(self, dataSource):
        MaterialIndexer.before_begin(self, dataSource)
        self.waferIds = []
        self.insertionIds = []
        self.partIds = []

    def before_send(self, dataSource, record):
        MaterialIndexer.before_send(self, dataSource, record)
        if record.name in self.indexed:
            head = record.values[record.HEAD_NUM]
            self.waferIds.append(self.getCurrentWafer(head))
            self.insertionIds.append(self.getCurrentInsertion(head))
            if record.name in self.perPart:
                site = record.values[record.SITE_NUM]
                self.partIds.append(self.getCurrentPart(head, site))
            else:
                self.partIds.append(None)
        else:
            self.waferIds.append(None)
            self.insertionIds.append(None)
            self.partIds.append(None)

#*******************************************************************************************************************
if __name__ == "__main__":
    from Parse import process_file
    import sys
    fn = r'../data/lot3.stdf'
    #fn = r'/path/to/log.stdf.gz'
    filename, = sys.argv[1:] or (fn,)
    record_mapper = StreamMapper()
    material_mapper = MaterialMapper()
    process_file(filename, [record_mapper, material_mapper], breakCount=20)
    for index, rectype in zip(record_mapper.indexes, record_mapper.records):
        print index, str(rectype)
    for index, waferId in enumerate(material_mapper.waferIds):
        print index, waferId
    for index, insId in enumerate(material_mapper.insertionIds):
        print index, insId
    for index, partId in enumerate(material_mapper.partIds):
        print index, partId
