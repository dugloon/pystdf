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

import bz2
import gzip
import re
import sys
import traceback

import V4
from Pipeline import DataSource
import IO
import Types


# **********************************************************************************************
# **********************************************************************************************
class Parser(DataSource):
    def __init__(self, inp=sys.stdin, lazy=False):
        super(Parser, self).__init__(['header'])
        self.inp = inp
        self.lazy = lazy
        self.endian = '@'

    # **********************************************************************************************
    def header(self, data):
        pass  # This is here so that sinks can intercept the header event

    # **********************************************************************************************
    def parse_records(self, breakCount=0):
        recordCount = 1
        try:
            while recordCount:
                header = IO.readHeader(self.endian, self.inp, V4.RecordRegistrar)
                self.header(header)
                if V4.RecordRegistrar.has_key((header.typ, header.sub)):
                    record = V4.RecordRegistrar[(header.typ, header.sub)](header=header, parser=self)
                    if not self.lazy:
                        IO.decodeValues(record)
                    self.send(record)
                else:
                    self.inp.read(header.len)
                if breakCount and recordCount > breakCount:
                    break
                recordCount += 1
        except Types.EofException:
            pass

    # **********************************************************************************************
    def parse(self, breakCount=0):
        self.begin()
        try:
            self.endian = IO.detectEndian(self.inp)
            self.parse_records(breakCount)
            self.complete()
        except Exception, exception:
            print traceback.format_exc(limit=7)
            self.cancel(exception)
            raise


# **********************************************************************************************
# **********************************************************************************************
class Reader(object):
    def __init__(self, fileName, mode="rb"):
        if fileName.endswith('.gz'):
            self.inp = gzip.open(fileName, mode)
        elif fileName.endswith('.bz'):
            self.inp = bz2.BZ2File(fileName, mode)
        else:
            self.inp = open(fileName, mode)
        self.endian = IO.detectEndian(self.inp)

    # **********************************************************************************************
    def __iter__(self):
        return self

    # **********************************************************************************************
    def __del__(self):
        if self.inp:
            self.inp.close()

    # **********************************************************************************************
    def next(self):
        try:
            header = IO.readHeader(self.endian, self.inp, V4.RecordRegistrar)
            key = (header.typ, header.sub)
            if V4.RecordRegistrar.has_key(key):
                record = V4.RecordRegistrar[key](header=header, parser=self)
                IO.decodeValues(record)
                return record
            else:
                raise KeyError("Unknown type (%s): Len (%d)" % (key, header.len))
        except Exception:
            self.inp.close()
            self.inp = None
            raise StopIteration


# **********************************************************************************************
# **********************************************************************************************
def runDocTests():
    import doctest
    with open(r'../data/demofile.stdf') as fin:
        pObj = Parser(inp=fin)
        doctest.testmod(extraglobs={'pObj': pObj})


# *******************************************************************************************************************
def process_file(filename, writers, breakCount=0, lazy=False):
    gzPattern = re.compile('\.g?z', re.I)
    bz2Pattern = re.compile('\.bz2', re.I)
    if filename is None:
        f = sys.stdin
    elif gzPattern.search(filename):
        reopen_fn = lambda: gzip.open(filename, 'rb')
        f = reopen_fn()
    elif bz2Pattern.search(filename):
        reopen_fn = lambda: bz2.BZ2File(filename, 'rb')
        f = reopen_fn()
    else:
        f = open(filename, 'rb')
    p = Parser(inp=f, lazy=lazy)
    for writer in writers:
        p.addSink(writer)
    p.parse(breakCount=breakCount)
    f.close()


# *******************************************************************************************************************
if __name__ == "__main__":
    fn = r'../data/demofile.stdf'
    # process_file(fn, [])
    for rec in Reader(fn):
        print repr(rec)