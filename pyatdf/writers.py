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
from cStringIO import StringIO
import threading
import json

class JsonWriter:

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        self.lines = list(['{"data":[\n'])

    def after_send(self, dataSource, record):
        line = dict(k=record.name, v=record.values)
        self.lines.append(json.dumps(line) + ',\n')
        if len(self.lines) > 1000:
            self.stream.writelines(self.lines)
            self.lines = list()

    def after_complete(self, dataSource):
        if len(self.lines):
            self.stream.writelines(self.lines)
        self.stream.seek(-3, 2)     # backup over the last ',\n'
        self.stream.write('\n]}\n')
        self.stream.flush()

class JsonStreamer(JsonWriter):

    def __init__(self):
        self._lock = threading.Lock()
        self._done = False
        JsonWriter.__init__(self, StringIO())

    def grabBuffer(self):
        with self._lock:
            self.stream.flush()
            self.stream.seek(0)
            buf = self.stream.read()
            self.stream.seek(0)
            self.stream.truncate()
        if buf:
            return buf
        if self._done:
            self.stream.close()
        return self._done

    def after_send(self, dataSource, record):
        with self._lock:
            JsonWriter.after_send(self, dataSource, record)

    def after_complete(self, dataSource):
        with self._lock:
            JsonWriter.after_complete(self, dataSource)
        self._done = True
