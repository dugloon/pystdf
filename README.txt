===================================
|PySTDF - The Pythonic STDF parser|
===================================
Originally developed by Casey Marshall <casey.marshall@gmail.com>

PySTDF is a parser for Standard Test Data Format (STDF) version 4 data files.
Casey wrote PySTDF to get familiar with functional programming idioms and
metaclasses in Python.  As such, it uses some of the more powerful and 
expressive features of the Python language.

PySTDF is an event-based parser.  As an STDF file is parsed, you receive
record "events" in callback functions

Refer to the provided command line scripts for ideas on how to use PySTDF:

stdf_atdf, a PySTDF implementation of an STDF-to-ATDF converter.
stdf_slice, an example of how to seek to a specific record offset in the STDF.

Casey also included a very basic STDF viewer GUI, StdfExplorer.  I have plans
to improve upon it further in Q4 2006 - Q5 2007.

=======================
|Fork by Doug Looney|
=======================
Thanks to Casey and the other contributors
Changes:
- Back to Python27
- Metaclasses were removed in favor of a registrar
- Added support for STDF version 2007
- Added ability to write STDF (See Writer.py)
- Added a separate ATDF package
- Added JSON writers
- Added a DPAT summarizer (Dynamic Part Average Testing)
