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

import re
import sys
import gzip, bz2
from parse import Parser
from writers import JsonWriter

gzPattern = re.compile('\.g?z', re.I)
bz2Pattern = re.compile('\.bz2', re.I)

def process_file(filename):
    if filename is None:
        f = sys.stdin
    elif gzPattern.search(filename):
        f = gzip.open(filename, 'rb')
    elif bz2Pattern.search(filename):
        f = bz2.BZ2File(filename, 'rb')
    else:
        f = open(filename, 'rb')
    p=Parser(inp=f)
    p.addSink(JsonWriter())
    p.parse()
    f.close()

#**************************************************************************************************
#**************************************************************************************************
if __name__ == "__main__":
    if len(sys.argv) < 2:
        process_file(r'/path/to/file.atdf')
    else:
        process_file(sys.argv[1])
