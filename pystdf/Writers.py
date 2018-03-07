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

from cStringIO import StringIO
import threading
import sys, re
from time import strftime, localtime
from xml.sax.saxutils import quoteattr
import Parse

def format_by_type(value, field_type):
    if field_type in ('B1', 'N1'):
        return '%02X' % value
    return str(value)

class XmlWriter:
    extra_entities = {'\0': ''}

    @staticmethod
    def xml_format(rectype, field):
        value = rectype.values[field.index]
        if value is None:
            return ""
        if field.arrayFmt: # An Array of some other type
            return ','.join([format_by_type(v, field.arrayFmt) for v in value])
        if rectype.name in ['Mir', 'Mrr']:
            if field.name.endswith('_T'): # A Date-Time in an MIR/MRR
                return strftime('%H:%M:%ST%d-%b-%Y', localtime(value))
            return str(value)
        return str(value)

    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def before_begin(self, _):
        self.stream.write('<Stdf>\n')

    def after_send(self, _, record):
        self.stream.write('<%s' % record.name)
        for field in record.fields():
            val = self.xml_format(record, field)
            self.stream.write(' %s=%s' % (field.name, quoteattr(val, self.extra_entities)))
        self.stream.write('/>\n')

    def after_complete(self, _):
        self.stream.write('</Stdf>\n')
        self.stream.flush()

def json_by_type(value, field_type):
    if field_type in ('B1', 'N1'):
        return '"0x%02X"' % value
    if field_type == 'C1':
        return '"%s"' % value if 31 < ord(value) < 127 else '" "'
    if field_type == 'Cn':
        return '"%s"' % value
    if field_type in ('Bn', 'Dn', 'Vn'):
        return str(value) if unicode(value).isnumeric() else '"%s"' % value
    return str(value)

class JsonWriter:
    _ws = re.compile(r'[\t\f\v]')
    _ms = re.compile(r' {2,}')

    @staticmethod
    def json_format(rectype, field):
        value = rectype.values[field.index]
        if value is None:
            return '""'
        if field.arrayFmt: # An Array of some other type
            if not len(value):
                return '[]'
            return '[%s]' % ','.join([json_by_type(v, field.format[:2]) for v in value])
        if rectype.name in ['Mir', 'Mrr']:
            if field.name.endswith('_T'): # A Date-Time in an MIR/MRR
                return strftime('"%Y-%m-%d %H:%M:%S"', localtime(value))
            return json_by_type(value, field.format[:2])
        return json_by_type(value, field.format[:2])

    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def before_begin(self, dataSource):
        self.stream.write('{"data":[\n')
        self.sep = ''

    def after_send(self, dataSource, record):
        line = '%s{"k":"%s", "v":[%s]}\n' % (self.sep, record.name,
                            ','.join([self.json_format(record, field) for field in record.fields()]))
        self.sep = ','
        line = self._ms.sub(' ', self._ws.sub(' ', line))
        self.stream.write(line)

    def after_complete(self, dataSource):
        self.stream.write(']}\n')
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

    def before_begin(self, dataSource):
        with self._lock:
            JsonWriter.before_begin(self, dataSource)

    def after_send(self, dataSource, record):
        with self._lock:
            JsonWriter.after_send(self, dataSource, record)

    def after_complete(self, dataSource):
        with self._lock:
            JsonWriter.after_complete(self, dataSource)
        self._done = True


#*******************************************************************************************************************
if __name__ == "__main__":
    fn = r'../data/tfile.std'
    obj = JsonWriter()
    Parse.process_file(fn, [obj])
    obj = XmlWriter()
    Parse.process_file(fn, [obj])
