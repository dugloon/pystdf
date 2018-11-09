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
"""
STDF Record Types
-----------------

====== ====== ==== ======  ====================================
Major  Minor  2007 Record  Type
====== ====== ==== ======  =================================== Info
   00     10       FAR     File Attributes Record
   00     20       ATR     Audit Trail Record
   00     30  new  VUR     Version Update Record
-------------------------------------------------------------- Per Lot
   01     10       MIR     Master Information Record
   01     20       MRR     Master Results Record
   01     30       PCR     Part Count Record
   01     40       HBR     Hardware Bin Record
   01     50       SBR     Software Bin Record
   01     60       PMR     Pin Map Record
   01     62       PGR     Pin Group Record
   01     63       PLR     Pin List Record
   01     70       RDR     Retest Data Record
   01     80       SDR     Site Description Record
   01     90  new  PSR     Pattern Sequence Record
   01     91  new  NMR     Name Map Record
   01     92  new  CNR     Cell Name Record
   01     93  new  SSR     Scan Structure Record
   01     94  new  CDR     Chain Description Record
------------------------------------------------------------- Per Wafer
   02     10       WIR     Wafer Information Record
   02     20       WRR     Wafer Results Record
   03     30       WCR     Wafer Configuration Record
------------------------------------------------------------- Per Part
   05     10       PIR     Part Information Record
   05     20       PRR     Part Results Record
------------------------------------------------------------- Per Test Description
   10     30       TSR     Test Synopsis Record
------------------------------------------------------------- Per Test Execution
   15     10       PTR     Parametric Test Record
   15     15       MPR     Multiple-Result Parametric Record
   15     20       FTR     Functional Test Record
   15     30  new  STR     Scan Test Record
------------------------------------------------------------- Per Program Segment
   20     10       BPS     Begin Program Section Record
   20     20       EPS     End Program Section Record
------------------------------------------------------------- Generic Data
   50     10       GDR     Generic Data Record
   50     30       DTR     Datalog Text Record
====== ====== ==== ======  ====================================


Data Type Codes and Representation
----------------------------------

====== ==== ===================================================  ===================
Code   2007 Description                                          C Type Specifier
====== ==== ===================================================  ===================
C*12        Fixed length character string:                       char[12]
              If a fixed length character string does not fill
              the entire field, it must be left-justified and
              padded with spaces.
C*n         Variable length character string:                    char[]
              first byte = unsigned count of bytes to follow
              (maximum of 255 bytes)
S*n    new  Variable length character string:                    char[]
              first two bytes = unsigned count of bytes to
              follow (maximum of 65535 bytes)
C*f         Variable length character string:                    char[]
              string length is stored in another field
U*f         Variable length U type fields where:
              the type f is stored in another field can have
              value 1, 2 or 4
U*1         One byte unsigned integer                            unsigned char
U*2         Two byte unsigned integer                            unsigned short
U*4         Four byte unsigned integer                           unsigned long
I*1         One byte signed integer                              char
I*2         Two byte signed integer                              short
I*4         Four byte signed integer                             long
R*4         Four byte floating point number                      float
R*8         Eight byte floating point number                     long float (double)
B*6         Fixed length bit-encoded data                        char[6]
V*n         Variable data type field:
              The data type is specified by a code in the
              first byte, and the data follows
              (maximum of 255 bytes)
B*n         Variable length bit-encoded field:                   char[]
              First byte = unsigned count of bytes to follow
              (maximum of 255 bytes).
              First data item in least significant bit of the
              second byte of the array (first byte is count.)
D*n         Variable length bit-encoded field:                   char[]
              First two bytes = unsigned count of bits to
              follow (maximum of 65,535 bits).
              First data item in least significant bit of the
              third byte of the array (first two bytes are
              count).
              Unused bits at the high order end of the last
              byte must be zero.
N*1         Unsigned integer data stored in a nibble.            char
              First item in low 4 bits, second item in high
              4 bits. If an odd number of nibbles is indicated,
              the high nibble of the byte will be zero. Only
              whole bytes can be written to the STDF file.
kxTYPE      Array of data of the type specified.                 TYPE[]
              The value of *k* (the number of elements in the
              array) is defined in an earlier field in the
              record. For example, an array of short unsigned
              integers is defined as kxU*2.
======      ===================================================  ===================

"""

from Types import RecordType, UnknownRecord
from IO import encodeGdr, GEN_DATA_

B7, B6, B5, B4, B3, B2, B1, B0, BN = 0x7f, 0xbf, 0xdf, 0xef, 0xf7, 0xfb, 0xfd, 0xfe, 0xff

# =======================================================================
RecordRegistrar = dict()

def recordByType(typ, sub):
    key = (typ, sub)
    if RecordRegistrar.has_key(key):
        return RecordRegistrar[key]()
    return UnknownRecord(typ, sub)

# =======================================================================
def registerMe(cls):
    """
    Decorator places each record class into the registrar by name and (type, subtype)
    """
    cls.name = cls.__name__
    cls._fields = [None] * len(cls.fieldMap)
    for ndx, fld in enumerate(cls.fieldMap):
        setattr(cls, fld[0], ndx)
        arrayFmt, arrayNdx, itemNdx  = None, None, None
        name, fmt, missing = fld[:3]
        if fmt[0] == 'k':
            arrayNdx, arrayFmt = cls.arrayMatch.match(fmt).groups()
            arrayNdx = int(arrayNdx)
        if name in cls.sizeMap:
            itemNdx = cls.sizeMap[name]
        cls._fields[ndx] = RecordType.Field(name=name,
                                format=fmt,
                                missing=missing,
                                index=ndx,
                                arrayFmt=arrayFmt,
                                arrayNdx=arrayNdx,
                                itemNdx=itemNdx)
    RecordRegistrar[cls.name] = RecordRegistrar[(cls.typ, cls.sub)] = cls
    return cls

@registerMe
class Far(RecordType):
    """
    **File Attributes Record (FAR)**

    Function:
      Contains the information necessary to determine how to decode
      the STDF data contained in the file.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(0)
      REC_SUB  U*1  Record sub-type (10)
      CPU_TYPE U*1  CPU type that wrote this file
      STDF_VER U*1  STDF version number
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      CPU_TYPE:
        Indicates which type of CPU wrote this STDF file. This information is
        useful for determining the CPU-dependent data representation of the
        integer and floating point fields in the file's records. The valid values
        are:

        - 0:        DEC PDP-11 and VAX processors. F and D floating point formats
                    will be used. G and H floating point formats will not be used.
        - 1:        Sun1,2,3, and 4computers.
        - 2:        Sun 386i computers, and IBM PC, IBM PC-AT, and IBM PC-XT
                    computers.
        - 3-127:    Reserved for future use by Teradyne.
        - 128-255:  Reserved for use by customers.

        A code defined here may also be valid for other CPU types whose data
        formats are fully compatible with that of the type listed here. Before
        using one of these codes for a CPU type not listed here, please check
        with the Teradyne hotline, which can provide additional information on CPU
        compatibility.
      STDF_VER:
        Identifies the version number of the STDF specification used in generating
        the data. This allows data analysis programs to handle STDF specification
        enhancements.

    Location:
      Required as the first record of the file.
    """
    typ = 0
    sub = 10
    fieldMap = (
        ('CPU_TYPE', 'U1', None),
        ('STDF_VER', 'U1', None)
        )

@registerMe
class Atr(RecordType):
    """
    **Audit Trail Record (ATR)**

    Function:
      Used to record any operation that alters the contents of the STDF
      file. The name of the program and all its parameters should be recorded
      in the ASCII field provided in this record. Typically, this record will
      be used to track filter programs that have been applied to the data.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(0)
      REC_SUB  U*1  Record sub-type (20)
      MOD_TIM  U*4  Date and time of STDF file
                    modification
      CMD_LINE C*n  Command line of program
      ======== ==== ========================================= ====================

    Frequency:
      Optional. One for each filter or other data transformation program applied
      to the STDF data.

    Location:
      Between the File Attributes Record (FAR) and the Master Information
      Record (MIR). The filter program that writes the altered STDF file must
      write its ATR immediately after the FAR (and hence before any other ATR's
      that may be in the file). In this way, multiple ATR's will be in reverse
      chronological order.

    Possible Use:
      Determining whether a particular filter has been applied to the data.
    """
    typ = 0
    sub = 20
    fieldMap = (
        ('MOD_TIM',  'U4', None),
        ('CMD_LINE', 'Cn', None)
        )

@registerMe
class Vur(RecordType):
    """
    **Version Update Record (VUR)**

    Function:
      Version update Record is used to identify the updates over version V4.
      Presence of this record indicates that the file may contain records defined by
      the new standard. This record is added to the major type 0 in the STDF V4.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(0)
      REC_SUB  U*1  Record sub-type (10)
      UPD_CNT  U*1  Count (k) of version update entries
      UPD_NAM  kxCn Array of update version name              K=0
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      UPD_NAM: This field will contain the version update name. For example the new
      standard name will be stored as 'Scan:2007.1' string in the UPD_NAM field.

    Location:
      Required directly subsequent to the FAR and optional ATRs IFF this file contains 2007 record types
    """
    typ = 0
    sub = 30
    fieldMap = (
        ('UPD_CNT',   'U1', None),
        ('UPD_NAM', 'k0Cn', None)
        )

@registerMe
class Mir(RecordType):
    """
    **Master Information Record (MIR)**

    Function:
      The MIR and the MRR (Master Results Record) contain all the global
      information that is to be stored for a tested lot of parts. Each data
      stream must have exactly oneMIR, immediately after theFAR (and the ATR's,
      if they are used). This will allow any data reporting or analysis
      programs access to this information in the shortest possible amount
      of time.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (10)
      SETUP_T  U*4  Date and time of job setup
      START_T  U*4  Date and time first part tested
      STAT_NUM U*1  Tester station number
      MODE_COD C*1  Test mode code (e.g. prod, dev) space
      RTST_COD C*1  Lot retest codespace
      PROT_COD C*1  Data protection codespace
      BURN_TIM U*2  Burn-in time (in minutes)65,535
      CMOD_COD C*1  Command mode codespace
      LOT_ID   C*n  Lot ID (customer specified)
      PART_TYP C*n  Part Type (or product ID)
      NODE_NAM C*n  Name of node that generated data
      TSTR_TYP C*n  Tester type
      JOB_NAM  C*n  Job name (test program name)
      JOB_REV  C*n  Job (test program) revision number        length byte = 0
      SBLOT_ID C*n  Sublot ID                                 length byte = 0
      OPER_NAM C*n  Operator name or ID (at setup time)       length byte = 0
      EXEC_TYP C*n  Tester executive software type            length byte = 0
      EXEC_VER C*n  Tester exec software version number       length byte = 0
      TEST_COD C*n  Test phase or step code                   length byte = 0
      TST_TEMP C*n  Test temperature                          length byte = 0
      USER_TXT C*n  Generic user text                         length byte = 0
      AUX_FILE C*n  Name of auxiliary data file               length byte = 0
      PKG_TYP  C*n  Package type                              length byte = 0
      FAMLY_ID C*n  Product family ID                         length byte = 0
      DATE_COD C*n  Date code                                 length byte = 0
      FACIL_ID C*n  Test facility ID                          length byte = 0
      FLOOR_ID C*n  Test floor ID                             length byte = 0
      PROC_ID  C*n  Fabrication process ID                    length byte = 0
      OPER_FRQ C*n  Operation frequency or step               length byte = 0
      TEST_COD      A user-defined field specifying the
                    phase or step in the device testing
                    process.
      TST_TEMP      The test temperature is an ASCII string.
                    Therefore, it can be stored as degrees
                    Celsius, Fahrenheit, Kelvin or whatever.
                    It can also be expressed in terms like
                    HOT, ROOM,and COLD if that is preferred.
      ======== ==== ========================================= ====================

    Frequency:
      Always required. One per data stream.

    Location:
      Immediately after the File Attributes Record (FAR) and the Audit Trail
      Records (ATR), if ATR's are used.

    Possible Use:
      Header information for all reports
    """
    typ = 1
    sub = 10
    fieldMap = (
        ('SETUP_T',  'U4', None),
        ('START_T',  'U4', None),
        ('STAT_NUM', 'U1', None),
        ('MODE_COD', 'C1', ' '),
        ('RTST_COD', 'C1', ' '),
        ('PROT_COD', 'C1', ' '),
        ('BURN_TIM', 'U2', 0xffff),
        ('CMOD_COD', 'C1', ' '),
        ('LOT_ID',   'Cn', None),
        ('PART_TYP', 'Cn', None),
        ('NODE_NAM', 'Cn', None),
        ('TSTR_TYP', 'Cn', None),
        ('JOB_NAM',  'Cn', None),
        ('JOB_REV',  'Cn', ''),
        ('SBLOT_ID', 'Cn', ''),
        ('OPER_NAM', 'Cn', ''),
        ('EXEC_TYP', 'Cn', ''),
        ('EXEC_VER', 'Cn', ''),
        ('TEST_COD', 'Cn', ''),
        ('TST_TEMP', 'Cn', ''),
        ('USER_TXT', 'Cn', ''),
        ('AUX_FILE', 'Cn', ''),
        ('PKG_TYP',  'Cn', ''),
        ('FAMLY_ID', 'Cn', ''),
        ('DATE_COD', 'Cn', ''),
        ('FACIL_ID', 'Cn', ''),
        ('FLOOR_ID', 'Cn', ''),
        ('PROC_ID',  'Cn', ''),
        ('OPER_FRQ', 'Cn', ''),
        ('SPEC_NAM', 'Cn', ''),
        ('SPEC_VER', 'Cn', ''),
        ('FLOW_ID',  'Cn', ''),
        ('SETUP_ID', 'Cn', ''),
        ('DSGN_REV', 'Cn', ''),
        ('ENG_ID',   'Cn', ''),
        ('ROM_COD',  'Cn', ''),
        ('SERL_NUM', 'Cn', ''),
        ('SUPR_NAM', 'Cn', '')
        )

@registerMe
class Mrr(RecordType):
    """
    **Master Results Record (MRR)**

    Function:
      The Master Results Record (MRR) is a logical extension of the Master
      Information Record (MIR). The data can be thought of as belonging
      with the MIR, but it is not available when the tester writes the MIR
      information. Each data stream must have exactly one MRR as the last
      record in the data stream.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (20)
      FINISH_T U*4  Date and time last part tested
      DISP_COD C*1  Lot disposition code                      space
      USR_DESC C*n  Lot description supplied by user          length byte = 0
      EXC_DESC C*n  Lot description supplied by exec          length byte = 0
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      DISP_COD:
        Supplied by the user to indicate the disposition of the lot of parts
        (or of the tester itself, in the case of checker or AEL data). The
        meaning of DISP_COD values are user-defined.  A valid value is an ASCII
        alphanumeric character (0 - 9 or A - Z). A space indicates a missing
        value.

    Frequency:
      Exactly one MRR required per data stream.

    Location:
      Must be the last record in the data stream.

    Possible Use:
      =========================     ============================
      Final Summary Sheet           Merged Summary Sheet
      Datalog                       Test Results Synopsis Report
      Wafer Map                     Trend Plot
      Histogram                     ADART
      Correlation                   RTBM
      Shmoo Plot                    User Data
      Repair Report
      =========================     ============================
    """
    typ = 1
    sub = 20
    fieldMap = (
        ('FINISH_T', 'U4', None),
        ('DISP_COD', 'C1', ' '),
        ('USR_DESC', 'Cn', ''),
        ('EXC_DESC', 'Cn', '')
        )

@registerMe
class Pcr(RecordType):
    """
    **Part Count Record (PCR)**

    Function:
      Contains the part count totals for one or all test sites. Each data stream
      must have at least one PCR to show the part count.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (30)
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      PART_CNT U*4  Number of parts tested
      RTST_CNT U*4  Number of parts retested                  4,294,967,295
      ABRT_CNT U*4  Number of aborts during testing           4,294,967,295
      GOOD_CNT U*4  Number of good (passed) parts tested      4,294,967,295
      FUNC_CNT U*4  Number of functional parts tested         4,294,967,295
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      HEAD_NUM:
        If this PCR contains a summary of the part counts for all test sites, this
        field must be set to 255.
      GOOD_CNT:
        A part is considered good when it is binned into one of the 'passing'
        hardware bins.
      FUNC_CNT:
        A part is considered functional when it is good enough to test, whether it
        passes or not. Parts that are incomplete or have shorts or opens are
        considered non-functional.

    Frequency:
      There must be at least one PCR in the file: either one summary PCR for all
      test sites (HEAD_NUM = 255), or one PCR for each head/site combination, or
      both.

    Location:
      Anywhere in the data stream after the initial sequence and before the MRR.
      When data is being recorded in real time, this record will usually appear
      near the end of the data stream.

    Possible Use:
      =========================  ==============================
      Final Summary Sheet        Merged Summary Sheet
      Site Summary Sheet         Report for Lot Tracking System
      =========================  ==============================
    """
    typ = 1
    sub = 30
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('PART_CNT', 'U4', None),
        ('RTST_CNT', 'U4', 0xffffffff),
        ('ABRT_CNT', 'U4', 0xffffffff),
        ('GOOD_CNT', 'U4', 0xffffffff),
        ('FUNC_CNT', 'U4', 0xffffffff)
        )

@registerMe
class Hbr(RecordType):
    """
    **Hardware Bin Record (HBR)**

    Function:
      Stores a count of the parts *physically* placed in a particular bin
      after testing. (In wafer testing, *physical* binning is not an actual
      transfer of the chip, but rather is represented by a drop of ink or an
      entry in a wafer map file.) This bin count can be for a single test
      site (when parallel testing) or a total for all test sites. The STDF
      specification also supports a Software Bin Record (SBR) for logical
      binning categories.  A part is *physically* placed in a hardware bin
      after testing. A part can be logically associated with a software bin
      during or after testing.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (40)
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      HBIN_NUM U*2  Hardware bin number
      HBIN_CNT U*4  Number of parts in bin
      HBIN_PF  C*1  Pass/fail indication                      space
      HBIN_NAM C*n  Name of hardware bin                      length byte = 0
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      HEAD_NUM:
        If this HBR contains a summary of the hardware bin counts for all test
        sites, this field must be set to 255.
      HBIN_NUM:
        Has legal values in the range 0 to 32767.
      HBIN_PF:
        This field indicates whether the hardware bin was a passing or failing
        bin. Valid values for this field are:

           * P = Passing bin
           * F = Failing bin
           * space = Unknown

    Frequency:
      One per hardware bin for each site. One per hardware bin for bin totals.
      May be included to name unused bins.

    Location:
      Anywhere in the data stream after the initial sequence and before the MRR.
      When data is being recorded in real time, this record usually appears near
      the end of the data stream.

    Possible Use:
      ===================== ==============================
      Final Summary Sheet   Merged Summary Sheet
      Site Summary Sheet    Report for Lot Tracking System
      ===================== ==============================
    """
    typ = 1
    sub = 40
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('HBIN_NUM', 'U2', None),
        ('HBIN_CNT', 'U4', None),
        ('HBIN_PF',  'C1', ' '),
        ('HBIN_NAM', 'Cn', '')
        )

@registerMe
class Sbr(RecordType):
    """
    **Software Bin Record (SBR)**

    Function:
      Stores a count of the parts associated with a particular logical
      bin after testing. This bin count can be for a single test site (when
      parallel testing) or a total for all test sites.  The STDF specification
      also supports a Hardware Bin Record (HBR) for actual physical binning. A
      part is *physically* placed in a hardware bin after testing. A part can
      be *logically* associated with a software bin during or after testing.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (50)
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      SBIN_NUM U*2  Software bin number
      SBIN_CNT U*4  Number of parts in bin
      SBIN_PF  C*1  Pass/fail indication                      space
      SBIN_NAM C*n  Name of software bin                      length byte = 0
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      HEAD_NUM:
        If this SBR contains a summary of the software bin counts for all test
        sites, this field must be set to 255.
      SBIN_NUM:
        Has legal values in the range 0 to 32767.
      SBIN_PF:
        This field indicates whether the software bin was a passing or failing
        bin. Valid values for this field are:

          * P = Passing bin
          * F = Failing bin
          * space = Unknown

    Frequency:
      One per software bin for each site. One per software bin for bin totals.
      Maybe included to name unused bins.

    Location:
      Anywhere in the data stream after the initial sequence and before the
      MRR. When data is being recorded in real time, this record usually appears
      near the end of the data stream.

    Possible Use:
      ===================== ================================
      Final Summary Sheet   Merged Summary Sheet
      Site Summary Sheet    Report for Lot Tracking System
      ===================== ================================
    """
    typ = 1
    sub = 50
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('SBIN_NUM', 'U2', None),
        ('SBIN_CNT', 'U4', None),
        ('SBIN_PF',  'C1', ' '),
        ('SBIN_NAM', 'Cn', '')
        )

@registerMe
class Pmr(RecordType):
    """
    **Pin Map Record (PMR)**

    Function:
      Provides indexing of tester channel names, and maps them to physical and
      logical pin names. Each PMR defines the information for a single channel/pin
      combination.

    Data Fields:
      ======== ==== ========================================= ====================
      Name     Type Description                               Missing/Invalid Flag
      ======== ==== ========================================= ====================
      REC_LEN  U*2  Bytes of data following header
      REC_TYP  U*1  Record type(1)
      REC_SUB  U*1  Record sub-type (60)
      PMR_INDX U*2  Unique index associated with pin
      CHAN_TYP U*2  Channel type                              0
      CHAN_NAM C*n  Channel namei                             length byte = 0
      PHY_NAM  C*n  Physical name of pin                      length byte = 0
      LOG_NAM  C*n  Logical name of pin                       length byte = 0
      HEAD_NUM U*1  Head number associated with channel       1
      SITE_NUM U*1  Site number associated with channel       1
      ======== ==== ========================================= ====================

    Notes on Specific Fields:
      PMR_INDX:
        This number is used to associate the channel and pin name information with
        data in the FTR or MPR. Reporting programs can then look up the PMR index
        and choose which of the three associated names they will use.
        The range of legalPMR indexes is 1 -32,767.
        The size of the FAIL_PIN and SPIN_MAP arrays in the FTR are directly
        proportional to the highest PMR index number. Therefore, it is important
        to start PMR indexes with a low number and use consecutive numbers if
        possible.
      CHAN_TYP:
        The channel type values are tester-specific. Please refer to the tester
        documentation for a list of the valid tester channel types and codes.
      HEAD_NUM:
        If a test system does not support parallel testing and does not have a
        standard way of
      SITE_NUM:
        identifying its single test site or head, these fields should be set to 1.
        If missing, the value of these fields will default to 1.

    Frequency:
      One per channel/pin combination used in the test program.
      Reuse of a PMR index number is not permitted.

    Location:
      After the initial sequence and before the first PGR, PLR, FTR,or MPR that
      uses this record's PMR_INDX value.

    Possible Use:
      * Functional Datalog
      * Functional Histogram
    """
    typ = 1
    sub = 60
    fieldMap = (
        ('PMR_INDX', 'U2', None),
        ('CHAN_TYP', 'U2', 0),
        ('CHAN_NAM', 'Cn', ''),
        ('PHY_NAM',  'Cn', ''),
        ('LOG_NAM',  'Cn', ''),
        ('HEAD_NUM', 'U1', 1),
        ('SITE_NUM', 'U1', 1)
        )

@registerMe
class Pgr(RecordType):
    """
    **Pin Group Record (PGR)**

    Function:
      Associates a name with a group of pins.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(1)
      REC_SUB  U*1   Record sub-type (62)
      GRP_INDX U*2   Unique index associated with pin group
      GRP_NAM  C*n   Name of pin group                        length byte = 0
      INDX_CNT U*2   Count (k)of PMR indexes
      PMR_INDX kxU*2 Array of indexes for pins in the group   INDX_CNT=0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      GRP_INDX:
        The range of legal group index numbers is 32,768 - 65,535.
      INDX_CNT, PMR_INDX:
        PMR_INDX is an array of PMR indexes whose length is defined by INDX_CNT.
        The order of the PMR indexes should be from most significant to least
        significant bit in the pin group (regardless of the order of PMR index
        numbers).

    Frequency:
      One per pin group defined in the test program.

    Location:
      After all the PMR's whose PMR index values are listed in the PMR_INDX array
      of this record, and before the first PLR that uses this record's GRP_INDX
      value.

    Possible Use:
      Functional Datalog
    """
    typ = 1
    sub = 62
    fieldMap = (
        ('GRP_INDX',   'U2', None),
        ('GRP_NAM',    'Cn', ''),
        ('INDX_CNT',   'U2', None),
        ('PMR_INDX', 'k2U2', [])
        )

@registerMe
class Plr(RecordType):
    """
    **Pin List Record (PLR)**

    Function:
      Defines the current display radix and operating mode for a pin or pin group.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(1)
      REC_SUB  U*1   Record sub-type (63)
      GRP_CNT  U*2   Count (k)of pins or pin groups
      GRP_INDX kxU*2 Array of pin or pin group indexes
      GRP_MODE kxU*2 Operating mode of pin group              0
      GRP_RADX kxU*1 Display radix of pin group0
      PGM_CHAR kxC*n Program state encoding characters        length byte = 0
      RTN_CHAR kxC*n Return state encoding characters         length byte = 0
      PGM_CHAL kxC*n Program state encoding characters        length byte = 0
      RTN_CHAL kxC*n Return state encoding characters         length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      GRP_CNT:
        GRP_CNT defines the number of pins or pin groups whose radix and mode are
        being defined. Therefore, it defines the size of each of the arrays that
        follow in the record.
        GRP_CNT must be greater than zero.
      GRP_MODE:
        The following are valid values for the pin group mode:
          * 00 = Unknown
          * 10 = Normal
          * 20 = SCIO (Same Cycle I/O)
          * 21 = SCIO Midband
          * 22 = SCIO Valid
          * 23 = SCIOWindowSustain
          * 30 = Dual drive (two drive bits per cycle)
          * 31 = Dual drive Midband
          * 32 = Dual drive Valid
          * 33 = Dual drive Window Sustain

        Unused pin group modes in the range of 1 through 32,767 are reserved for
        future use. Pin group modes 32,768 through 65,535 are available for
        customer use.
      GRP_RADX:
        The following are valid values for the pin group display radix:
          * 0 = Use display program default
          * 2 = Display in Binary
          * 8= Display in Octal
          * 10 = Display in Decimal
          * 16 = Display in Hexadecimal
          * 20 = Display as symbolic

      PGM_CHAR, PGM_CHAL:
        These ASCII characters are used to display the programmed state in
        the FTR or MPR. Use of these character arrays makes it possible to
        store tester-dependent display representations in a tester-independent
        format. If a single character is used to represent each programmed state,
        then only the PGM_CHAR array need be used. If two characters represent
        each state, then the first (left) character is stored in PGM_CHAL and
        the second (right) character is stored in PGM_CHAR .
      RTN_CHAR,RTN_CHAL:
        These ASCII characters are used to display the returned state in
        the FTR or MPR .Use of these character arrays makes it possible to
        store tester-dependent display representations in a tester-independent
        format. If a single character is used to represent each returned state,
        then only the RTN_CHAR array need be used. If two characters represent
        each state, then the first (left) character is stored in RTN_CHAL and
        the second (right) character is stored in RTN_CHAR .

    Note on Missing/Invalid Data Flags:
      For each field, the missing/invalid data flag applies to each member of
      the array, not to the array as a whole. Empty arrays (or empty members of
      arrays) can be omitted if they occur at the end of the record. Otherwise,
      each array must have the number of members indicated by GRP_CNT .You
      can then use the field's missing/invalid data flag to indicate which
      array members have no data. For example, if GRP_CNT =3, and if PGM_CHAL
      contains no data (but RTN_CHAL , which appears after PGM_CHAL, does),
      then PGM_CHAL should be an array of three missing/invalid data flags:
      0, 0, 0.

    Frequency:
      One or more whenever the usage of a pin or pin group changes in the test
      program.

    Location:
      After all the PMR's and PGR's whose PMR index values and pin group index
      values are listed in the GRP_INDX array of this record; and before the first
      FTR that references pins or pin groups whose modes are defined in this
      record.

    Possible Use:
      Functional Datalog
    """
    typ = 1
    sub = 63
    fieldMap = (
        ('GRP_CNT',    'U2', None),
        ('GRP_INDX', 'k0U2', None),
        ('GRP_MODE', 'k0U2', 0),
        ('GRP_RADX', 'k0U1', 0),
        ('PGM_CHAR', 'k0Cn', []),
        ('RTN_CHAR', 'k0Cn', []),
        ('PGM_CHAL', 'k0Cn', []),
        ('RTN_CHAL', 'k0Cn', [])
        )

@registerMe
class Rdr(RecordType):
    """
    **Retest Data Record (RDR)**

    Function:
      Signals that the data in this STDF file is for retested parts. The data in
      this record, combined with information in the MIR, tells data filtering
      programs what data to replace when processing retest data.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(1)
      REC_SUB  U*1   Record sub-type (70)
      NUM_BINS U*2   Number (k)ofbinsbeing retested
      RTST_BIN kxU*2 Array of retest bin numbers              NUM_BINS=0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      NUM_BINS,RTST_BIN:
        NUM_BINS indicates the number of hardware bins being retested and there
        fore the size of the RTST_BIN array that follows. If NUM_BINS is zero,
        then all bins in the lot are being retested and RTST_BIN is omitted.
        The LOT_ID, SUBLOT_ID, and TEST_COD of the current STDF file should match
        those of the STDF file that is being retested, so the data can be properly
        merged at a later time.

    Frequency:
      Optional. One per data stream.

    Location:
      If this record is used, it must appear immediately after the Master
      Information Record (MIR).

    Possible Use:
      Tells data filtering programs how to handle retest data.
    """
    typ = 1
    sub = 70
    fieldMap = (
        ('NUM_BINS',   'U2', None),
        ('RTST_BIN', 'k0U2', [])
        )

@registerMe
class Sdr(RecordType):
    """
    **Site Description Record (SDR)**

    Function:
      Contains the configuration information for one or more test sites, connected
      to one test head, that compose a site group.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(1)
      REC_SUB  U*1   Record sub-type (80)
      HEAD_NUM U*1   Test head number
      SITE_GRP U*1   Site group number
      SITE_CNT U*1   Number (k) of test sites in site group
      SITE_NUM kxU*1 Array of test site numbers
      HAND_TYP C*n   Handler or prober type                   length byte = 0
      HAND_ID  C*n   Handler or prober ID                     length byte = 0
      CARD_TYP C*n   Probe card type                          length byte = 0
      CARD_ID  C*n   Probecard ID                             length byte = 0
      LOAD_TYP C*n   Load board type                          length byte = 0
      LOAD_ID  C*n   Load board ID                            length byte = 0
      DIB_TYP  C*n   DIB board type                           length byte = 0
      DIB_ID   C*n   DIB board ID                             length byte = 0
      CABL_TYP C*n   Interface cable type                     length byte = 0
      CABL_ID  C*n   Interface cable ID                       length byte = 0
      CONT_TYP C*n   Handler contactor type                   length byte = 0
      CONT_ID  C*n   Handler contactor ID                     length byte = 0
      LASR_TYP C*n   Laser type                               length byte = 0
      LASR_ID  C*n   Laser ID                                 length byte = 0
      EXTR_TYP C*n   Extra equipment type field               length byte = 0
      EXTR_ID  C*n   Extra equipment ID                       length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      SITE_GRP:
        Specifies a site group number (called a station number on some
        testers) for the group of sites whose configuration is defined by this
        record. Note that this is different from the station number specified
        in theMIR, which refers to a software station only.  The value in this
        field must be unique within the STDF file.
      SITE_CNT, SITE_NUM
        SITE_CNT tells how many sites are in the site group that the current SDR
        configuration applies to. SITE_NUM is an array of those site numbers.
      _TYP fields:
        These are the type or model number of the interface or peripheral
        equipment being used for testing: HAND_TYP, CARD_TYP, LOAD_TYP, DIB_TYP,
        CABL_TYP, CONT_TYP, LASR_TYP, EXTR_TYP
      _ID fields:
        These are the IDs or serial numbers of the interface or peripheral
        equipment being used for testing: HAND_ID, CARD_ID, LOAD_ID, DIB_ID,
        CABL_ID, CONT_ID, LASR_ID, EXTR_ID

    Frequency:
      One for each site or group of sites that is differently configured.

    Location:
      Immediately after the MIR andRDR (if an RDR is used).

    Possible Use:
      Correlation of yield to interface or peripheral equipment
    """
    typ = 1
    sub = 80
    fieldMap = (
        ('HEAD_NUM',   'U1', None),
        ('SITE_GRP',   'U1', None),
        ('SITE_CNT',   'U1', None),
        ('SITE_NUM', 'k2U1', None),
        ('HAND_TYP',   'Cn', ''),
        ('HAND_ID',    'Cn', ''),
        ('CARD_TYP',   'Cn', ''),
        ('CARD_ID',    'Cn', ''),
        ('LOAD_TYP',   'Cn', ''),
        ('LOAD_ID',    'Cn', ''),
        ('DIB_TYP',    'Cn', ''),
        ('DIB_ID',     'Cn', ''),
        ('CABL_TYP',   'Cn', ''),
        ('CABL_ID',    'Cn', ''),
        ('CONT_TYP',   'Cn', ''),
        ('CONT_ID',    'Cn', ''),
        ('LASR_TYP',   'Cn', ''),
        ('LASR_ID',    'Cn', ''),
        ('EXTR_TYP',   'Cn', ''),
        ('EXTR_ID',    'Cn', '')
        )

@registerMe
class Psr(RecordType):
    """
    **Pattern Sequence Record (PSR)**

    Function:
      PSR record contains the information on the pattern profile for a specific
      executed scan test as part of the Test Identification information. In particular it
      implements the Test Pattern Map data object in the data model. It specifies
      how the patterns for that test were constructed. There will be a PSR record for
      each scan test in a test program. A PSR is referenced by the STR (Scan Test
      Record) using its PSR_INDX field

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      CONT_FLG B*1   Continuation PSR record exist; default 0
      PSR_INDX U*2   PSR Record Index (used by STR records)
      PSR_NAM  C*n   Symbolic name of PSR record length byte = 0
      OPT_FLG  B*1   Contains PAT_LBL, FILE_UID, ATPG_DSC,
                     and SRC_ID field missing flag bits and
                     flag for start index for first cycle number.
      TOTP_CNT U*2   Count of total pattern file information
                     sets in the complete PSR data set
      LOCP_CNT U*2   Count (k) of pattern file information
                     sets in this record
      PAT_BGN  kxU8  Array of Cycle #s patterns begins on
      PAT_END  kxU8  Array of Cycle #s patterns stops at
      PAT_FILE kxCn  Array of Pattern File Names
      PAT_LBL  K*Cn  Optional pattern symbolic name           OPT_FLG bit 0 = 1
      FILE_UID kxCn  Optional array of file identifier code   OPT_FLG bit 1 = 1
      ATPG_DSC kxCn  Optional array of ATPG information       OPT_FLG bit 2 = 1
      SRC_ID   kxCn  Optional array of PatternInSrcFileID     OPT_FLG bit 3 = 1
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
        CONT_FLG: This flag is used to indicated existence of continuation PSR records. If it
        is set to 1 then it mean a continuation PSR exists. A 0 value indicated that this is the last PSR record.

        PSR_INDX: This is a unique identifier for the set of PSRs that describe the patterns for a scan test.

        PSR_NAM: It is a symbolic name of the test suite to which this PSR belongs. For
        example with reference to figure 8, it would be stuck-at for the test_suite #1.

        OPT_FLG: This flag is used to indicate the presence of optional fields. The bit
        assignment for the optional fields in as shown in Table 3. If the bit is set to 1 the
        corresponding optional field is considered missing
            Optional Field Flags in PSR
            Bit Description
            0   Symbolic pattern label missing
            1   Unique File Identifier for the file is missing
            2   Details of ATPG used to create the patterns
            3   Identification of a pattern within a source file
            4   The first cycle number is determined by the value of this bit.
            5   The first pattern number is determined by the value of this bit (0 or 1)
            6   The bit position starts with the value of this bit

        TOTP_CNT: This field indicates the total number of pattern that make up a scan test
        over all the PSRs. The description of all the patterns may not fit into a single PSR as
        mention above. For continuation records this should be the same count as for the first
        record (i.e. the final total)

        LOCP_CNT: This field indicates the total number of patterns that are described in the
        current PSR from a scan test.

        NOTE 1 The next set of fields is repeated for each pattern that is contained in a scan test.
        Each of these fields is stored in its own array of size LOCAL_CNT.

        PAT_FILE : The name of the ATPG file from which the current pattern was created

        PAT_BGN: The cycle count the specified ATPG pattern begins on where the 1st cycle
        number is determined by the OPT_FLG (bit 4).

        PAT_END : The cycle count the specified ATPG pattern ends on.

        PAT_LBL: (Optional) This is a symbolic name of the pattern within a test suite. For
        example, with reference to figure 8 it will be P1 for the pattern coming from file1.

        FILE_UID: (Optional) - Unique character string that uniquely identifies the file. This
        field is provided as a means to additionally uniquely identify the source file. The exact
        mechanism to use this field is decided by the ATPG software, which will also provide
        this piece of information in the source files during the translation process.

        SRC_ID: (Optional) - The name of the specific PatternExec block in the source file. In
        case there are multiple patterns being specified in the source file e.g. multiple
        PatternExec blocks in STIL, this field specifies the one, which is the source of the pattern
        in this PSR

        ATPG_DSC (Optional) - This field intended to be used to store any ASCII data that can
        identify the source tool, time of generation etc.
    """
    typ = 1
    sub = 90
    fieldMap = (
        ('CONT_FLG',   'B1', None),
        ('PSR_INDX',   'U2', None),
        ('PSR_NAM',    'Cn', ''),
        ('OPT_FLG',    'B1', BN),
        ('TOTP_CNT',   'U2', None),
        ('LOCP_CNT',   'U2', None),
        ('PAT_BGN',  'k5U8', None),
        ('PAT_END',  'k5U8', None),
        ('PAT_FILE', 'k5Cn', None),
        ('PAT_LBL',  'k5Cn', ('OPT_FLG', B0)),
        ('FILE_UID', 'k5Cn', ('OPT_FLG', B1)),
        ('ATPG_DSC', 'k5Cn', ('OPT_FLG', B2)),
        ('SRC_ID',   'k5Cn', ('OPT_FLG', B3)),
        )

@registerMe
class Nmr(RecordType):
    """
    **Name Map Record (NMR)**

    Function:
        This record contains a map of PMR indexes to ATPG signal names. This
        record is designed to allow preservation of ATPG signal names used in the
        ATPG files through the datalog output. This record is only required when the
        standard PMR records do not contain the ATPG signal name

    Data Fields:
        ======== ===== ======================================== ====================
        Name     Type  Description                              Missing/Invalid Flag
        ======== ===== ======================================== ====================
        CONT_FLG B*1   Continuation PSR record exist; default 0
        NMR_INDX U*2   NMR record unique index
        TOTM_CNT U*2   Count of PMR indexes and ATPG_NAM entries 0
        LOCM_CNT U*2   Count of (k) PMR indexes and ATPG_NAM
                       entries in this record                    0
        PMR_INDX kxU*2 Array of PMR indexes                      LOCM_CNT=0
        ATPG_NAM kxC*n Array of ATPG signal names                LOCM_CNT=0
        ======== ===== ======================================== ====================

    Notes on Specific Fields:
        NMR_INDX: This is a unique identifier for one for each NMR record. A set of NMR
            records can be defined multiple mapping from pin names to ATPG names. The particular
            mapping used by a test can identified by referencing the corresponding NMR its
        NMR_INDX in the STR field. NMR_INDX values start at 1.
        TOTM_CNT: This the count of total number of entries in the mapping table across all
            the NMR records
        LOCM_CNT: The count of number of entries in the current NMR record.
        PMR_INDX: It is the array of PMR indexes for which the ATPG names are provided
        ATPG_NAM: It is the array ATPG signal names corresponding to the pin in
            PMR_INDX array.
    """
    typ = 1
    sub = 91
    fieldMap = (
        ('CONT_FLG',   'B1', None),
        ('NMR_INDX',   'U2', None),
        ('TOTM_CNT',   'U2', 0),
        ('LOCM_CNT',   'U2', 0),
        ('PMR_INDX', 'k3U2', []),
        ('ATPG_NAM', 'k3Cn', []),
        )

@registerMe
class Cnr(RecordType):
    """
    **Scan Cell Name Record (CNR)**

    Function:
        This record is used to store the mapping from Chain and Bit position to the
        Cell/FlipFlop name. A CNR record should be created for each Cell for which
        a name mapping is required. Typical usage would be to create a record for
        each failing cell/FlipFlop. A CNR with new mapping for a chain and bit
        position would override the previous mapping.

    Data Fields:
        ======== ===== ======================================== ====================
        Name     Type  Description                              Missing/Invalid Flag
        ======== ===== ======================================== ====================
        CHN_NUM  U*2   Chain number. Referenced by the
                       CHN_NUM array in an STR record
        BIT_POS  U*4   Bit position in the chain
        CELL_NAM S*n   Scan Cell Name
        ======== ===== ======================================== ====================

    Notes on Specific Fields:
        CHN_NUM: This is the array for the chain identification for the target Flip Flop for
            which the name is provided in the table.
        BIT_POS: This is an array for the bit position within the chain identified by the
            CHAIN_NO field for the target Flip Flop for which the name is provided in the table.
        CELL_NAM: The is name of the of Flip Flop at the CHN_NUM and BIT_POS. Please
            note the type of this field is S*n where the length of the Flip Flop name is stored in the
            first two bytes and then the name follows.
    """
    typ = 1
    sub = 92
    fieldMap = (
        ('CHN_NUM',  'U2', None),
        ('BIT_POS',  'U4', None),
        ('CELL_NAM', 'Sn', None),
        )

@registerMe
class Ssr(RecordType):
    """
    **Scan Structure Record (SSR)**

    Function:
        This record contains the Scan Structure information normally found in a STIL
        file. The SSR is a top level Scan Structure record that contains an array of
        indexes to CDR (Chain Description Record) records which contain the chain
        information.

    Data Fields:
        ======== ===== ======================================== ====================
        Name     Type  Description                              Missing/Invalid Flag
        ======== ===== ======================================== ====================
        SSR_NAM  C*n   Name of the STIL Scan Structure for reference    Length byte = 0
        CHN_CNT  U*2   Count (k) of number of Chains listed in CHN_LIST
        CHN_LIST kxU*2 Array of CDR Indexes
        ======== ===== ======================================== ====================

    Notes on Specific Fields:
        SSR_NAM: This is a ASCII unique name for the scan structure record that is normally
            provided by the STIL (IEEE 1450) file.
        CHN_CNT: It is the count of number of scan chains in a scan structure.
        CHN_LIST: It is an array of index of each chain that is part of this scan structure. No
            particular order of the scan chain indexes is specified by the standard.
    """
    typ = 1
    sub = 93
    fieldMap = (
        ('SSR_NAM',    'Cn', ''),
        ('CHN_CNT',    'U2', None),
        ('CHN_LIST', 'k1U2', None),
        )

@registerMe
class Cdr(RecordType):
    """
    **Chain Description Record (CDR)**

    Function:
        This record contains the description of a scan chain in terms of its input,
        output, number of cell and clocks. Each CDR record contains description of
        exactly one scan chain. Each CDR is uniquely identified by an index.

    Data Fields:
        ======== ===== ======================================== ====================
        Name     Type  Description                              Missing/Invalid Flag
        ======== ===== ======================================== ====================
        CONT_FLG B*1   Continuation CDR record follows if not 0
        CDR_INDX U*2   SCR Index
        CHN_NAM  C*n   Chain Name Length byte = 0
        CHN_LEN  U*4   Chain Length (# of scan cells in chain)
        SIN_PIN  U*2   PMR index of the chain's Scan In Signal      0
        SOUT_PIN U*2   PMR index of the chain's Scan Out Signal     0
        MSTR_CNT U*1   Count (m) of master clock pins
                       specified for this scan chain
        M_CLKS   mxU*2 Array of PMR indexes for the master
                       clocks assigned to this chain                MSTR_CNT=0
        SLAV_CNT U*1   Count (n) of slave clock pins specified
                       for this scan chain
        S_CLKS   nxU*2 Array of PMR indexes for the slave
                       clocks assigned to this chain                SLAV_CNT=0
        INV_VAL  U*1   0: No Inversion, 1: Inversion 255
        LST_CNT  U*2   Count (k) of scan cells listed in this record
        CELL_LST kxS*n Array of Scan Cell Names LST_CNT=0
        ======== ===== ======================================== ====================

    Notes on Specific Fields:
        CDR_INDX: This is a unique number assigned to each CDR. It is used by the SSR
            record to reference a particular CDR.
        CHN_NAM: This is an optional ASCII unique name for the scan chain (user
            defined or derived/copied from ATPG files).
        TOTS_CNT: The number of scan cells contained within the scan chain
        LOCS_CNT: The number of scan cells listed in this record (the others are listed in continuation SCR records)
        SIN_PIN: The PMR record index for the chain's Scan In signal
        SOUT_PIN: The PMR record index for the chain's Scan Out signal
        MSTR_CNT: The # of master clock pins assigned to the scan chain
        SLAV_CNT: The # of slave clock pins assigned to the scan chain
        M_CLKS: An optional array of PMR indexes for the chain's master clock pins
            The length of this array is specified in the MSTR_CNT field
        S_CLKS: An optional array of PMR indexes for the chain's slave clock pins
            The length of this array is specified in the SLAV_CNT field.
        INV_VAL: A Boolean value to indicate if the Scan_Out signal is inverted from the
            Scan_In signal. A 0 value indicated no inversion. A value of 255 indicates unknown status.
        CELL_LST: The array of scan cell names.
    """
    typ = 1
    sub = 94
    fieldMap = (
        ('CONT_FLG',    'B1', None),
        ('CDR_INDX',    'U2', None),
        ('CHN_NAM',     'Cn', ''),
        ('CHN_LEN',     'U2', None),
        ('SIN_PIN',     'U2', 0),
        ('SOUT_PIN',    'U2', 0),
        ('MSTR_CNT',    'U1', None),
        ('M_CLKS',    'k6U2', []),
        ('SLAV_CNT',    'U1', None),
        ('S_CLKS',    'k8U2', []),
        ('INV_VAL',     'U1', 0xff),
        ('LST_CNT',     'U2', None),
        ('CELL_LST', 'k11Sn', []),
        )

@registerMe
class Wir(RecordType):
    """
    **Wafer Information Record (WIR)**

    Function:
      Acts mainly as a marker to indicate where testing of a particular wafer
      begins for each wafer tested by the job plan. The WIR and the Wafer
      Results Record (WRR) bracket all the stored information pertaining
      to one tested wafer. This record is used only when testing at wafer
      probe. AWIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(2)
      REC_SUB  U*1   Record sub-type (10)
      HEAD_NUM U*1   Test head number
      SITE_GRP U*1   Site group number                        255
      START_T  U*4   Date and time first part tested
      WAFER_ID C*n   Wafer ID                                 length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      SITE_GRP:
        Refers to the site group in the SDR. This is a means of relating the wafer
        information to the configuration of the equipment used to test it. If
        this information is not known, or the tester does not support the
        concept of site groups, this field should be set to 255.
      WAFER_ID:
        Is optional, but is strongly recommended in order to make the resultant
        data files as useful as possible.

    Frequency:
      One per wafer tested.

    Location:
      Anywhere in the data stream after the initial sequence and before the MRR.
      Sent before testing each wafer.

    Possible Use:
      * Wafer Summary Sheet
      * Datalog
      * Wafer Map
    """
    typ = 2
    sub = 10
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_GRP', 'U1', 0xff),
        ('START_T',  'U4', None),
        ('WAFER_ID', 'Cn', '')
        )

@registerMe
class Wrr(RecordType):
    """
    **Wafer Results Record (WRR)**

    Function:
      Contains the result information relating to each wafer tested by the
      job plan. The WRR and the Wafer Information Record (WIR) bracket all
      the stored information pertaining to one tested wafer. This record is
      used only when testing at wafer probe time. A WIR/WRR pair will have
      the same HEAD_NUM and SITE_GRP values.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(2)
      REC_SUB  U*1   Record sub-type (20)
      HEAD_NUM U*1   Test head number
      SITE_GRP U*1   Site group number                        255
      FINISH_T U*4   Date and time last part tested
      PART_CNT U*4   Number of parts tested
      RTST_CNT U*4   Number of parts retested                 4,294,967,295
      ABRT_CNT U*4   Number of aborts during testing          4,294,967,295
      GOOD_CNT U*4   Number of good (passed) parts tested     4,294,967,295
      FUNC_CNT U*4   Number of functional parts tested        4,294,967,295
      WAFER_ID C*n   Wafer ID                                 length byte = 0
      FABWF_ID C*n   Fab wafer ID                             length byte = 0
      FRAME_ID C*n   Wafer frame ID                           length byte = 0
      MASK_ID  C*n   Wafer mask ID                            length byte = 0
      USR_DESC C*n   Wafer description supplied by user       length byte = 0
      EXC_DESC C*n   Wafer description supplied by exec       length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      SITE_GRP:
        Refers to the site group in the SDR .This is a means of relating the
        wafer information to the configuration of the equipment used to test
        it. If this information is not known, or the tester does not support
        the concept of site groups, this field should be set to 255.
    WAFER_ID:
      Is optional, but is strongly recommended in order to make the resultant
      data files as useful as possible. A Wafer ID in the WRR supersedes any
      Wafer ID found in the WIR.
    FABWF_ID:
      Is the ID of the wafer when it was in the fabrication process. This
      facilitates tracking of wafers and correlation of yield with fabrication
      variations.
    FRAME_ID:
      Facilitates tracking of wafers once the wafer has been through the saw
      step and the wafer ID is no longer readable on the wafer itself. This
      is an important piece of information for implementing an inkless
      binning scheme.

    Frequency:
      One per wafer tested.

    Location:
      Anywhere in the data stream after the corresponding WIR.
      Sent after testing each wafer.

    Possible Use:
      * Wafer Summary Sheet
      * Datalog
      * Wafer Map
    """
    typ = 2
    sub = 20
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_GRP', 'U1', 0xff),
        ('FINISH_T', 'U4', None),
        ('PART_CNT', 'U4', None),
        ('RTST_CNT', 'U4', 0xffffffff),
        ('ABRT_CNT', 'U4', 0xffffffff),
        ('GOOD_CNT', 'U4', 0xffffffff),
        ('FUNC_CNT', 'U4', 0xffffffff),
        ('WAFER_ID', 'Cn', ''),
        ('FABWF_ID', 'Cn', ''),
        ('FRAME_ID', 'Cn', ''),
        ('MASK_ID',  'Cn', ''),
        ('USR_DESC', 'Cn', ''),
        ('EXC_DESC', 'Cn', '')
        )

@registerMe
class Wcr(RecordType):
    """
    **Wafer Configuration Record (WCR)**

    Function:
    Contains the configuration information for the wafers tested by the job
    plan. The WCR provides the dimensions and orientation information for
    all wafers and dice in the lot. This record is used only when testing
    at wafer probe time.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(2)
      REC_SUB  U*1   Record sub-type (30)
      WAFR_SIZ R*4   Diameter of wafer in WF_UNITS            0
      DIE_HT   R*4   Height of die in WF_UNITS                0
      DIE_WID  R*4   Width of die in WF_UNITS                 0
      WF_UNITS U*1   Units for wafer and die dimensions       0
      WF_FLAT  C*1   Orientation of wafer flat                space
      CENTER_X I*2   X coordinate of center die on wafer      -32768
      CENTER_Y I*2   Y coordinate of center die on wafer      -32768
      POS_X    C*1   Positive X direction of wafer            space
      POS_Y    C*1   Positive Y direction of wafer            space
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      WF_UNITS:
        Has these valid values:
          * 0 = Unknown units
          * 1 = Units are in inches
          * 2 = Units are in centimeters
          * 3 = Units are in millimeters
          * 4 = Units are in mils
      WF_FLAT:
        Has these valid values:
          * U=Up
          * D=Down
          * L=Left
          * R=Right
          * space = Unknown
      CENTER_X, CENTER_Y:
        Use the value -32768 to indicate that the field is invalid.
    """
    typ = 2
    sub = 30
    fieldMap = (
        ('WAFR_SIZ', 'R4', 0),
        ('DIE_HT',   'R4', 0),
        ('DIE_WID',  'R4', 0),
        ('WF_UNITS', 'U1', 0),
        ('WF_FLAT',  'C1', ' '),
        ('CENTER_X', 'I2', -32768),
        ('CENTER_Y', 'I2', -32768),
        ('POS_X',    'C1', ' '),
        ('POS_Y',    'C1', ' ')
        )

@registerMe
class Pir(RecordType):
    """
    **Part Information Record (PIR)**

    Function:
      Acts as a marker to indicate where testing of a particular part begins
      for each part tested by the test program. The PIR and the Part ResultsRecord
      (PRR) bracket all the stored information pertaining to one tested part.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(5)
      REC_SUB  U*1   Record sub-type (10)
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      HEAD_NUM,SITE_NUM:
        If a test system does not support parallel testing, and does not have
        a standard way to identify its single test site or head, then these
        fields should be set to 1.  When parallel testing, these fields are
        used to associate individual datalogged results (FTR's and PTR's) with
        a PIR/PRR pair. An FTR or PTR belongs to the PIR/PRR pair having the
        same values for HEAD_NUM and SITE_NUM.

    Frequency:
      One per part tested.

    Location:
      Anywhere in the data stream after the initial sequence, and before the
      corresponding  PRR .
      Sent before testing each part.

    Possible Use:
      Datalog
    """
    typ = 5
    sub = 10
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None)
        )

@registerMe
class Prr(RecordType):
    """
    **Part Results Record (PRR)**

    Function:
      Contains the result information relating to each part tested by the
      test program. The PRR and the Part Information Record (PIR) bracket
      all the stored information pertaining to one tested part.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(5)
      REC_SUB  U*1   Record sub-type (20)
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      PART_FLG B*1   Part information flag
      NUM_TEST U*2   Number of tests executed
      HARD_BIN U*2   Hardware bin number
      SOFT_BIN U*2   Software bin number                      65535
      X_COORD  I*2   (Wafer) X coordinate                     -32768
      Y_COORD  I*2   (Wafer) Y coordinate                     -32768
      TEST_T   U*4   Elapsed test time in milliseconds        0
      PART_ID  C*n   Part identification                      length byte = 0
      PART_TXT C*n   Part description text                    length byte = 0
      PART_FIX B*n   Part repair information                  length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      HEAD_NUM, SITE_NUM:
        If a test system does not support parallel testing, and does not have
        a standard way to identify its single test site or head, then these
        fields should be set to 1.  When parallel testing, these fields are
        used to associate individual datalogged results (FTR's an dPTR's) with
        a PIR/PRR pair. An FTR or PTR belongs to the PIR/PRR pair having the
        same values for HEAD_NUM and SITE_NUM.
      X_COORD, Y_COORD:
        Have legal values in the range -32767 to 32767. A missing value is
        indicated by the value -32768.
      X_COORD, Y_COORD, PART_ID:
        Are all optional, but you should provide either the PART_ID or the X_COORD
        and Y_COORD in order to make the resultant data use ful for analysis.
      PART_FLG:
        Contains the following fields:

          * bit 0:

            * 0 = This is a new part. Its data device does not supersede that of
              any previous device.
            * 1 = The PIR, PTR, MPR, FTR, and PRR records that make up the current
              sequence (identified as having the same HEAD_NUM and SITE_NUM)
              supersede any previous sequence of records with the same PART_ID.(A
              repeated part sequence usually indicates a mistested part.)
          * bit 1:

            * 0 = This is a new part. Its data device does not supersede that of
              any previous device.
            * 1 = The PIR, PTR, MPR, FTR, and PRR records that make up the current
              sequence (identified as having the same HEAD_NUM and SITE_NUM)
              supersede any previous sequence of records with the same X_COORD and
              Y_COORD.(A repeated part sequence usually indicates a mistested
              part.)

          Note:
            Either Bit 0 or Bit 1 can be set, but not both. (It is also valid to
            have neither set.)

          * bit2:

            * 0 = Part testing completed normally
            * 1 = Abnormal end of testing

          * bit3:

            * 0 = Part passed
            * 1 = Part failed

          * bit 4:

            * 0 = Pass/fail flag (bit 3) is valid
            * 1 = Device completed testing with no pass/fail indication
              (i.e., bit 3 is invalid)

          * bits 5 - 7:

            Reserved for future use  must be 0

      HARD_BIN:
        Has legal values in the range 0 to 32767.
      SOFT_BIN:
        Has legal values in the range 0 to 32767. A missing value is indicated
        by the value 65535.
      PART_FIX:
        This is an application-specific field for storing device repair
        information. It may be used for bit-encoded, integer, floating point,
        or character information. Regardless of the information stored, the
        first byte must contain the number of bytes to follow. This field can
        be decoded only by an application-specific analysis program.

    Frequency:
      One per part tested.

    Location:
      Anywhere in the data stream after the corresponding PIR and before the MRR.
      Sent after completion of testing each part.

    Possible Use:
      * Datalog
      * Wafer map
      * RTBM
      * Shmoo Plot
      * Repair Data
    """
    typ = 5
    sub = 20
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('PART_FLG', 'B1', None),
        ('NUM_TEST', 'U2', None),
        ('HARD_BIN', 'U2', None),
        ('SOFT_BIN', 'U2', 0xffff),
        ('X_COORD',  'I2', -32768),
        ('Y_COORD',  'I2', -32768),
        ('TEST_T',   'U4', 0),
        ('PART_ID',  'Cn', ''),
        ('PART_TXT', 'Cn', ''),
        ('PART_FIX', 'Bn', [])
        )

@registerMe
class Tsr(RecordType):
    """
    **Test Synopsis Record (TSR)**

    Function:
      Contains the test execution and failure counts for one parametric or
      functional test in the test program. Also contains static information,
      such as test name. The TSR is related to the Functional Test Record
      (FTR), the Parametric Test Record (PTR), and the Multiple Parametric
      Test Record (MPR) by test number, head number, and site number.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(10)
      REC_SUB  U*1   Record sub-type (30)
      HEAD_NUM U*1   Test head number                         See note
      SITE_NUM U*1   Test site number
      TEST_TYP C*1   Test type                                space
      TEST_NUM U*4   Test number
      EXEC_CNT U*4   Number of test executions                4,294,967,295
      FAIL_CNT U*4   Number of test failures                  4,294,967,295
      ALRM_CNT U*4   Number of alarmed tests                  4,294,967,295
      TEST_NAM C*n   Test name                                length byte = 0
      SEQ_NAME C*n   Sequencer (program segment/flow) name    length byte = 0
      TEST_LBL C*n   Test label or text                       length byte = 0
      OPT_FLAG B*1   Optional data flag                       See note
      TEST_TIM R*4   Average test execution time in seconds   OPT_FLAG bit 2 = 1
      TEST_MIN R*4   Lowest test result value                 OPT_FLAG bit 0 = 1
      TEST_MAX R*4   Highest test result value                OPT_FLAG bit 1 = 1
      TST_SUMS R*4   Sum of test result values                OPT_FLAG bit 4 = 1
      TST_SQRS R*4   Sum of squares of test result values     OPT_FLAG bit 5 = 1
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      HEAD_NUM:
        If this TSR contains a summary of the test counts for all test sites,
        this field must be set to 255.
      TEST_TYP:
        Indicates what type of test this summary data is for. Valid values are:
          * P = Parametric test
          * F = Functional test
          * M = Multiple-result parametric test
          * space = Unknown
    EXEC_CNT,FAIL_CNT, ALRM_CNT:
      Are optional, but are strongly recommended because they are needed to
      compute, values for complete final summary sheets.
    OPT_FLAG:
      Contains the following fields:
        * bit 0 set = TEST_MIN value is invalid
        * bit 1 set = TEST_MAX value is invalid
        * bit 2 set = TEST_TIM value is invalid
        * bit 3 is reserved for future use and must be 1
        * bit 4 set = TST_SUMS value is invalid
        * bit 5 set = TST_SQRS value is invalid
        * bits 6 - 7 are reserved for future use and must be 1
      OPT_FLAG is optional if it is the last field in the record.

    TST_SUMS, TST_SQRS:
      Are useful incalculating the mean and standard deviationfor a single lot or
      when combining test data from multiple STDF files.

    Frequency:
      One for each test executed in the test program.
      May optionally be used to identify unexecuted tests.

    Location:
      Anywhere in the data stream after the initial sequence and before the MRR.
      When test data is being generated in real-time, these records will appear
      after the last PRR.

    Possible Use:
      ======================  ======================
      Final Summary Sheet     Datalog
      Merged Summary Sheet    Histogram
      Wafer Map               Functional Histogram
      ======================  ======================
    """
    typ = 10
    sub = 30
    fieldMap = (
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('TEST_TYP', 'C1', ' '),
        ('TEST_NUM', 'U4', None),
        ('EXEC_CNT', 'U4', 0xffffffff),
        ('FAIL_CNT', 'U4', 0xffffffff),
        ('ALRM_CNT', 'U4', 0xffffffff),
        ('TEST_NAM', 'Cn', ''),
        ('SEQ_NAME', 'Cn', ''),
        ('TEST_LBL', 'Cn', ''),
        ('OPT_FLAG', 'B1', BN),
        ('TEST_TIM', 'R4', ('OPT_FLAG', B2)),
        ('TEST_MIN', 'R4', ('OPT_FLAG', B0)),
        ('TEST_MAX', 'R4', ('OPT_FLAG', B1)),
        ('TST_SUMS', 'R4', ('OPT_FLAG', B4)),
        ('TST_SQRS', 'R4', ('OPT_FLAG', B5))
        )
        
@registerMe
class Ptr(RecordType):
    """
    **Parametric Test Record (PTR)**

    Function:
      Contains the results of a single execution of a parametric test in the
      test program. The first occurrence of this record also establishes
      the default values for all semi-static information about the test,
      such as limits, units, and scaling. The PTR is related to the Test
      Synopsis Record (TSR) by test number, head number, and site number.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(15)
      REC_SUB  U*1   Record sub-type (10)
      TEST_NUM U*4   Test number
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      TEST_FLG B*1   Test flags (fail, alarm, etc.)
      PARM_FLG B*1   Parametric test flags (drift, etc.)
      RESULT   R*4   Test result                              TEST_FLG bit 1 = 1
      TEST_TXT C*n   Test description text or label           length byte = 0
      ALARM_ID C*n   Name of alarm                            length byte = 0
      OPT_FLAG B*1   Optional data flag                       See note
      RES_SCAL I*1   Test results scaling exponent            OPT_FLAG bit 0 = 1
      LLM_SCAL I*1   Low limit scaling exponent               OPT_FLAG bit 4or6=1
      HLM_SCAL I*1   High limit scaling exponent              OPT_FLAG bit 5or7=1
      LO_LIMIT R*4   Low test limit value                     OPT_FLAG bit 4or6=1
      HI_LIMIT R*4   High test limit value                    OPT_FLAG bit 5or7=1
      UNITS    C*n   Test units                               length byte = 0
      C_RESFMT C*n   ANSI Cresultformatstring                 length byte = 0
      C_LLMFMT C*n   ANSI C low limit format string           length byte = 0
      C_HLMFMT C*n   ANSI C high limit format string          length byte = 0
      LO_SPEC  R*4   Low specification limit value            OPT_FLAG bit 2 = 1
      HI_SPEC  R*4   High specification limit value           OPT_FLAG bit 3 = 1
      ======== ===== ======================================== ====================

    Notes on Specific Fields:

    Default Data:
      All data following the OPT_FLAG field has a special function in the STDF
      file. The first PTR for each test will have these fields filled in. These
      values will be the default for each subsequent PTR with the same test
      number: if a subsequent PTR has a value for one of these fields, it will
      be used instead of the default, for that one record only; if the field
      is blank, the default will be used. This method replaces use of the PDR
      in STDF V3.  If the PTR is not associated with a test execution (that
      is, it contains only default information), bit 4 of the TEST_FLG field
      must be set, and the PARM_FLG field must be zero.  Unless the default
      is being overridden, the default data fields should be omitted in order
      to save space in the file.  Note that RES_SCAL, LLM_SCAL, HLM_SCAL,
      UNITS, C_RESFMT, C_LLMFMT, and C_HLMFMT are interdependent. If you
      are overriding the default value of one, make sure that you also make
      appropriate changes to the others in order to keep them consistent.
      For character strings, you can override the default with a null value
      by setting the string length to 1 and the string itself to a single
      binary 0.
    HEAD_NUM, SITE_NUM:
      If a test system does not support parallel testing, and does not have a
      standard way of identifying its single test site or head, these fields
      should be set to 1.  When parallel testing, these fields are used to
      associate individual datalogged results with a PIR/PRR pair. APTR belongs
      to the PIR/PRR pair having the same values for HEAD_NUM and SITE_NUM.

    TEST_FLG:
      Contains the following fields:

        * bit 0

          * 0 = No alarm
          * 1 = Alarm detected during testing

        * bit 1

          * 0 = The value in the RESULT field is valid (see note on RESULT )
          * 1 = The value in the RESULT field is not valid. This setting
            indicates that the test was executed, but no datalogged value was
            taken. You should read bits 6 and 7 of TEST_FLG to determine if the
            test passed or failed.

        * bit2

          * 0 = Test result is reliable
          * 1 = Test result is unreliable

        * bit 3

          * 0 = No timeout
          * 1 = Timeout occurred

        * bit 4

          * 0 = Test was executed
          * 1 = Test not executed

        * bit 5

          * 0 = No abort
          * 1 = Test aborted

        * bit 6

          * 0 = Pass/fail flag (bit 7) is valid
          * 1 = Test completed with no pass/fail indication

        * bit 7

          * 0 = Test passed
          * 1 = Test failed

    PARM_FLG:
      Is the parametric flag field, and contains the following bits:
        * bit 0

          * 0 = No scale error
          * 1 = Scale error

        * bit 1

          * 0 = No drift error
          * 1 = Drift error (unstable measurement)

        * bit 2

          * 0 = No oscillation
          * 1 = Oscillation detected

        * bit 3

          * 0 = Measured value not high
          * 1 = Measured value higher than high test limit

        * bit 4

          * 0 = Measured value not low
          * 1 = Measured value lower than low test limit

        * bit 5

          * 0 = Test failed or test passed standard limits
          * 1 = Test passed alternate limits

        * bit 6

          * 0 = If result = low limit, then result is *fail.*
          * 1 = If result = low limit, then result is *pass.*

        * bit 7

          * 0 = If result = high limit, then result is *fail.*
          * 1 = If result = high limit, then result is *pass.*

    RESULT:
      The RESULT value is considered useful only if all the following bits from
      TEST_FLG and PARM_FLG are 0:

        * TEST_FLG

          * bit 0 = 0 no alarm
          * bit 1 = 0 value in result field is valid
          * bit 2 = 0 test result is reliable
          * bit 3 = 0 no timeout
          * bit 4 = 0 test was executed
          * bit 5 = 0 no abort

        * PARM_FLG

          * bit 0 = 0 no scale error
          * bit 1 = 0 no drifterror
          * bit 2 = 0 no oscillation

      If any one of these bits is 1, then the PTR result should not be used.

    ALARM_ID:
      If the alarm flag (bit 0 of TEST_FLG ) is set, this field can contain
      the name or ID of the alarms that were triggered. Alarm names are
      tester-dependent.

    OPT_FLAG:
      Is the Optional data flag and contains the following bits:

        * bit 0 set = RES_SCAL value is invalid. The default set by the first PTR
          with this test number will be used.
        * bit 1 reserved for future used and must be 1.
        * bit 2 set = No low specification limit.
        * bit 3 set = No high specification limit.
        * bit 4 set = LO_LIMIT and LLM_SCAL are invalid. The default values set
          for these fields in the first PTR with this test number will be used.
        * bit 5 set = HI_LIMIT and HLM_SCAL are invalid. The default values set
          for these fields in the first PTR with this test number will be used.
        * bit 6 set = No Low Limit for this test (LO_LIMIT and LLM_SCAL are
          invalid).
        * bit7 set = No High Limit for this test (HI_LIMIT and HLM_SCAL
          are invalid).

      The OPT_FLAG field may be omitted if it is the last field in the record.

    C_RESFMT, C_LLMFMT, C_HLMFMT:
      ANSI C format strings for use in formatting the test result and low
      and high limits ,(both test and spec). For example, *%7.2*.Tf he format
      string is also known as an output specification string, as used with the
      printf statement. See any ANSI C reference man, or the man page on printf

    LO_SPEC, HI_SPEC:
      The specification limits are set in the first PTR and should never
      change. They use the same scaling and format strings as the corresponding
      test limits.

    Frequency:
      One per parametric test execution.

    Location:
      Under normal circumstances, the PTR can appear anywhere in the data
      stream after the corresponding Part Information Record (PIR) and before
      the corresponding Part Result Record (PRR).  In addition, to facilitate
      conversion from STDF V3, if the first PTR for a test contains default
      information only (no test results), it may appear anywhere after the
      initial sequence, and before the first corresponding PTR , but need
      not appear between a PIR and PRR.

    Possible Use:
      * Datalog
      * Histogram
      * Wafer Map
    """
    typ = 15
    sub = 10
    fieldMap = (
        ('TEST_NUM', 'U4', None),
        ('HEAD_NUM', 'U1', None),
        ('SITE_NUM', 'U1', None),
        ('TEST_FLG', 'B1', BN),
        ('PARM_FLG', 'B1', None),
        ('RESULT',   'R4', ('TEST_FLG', B1)),
        ('TEST_TXT', 'Cn', ''),
        ('ALARM_ID', 'Cn', ''),
        ('OPT_FLAG', 'B1', BN),
        ('RES_SCAL', 'I1', ('OPT_FLAG', B0)),
        ('LLM_SCAL', 'I1', ('OPT_FLAG', B4 & B6)),
        ('HLM_SCAL', 'I1', ('OPT_FLAG', B5 & B7)),
        ('LO_LIMIT', 'R4', ('OPT_FLAG', B4 & B6)),
        ('HI_LIMIT', 'R4', ('OPT_FLAG', B5 & B7)),
        ('UNITS',    'Cn', ''),
        ('C_RESFMT', 'Cn', ''),
        ('C_LLMFMT', 'Cn', ''),
        ('C_HLMFMT', 'Cn', ''),
        ('LO_SPEC',  'R4', ('OPT_FLAG', B2)),
        ('HI_SPEC',  'R4', ('OPT_FLAG', B3))
        )

@registerMe
class Mpr(RecordType):
    """
    **Multiple-Result Parametric Record (MPR)**

    Function:
      Contains the results of a single execution of a parametric test in
      the test program where that test returns multiple values. The first
      occurrence of this record also establishes the default values for
      all semi-static information about the test, such as limits, units,
      and scaling. The MPR is related to the Test Synopsis Record (TSR)
      by test number, head number, and site number.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(15)
      REC_SUB  U*1   Record sub-type (15)
      TEST_NUM U*4   Test number
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      TEST_FLG B*1   Test flags (fail, alarm, etc.)
      PARM_FLG B*1   Parametric test flags (drift, etc.)
      RTN_ICNT U*2   Count (j) of PMR indexes                 See note
      RSLT_CNT U*2   Count (k) of returned results            See note
      RTN_STAT jxN*1 Array of returned states                 RTN_ICNT = 0
      RTN_RSLT kxR*4 Array of returned results                RSLT_CNT = 0
      TEST_TXT C*n   Descriptive text or label                length byte = 0
      ALARM_ID C*n   Name of alarm                            length byte = 0
      OPT_FLAG B*1   Optional data flag                       See note
      RES_SCAL I*1   Test result scaling exponent             OPT_FLAG bit 0 = 1
      LLM_SCAL I*1   Test low limit scaling exponent          OPT_FLAG bit 4or6=1
      HLM_SCAL I*1   Test high limit scaling exponent         OPT_FLAG bit 5or7=1
      LO_LIMIT R*4   Test low limit value                     OPT_FLAG bit 4or6=1
      HI_LIMIT R*4   Test high limit value                    OPT_FLAG bit5or7=1
      START_IN R*4   Starting input value (condition)         OPT_FLAG bit 1 = 1
      INCR_IN  R*4   Increment of input condition             OPT_FLAG bit 1 = 1
      RTN_INDX jxU*2 Array of PMR indexes                     RTN_ICNT = 0
      UNITS    C*n   Units of returned results                length byte = 0
      UNITS_IN C*n   Input condition units                    length byte = 0
      C_RESFMT C*n   ANSI C-result format string              length byte = 0
      C_LLMFMT C*n   ANSI C low limit format string           length byte = 0
      C_HLMFMT C*n   ANSI C high limit format string          length byte = 0
      LO_SPEC  R*4   Low specification limit value            OPT_FLAG bit 2 = 1
      HI_SPEC  R*4   High specification limit value           OPT_FLAG bit 3 = 1
      ======== ===== ======================================== ====================


    Notes on Specific Fields:
      Default Data:
        All data beginning with the OPT_FLAG field has a special function
        in the STDF file. The first MPR for each test will have these fields
        filled in. These values will be the default for each subsequent MPR
        with the same test number: if a subsequent MPR has a value for one
        of these fields, it will be used instead of the default, for that one
        record only; if the field is blank, the default will be used.  If the
        MPR is not associated with a test execution (that is, it contains only
        default information), bit 4 of the TEST_FLG field must be set, and the
        PARM_FLG field must be zero.  Unless the default is being overridden,
        the default data fields should be omitted in order to save space in
        the file.  Note that RES_SCAL, LLM_SCAL, HLM_SCAL, UNITS, C_RESFMT,
        C_LLMFMT, and C_HLMFMT are interdependent. If you are overriding the
        default value of one, make sure that you also make appropriate changes
        to the others in order to keep them consistent.  For character strings,
        you can override the default with a null value by setting the string
        length to 1 and the string itself to a single binary 0.

      TEST_NUM:
        The test number does not implicitly increment for successive values in
        the result array.

      HEAD_NUM, SITE_NUM:
        If a test system does not support parallel testing, and does not have a
        standard way of identifying its single test site or head, these fields
        should be set to 1.
        When parallel testing, these fields are used to associate individual
        datalogged results with a PIR/PRR pair. An MPR belongs to the PIR/PRR
        pair having the same values for HEAD_NUM and SITE_NUM.

      TEST_FLG:
        Contains the following fields:

          * bit 0:

            * 0 = No alarm
            * 1 = Alarm detected during testing

          * bit 1: Reserved for future use. Must be zero.
          * bit 2:

            * 0 = Test results are reliable
            * 1 = Test results are unreliable

          * bit 3:

            * 0 = No timeout
            * 1 = Timeout occurred

          * bit 4:

            * 0 = Test was executed
            * 1 = Test not executed

          * bit 5:

            * 0 = No abort
            * 1 = Test aborted

          * bit 6:

            * 0 = Pass/fail flag (bit 7) is valid
            * 1 = Test completed with no pass/fail indication

          * bit7:

            * 0 = Test passed
            * 1 = Test failed

      PARM_FLG:
        Is the parametric flag field, and contains the following bits:

          * bit 0:

            * 0 = No scale error
            * 1 = Scale error

          * bit 1:

            * 0 = No drift error
            * 1 = Drift error (unstable measurement)

          * bit 2:

            * 0 = No oscillation
            * 1 = Oscillation detected

          * bit 3:

            * 0 = Measured value not high
            * 1 = Measured value higher than high test limit

          * bit 4:

            * 0 = Measured value not low
            * 1 = Measured value lower than low test limit

          * bit 5:

            * 0 = Test failed or test passed standard limits
            * 1 = Test passed alternate limits

          * bit 6:

            * 0 = If result = low limit, then result is *fail*.
            * 1 = If result = low limit, then result is *pass*.

          * bit 7:

            * 0 = If result = high limit, then result is *fail*.
            * 1 = If result = high limit, then result is *pass*.

      RTN_ICNT, RTN_INDX, RTN_STAT:
        The number of element in the RTN_INDX and RTN_STAT arrays is determined
        by the, value of RTN_ICNT. The RTN_STAT field is stored 4 bits per
        value. The first value is stored in the low order 4 bits of the byte. If
        the number of indexes is odd, the high order 4 bits of the last byte
        in RTN_STAT will be padded with zero. The indexes referred to in the
        RTN_INDX are the PMR indexes defined in the Pin Map Record (PMR). The
        return state codes are the same as those defined for the RTN_STAT field
        in the FTR.  RTN_ICNT may be omitted if it is zero and it is the last
        field in the record.

     RSLT_CNT, RTN_RSLT:
       RSLT_CNT defines the number of parametric testresults in the
       RTN_RSLT. If this is a multiple pin measurement, and if PMR indexes
       will be specified, then the value of RSLT_CNT should be the same as
       RTN_ICNT. RTN_RSLT is an array of the parametric test result values.
       RSLT_CNT may be omitted if it is zero and it is the last field in
       the record.

     ALARM_ID:
       If the alarm flag (bit 0 of TEST_FLG ) is set, this field can contain
       the name or ID of the alarms that were triggered. Alarm names are
       tester-dependent.

     OPT_FLAG:
       Is the Optional Data Flag and contains the following bits:

         * bit 0 set = RES_SCAL value is invalid. The default set by the first
           MPR with this test number will be used.
         * bit 1 set = START_IN and INCR_IN are invalid.
         * bit 2 set = No low specification limit.
         * bit 3 set = No high specification limit.
         * bit 4 set = LO_LIMIT and LLM_SCAL are invalid. The default values set
           for these fields in the first MPR with this test number will be used.
         * bit 5 set = HI_LIMIT and HLM_SCAL are invalid. The default values set
           for these fields in the first MPR with this test number will be used.
         * bit 6 set = No Low Limit for this test(LO_LIMIT and LLM_SCAL are
           invalid).
         * bit7 set = No High Limit for this test (HI_LIMIT and HLM_SCAL are
           invalid).

       The OPT_FLAG field may be omitted if it is the last field in the record.

     START_IN, INCR_IN, UNITS_IN:
       For logging shmoo data, these fields specify the input
       conditions. START_IN is the ,beginning input value and INCR_IN is
       the increment, in UNITS_IN units. The input is applied and the output
       measured RSLT_CNT number of times. Values for INCR_IN can be positive
       or negative.

     LO_LIMIT, HI_LIMIT, UNITS:
       Regardless of how many test measurements are made, all must use the same
       limits, units, scaling, and significant digits.

     C_RESFMT, C_LLMFMT, C_HLMFMT:
       ANSI C format strings for use in formatting the test result and low
       and high limits (both test and spec). For example, *%7.2f*. The format
       string is also known as an output specification string, as used with the
       printstfatement. See any ANSI C reference man, or the man page on printf

     LO_SPEC, HI_SPEC:
       The specification limits are set in the first MPR and should
       never change. They use the same scaling and format strings as the
       corresponding test limits.

    Frequency:
      One per multiple-result parametric test execution.

    Location:
      Anywhere in the data stream after the corresponding Part Information
      Record (PIR) and before the corresponding Part Result Record (PRR).

    Possible Use:
      * Datalog
      * Shmoo Plot
    """
    typ = 15
    sub = 15
    fieldMap = (
        ('TEST_NUM',   'U4', None),
        ('HEAD_NUM',   'U1', None),
        ('SITE_NUM',   'U1', None),
        ('TEST_FLG',   'B1', None),
        ('PARM_FLG',   'B1', None),
        ('RTN_ICNT',   'U2', 0),
        ('RSLT_CNT',   'U2', 0),
        ('RTN_STAT', 'k5N1', []),
        ('RTN_RSLT', 'k6R4', []),
        ('TEST_TXT',   'Cn', ''),
        ('ALARM_ID',   'Cn', ''),
        ('OPT_FLAG',   'B1', BN),
        ('RES_SCAL',   'I1', ('OPT_FLAG', B0)),
        ('LLM_SCAL',   'I1', ('OPT_FLAG', B4 | B6)),
        ('HLM_SCAL',   'I1', ('OPT_FLAG', B5 | B7)),
        ('LO_LIMIT',   'R4', ('OPT_FLAG', B4 | B6)),
        ('HI_LIMIT',   'R4', ('OPT_FLAG', B5 | B7)),
        ('START_IN',   'R4', ('OPT_FLAG', B1)),
        ('INCR_IN',    'R4', ('OPT_FLAG', B1)),
        ('RTN_INDX', 'k5U2', ''),
        ('UNITS',      'Cn', ''),
        ('UNITS_IN',   'Cn', ''),
        ('C_RESFMT',   'Cn', ''),
        ('C_LLMFMT',   'Cn', ''),
        ('C_HLMFMT',   'Cn', ''),
        ('LO_SPEC',    'R4', ('OPT_FLAG', B2)),
        ('HI_SPEC',    'R4', ('OPT_FLAG', B3))
        )

@registerMe
class Ftr(RecordType):
    """
    **Functional Test Record (FTR)**

    Function:
      Contains the results of the single execution of a functional test in the
      test program. The first occurrence of this record also establishes the
      default values for all semi-static information about the test. The FTR
      is related to the Test Synopsis Record (TSR) by test number, head number,
      and site number.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(15)
      REC_SUB  U*1   Record sub-type (20)
      TEST_NUM U*4   Test number
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      TEST_FLG B*1   Test flags (fail, alarm, etc.)
      OPT_FLAG B*1   Optional data flagSee note
      CYCL_CNT U*4   Cycle count of vector                    OPT_FLAG bit0 = 1
      REL_VADR U*4   Relative vector address                  OPT_FLAG bit1 = 1
      REPT_CNT U*4   Repeat count of vector                   OPT_FLAG bit2 = 1
      NUM_FAIL U*4   Number of pins with 1 or more failures   OPT_FLAG bit3 = 1
      XFAIL_AD I*4   X logical device failure address         OPT_FLAG bit4 = 1
      YFAIL_AD I*4   Y logical device failure address         OPT_FLAG bit4 = 1
      VECT_OFF I*2   Offset from vector of interest           OPT_FLAG bit5 = 1
      RTN_ICNT U*2   Count (j)of return data PMR indexes      See note
      PGM_ICNT U*2   Count (k)of programmed state indexes     See note
      RTN_INDX jxU*2 Array of return data PMR indexes         RTN_ICNT = 0
      RTN_STAT jxN*1 Array of returned states                 RTN_ICNT = 0
      PGM_INDX kxU*2 Array of programmed state indexes        PGM_ICNT = 0
      PGM_STAT kxN*1 Array of programmed states               PGM_ICNT = 0
      FAIL_PIN D*n   Failing pin bitfield                     length bytes = 0
      VECT_NAM C*n   Vector module pattern name               length byte = 0
      TIME_SET C*n   Time set name                            length byte = 0
      OP_CODE  C*n   Vector Op Code                           length byte = 0
      TEST_TXT C*n   Descriptive text or label                length byte = 0
      ALARM_ID C*n   Name of alarm                            length byte = 0
      PROG_TXT C*n   Additional programmed information        length byte = 0
      RSLT_TXT C*n   Additional result information            length byte = 0
      PATG_NUM U*1   Pattern generator number                 255
      SPIN_MAP D*n   Bit map of enabled comparators           length byte = 0
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      Default Data:
        All data starting with the PATG_NUM field has a special function in
        the STDF file. The first FTR for each test will have these fields
        filled in. These values will be the default for each subsequent FTR
        with the same test number. If a subsequent FTR has a value for one of
        these fields, it will be used instead of the default, for that one
        record only. If the field is blank, the default will be used. This
        method replaces use of the FDR in STDF V3.  Unless the default is
        being overridden, the default data fields should be omitted in order
        to save space in the file.

      HEAD_NUM, SITE_NUM:
        If a test system does not support parallel testing, and does not
        have a standard way of identifying its single test site or head,
        these fields should be set to 1.  When parallel testing, these fields
        are used to associate individual datalogged results with a PIR/PRR
        pair. An FTR belongs to the PIR/PRR pair having the same values for
        HEAD_NUM and SITE_NUM.

      TEST_FLG:
        Contains the following fields:
          * bit 0:

            * 0 = No alarm
            * 1 = Alarm detected during testing

          * bit 1: Reserved for future use * must be 0
          * bit2:

            * 0 = Testresult is reliable
            * 1 = Test result is unreliable

          * bit 3:

            * 0 = No timeout
            * 1 = Timeout occurred

          * bit 4:

            * 0 = Test was executed
            * 1= Test not executed

          * bit 5:

            * 0 = No abort
            * 1= Test aborted

          * bit 6:

            * 0 = Pass/fail flag (bit 7) is valid
            * 1 = Test completed with no pass/fail indication

          * bit7:

            * 0 = Testpassed
            * 1 = Test failed

      OPT_FLAG:
        Contains the following fields:

          * bit 0 set = CYCL_CNT data is invalid
          * bit 1 set = REL_VADR data is invalid
          * bit 2 set = REPT_CNT data is invalid
          * bit 3 set = NUM_FAIL data is invalid
          * bit 4 set = XFAIL_AD and YFAIL_AD data are invalid
          * bit 5 set = VECT_OFF data is invalid (offset defaults to 0)
          * bits 6 - 7 are reserved for future use and must be 1

        This field is only optional if it is the last field in the record.

      XFAIL_AD, YFAIL_AD:
        The logical device address produced by the memory pattern generator,
        before going through conversion to a physical memory address. This
        logical address can be different from the physical address presented
        to the DUT pins.

      VECT_OFF:
        This is the integer offset of this vector (in sequence of execution)
        from the vector of interest (usually the failing vector). For example,
        if this FTR contains data for the vector before the vector of interest,
        this field is set to -1. If this FTR contains data for the third
        vector after the vector of interest, this field is set to 3. If this
        FTR is the vector of interest, VECT_OFF is set to 0. It is therefore
        possible to record an entire sequence of vectors around a failing
        vector for use with an offline debugger or analysis program.

      RTN_ICNT, PGM_ICNT:
        These fields may be omitted if all data following them is missing or
        invalid.

      RTN_ICNT, RTN_INDX, RTN_STAT:
        The size of the RTN_INDX and RTN_STAT arrays is determined by the
        value of RTN_ICNT.  The RTN_STAT field is stored 4 bits per value. The
        first value is stored in the low order 4 bits of the byte. If the
        number of indexes is odd, the high order 4 bits of the last byte in
        RTN_STAT will be padded with zero. The indexes referred to in the
        RTN_INDX are those defined in the PMR .

      RTN_STAT:
        The table of valid returned state values
        (expressed as hexadecimal digits) is:

          * 0= 0 or low
          * 1= 1 or high
          * 2= midband
          * 3 = glitch
          * 4 = undetermined
          * 5 = failed low
          * 6 = failed high
          * 7 = failed midband
          * 8 = failed with a glitch
          * 9= open
          * A= short

        The characters generated to represent these values are
        tester-dependent, and are specified in the PLR.

      PGM_ICNT, PGM_INDX, PGM_STAT:
        The size of the PGM_INDX and PGM_STAT arrays is determined by the
        value of PGM_ICNT. The indexes referred to in the PGM_INDX are those
        defined in the PMR.

      PGM_STAT:
        The table of valid program state values (expressed in hexadecimal)
        is listed below. Note that there are three defined program modes:
        Normal, Dual Drive (two drive bits per cycle), and SCIO (same
        cycle I/O).  The characters generated to represent these values are
        tester-dependent, and are specified in the PLR.

        ======================================  ============================
        Normal Mode Program States              Typical State Representation
        ======================================  ============================
        0 = DriveLow                            0
        1 = Drive High                          1
        2 = Expect Low                          L
        3 = Expect High                         H
        4 = Expect Midband                      M
        5 = Expect Valid (not midband)          V
        6 = Don't drive,or compare.             X
        7 = Keep window open from prior cycle.  W
        (used to *stretch* a comparison across
        cycles)
        ======================================  ============================

        ======================================  =============================
        Dual Drive Mode Program States          Typical State Representations
        ======================================  =============================
        0 = Low at D2, Low at D1 times          00 0
        1 = Low at D2, High at D1 times         10 1
        2 = Hi at D2, Low at D1 times           01 2
        3 = Hi at D2,High atD1times             11 3
        4 = Compare Low                         L
        5 = Compare High                        H
        6 = Compare Midband                     M
        7 = Don't Compare                       X
        ======================================  =============================

        ======================================  =============================
        SCIO Mode Program States                Typical State Representations
        ======================================  =============================
        0 = Drive Low, Compare Low.             0L l
        1 = Drive Low, Compare High             0H h
        2 = Drive Low, Compare Midband          0M m
        3 = Drive Low, Don't Compare            0X x
        4 = Drive High, Compare Low.            1L L
        5 = Drive High, Compare High            1H H
        6 = Drive High, Compare Midband         1M M
        7 = Drive High, Don't Compare           1X X
        ======================================  =============================

      FAIL_PIN:
        Encoded with PMR index 0 in bit 0 of the field, PMR index 1 in the
        1st position, and so on. Bits representing PMR indexes of failing
        pins are set to 1.

      ALARM_ID:
        If the alarm flag (bit 0 of TEST_FLG ) is set, this field can
        optionally contain the name or ID of the alarm or alarms that were
        triggered. The names of these alarms are tester-dependent.

      SPIN_MAP:
        This field contains an array of bits corresponding to the PMR index
        numbers of the enabled comparators. The 0th bit corresponds to PMR
        index 0, the 1st bit corresponds to PMR index 1, and so on. Each
        comparator that is enabled will have its corresponding PMR index bit
        set to 1.

    Frequency:
      One or more for each execution of a functional test.

    Location:
      Anywhere in the data stream after the corresponding Part Information
      Record (PIR) and before the corresponding Part Result Record (PRR).

    Possible Use:
      * Datalog
      * Functional Histogram
      * Functional Failure Analyzer
    """
    typ = 15
    sub = 20
    fieldMap = (
        ('TEST_NUM',    'U4', None),
        ('HEAD_NUM',    'U1', None),
        ('SITE_NUM',    'U1', None),
        ('TEST_FLG',    'B1', None),
        ('OPT_FLAG',    'B1', BN),
        ('CYCL_CNT',    'U4', ("OPT_FLAG", B0)),
        ('REL_VADR',    'U4', ("OPT_FLAG", B1)),
        ('REPT_CNT',    'U4', ("OPT_FLAG", B2)),
        ('NUM_FAIL',    'U4', ("OPT_FLAG", B3)),
        ('XFAIL_AD',    'I4', ("OPT_FLAG", B4)),
        ('YFAIL_AD',    'I4', ("OPT_FLAG", B4)),
        ('VECT_OFF',    'I2', ("OPT_FLAG", B5)),
        ('RTN_ICNT',    'U2', 0),
        ('PGM_ICNT',    'U2', 0),
        ('RTN_INDX', 'k12U2', []),
        ('RTN_STAT', 'k12N1', []),
        ('PGM_INDX', 'k13U2', []),
        ('PGM_STAT', 'k13N1', []),
        ('FAIL_PIN',    'Dn', []),
        ('VECT_NAM',    'Cn', ''),
        ('TIME_SET',    'Cn', ''),
        ('OP_CODE',     'Cn', ''),
        ('TEST_TXT',    'Cn', ''),
        ('ALARM_ID',    'Cn', ''),
        ('PROG_TXT',    'Cn', ''),
        ('RSLT_TXT',    'Cn', ''),
        ('PATG_NUM',    'U1', 0xff),
        ('SPIN_MAP',    'Dn', []),
        )

@registerMe
class Str(RecordType):
    """
    **Scan Test Record (STR)**

    Function:
        Scan Test Record (STR) is a new record that is added to the major record type
        15 category (Data Collected Per Test Execution). This is the same category
        where functional and parametric fail records exist. Thus the scan test record
        becomes another test record type in this category.
        It contains all or some of the results of the single execution of a scan test in
        the test program. It is intended to contain all of the individual pin/cycle
        failures that are detected in a single test execution. If there are more failures
        than can be contained in a single record, then the record may be followed by
        additional continuation STR records.
        In this new record some fields have been brought over from the functional test
        record and some new fields have been added to handle the scan test data.

    Data Fields:
        ======== ===== ======================================== ====================
        Name     Type  Description                              Missing/Invalid Flag
        ======== ===== ======================================== ====================
        CONT_FLG B*1   Continuation STR follows if not 0
        TEST_NUM U*4   Test number
        HEAD_NUM U*1   Test head number
        SITE_NUM U*1   Test site number
        PSR_REF  U*2   PSR Index (Pattern Sequence Record)
        TEST_FLG B*1   Test flags (fail, alarm, etc.)
        LOG_TYP  C*n   User defined description of datalog      length byte = 0
        TEST_TXT C*n   Descriptive text or label                length byte = 0
        ALARM_ID C*n   Name of alarm                            length byte = 0
        PROG_TXT C*n   Additional Programmed information        length byte = 0
        RSLT_TXT C*n   Additional result information            length byte = 0
        Z_VAL    U*1   Z Handling Flag
        FMU_FLG  B*1   MASK_MAP & FAL_MAP field status & Pattern Changed flag
        MASK_MAP D*n   Bit map of Globally Masked Pins          FMU_FLG bit 0 = 0 OR bit1 = 1
        FAL_MAP  D*n   Bit map of failures after buffer full    FMU_FLG bit 2 = 0 OR bit3 = 1
        CYC_CNT  U*8   Total cycles executed in test
        TOTF_CNT U*4   Total failures (pin x cycle) detected in test execution
        TOTL_CNT U*4   Total fails logged across the complete STR data set
        CYC_BASE U*8   Cycle offset to apply for the values in the CYCL_OFST array
        BIT_BASE U*4   Offset to apply for the values in the BIT_POS array
        COND_CNT U*2   Count (g) of Test Conditions and optional data specifications in present record
        LIM_CNT  U*2   Count (j) of LIM Arrays in present record, 1 for global specification
        CYC_SIZE U*1   Size (f) of data (1,2,4, or 8 byes) in CYC_OFST field        0
        PMR_SIZE U*1   Size (f) of data (1 or 2 bytes) in PMR_INDX field            0
        CHN_SIZE U*1   Size (f) of data (1, 2 or 4 bytes) in CHN_NUM field          0
        PAT_SIZE U*1   Size (f) of data (1,2, or 4 bytes) in PAT_NUM field          0
        BIT_SIZE U*1   Size (f) of data (1,2, or 4 bytes) in BIT_POS field          0
        U1_SIZE  U*1   Size (f) of data (1,2,4 or 8 bytes) in USR1 field            0
        U2_SIZE  U*1   Size (f) of data (1,2,4 or 8 bytes) in USR2 field            0
        U3_SIZE  U*1   Size (f) of data (1,2,4 or 8 bytes) in USR3 field            0
        UTX_SIZE U*1   Size (f) of each string entry in USER_TXT array              0
        CAP_BGN  U*2   Offset added to BIT_POS value to indicate capture cycles
        LIM_INDX jxU*2 Array of PMR indexes that require unique limit specs         LIM_CNT=0
        LIM_SPEC jxU*4 Array of fail limits for the PMRs listed in LIM_INDX         LIM_CNT=0
        COND_LST gxC*n Array of test condition (Name=value) pairs                   COND_CNT=0
        CYCO_CNT U*2   Count (k) of entries in CYC_OFST array                       0
        CYC_OFST kxU*f Array of cycle numbers relative to CYC_BASE                  CYCO_CNT=0
        PMR_CNT  U*2   Count (k) of entries in the PMR_INDX array                   0
        PMR_INDX kxU*f Array of PMR Indexes (All Formats)                           PMR_CNT=0
        CHN_CNT  U*2   Count (k) of entries in the CHN_NUM array                    0
        CHN_NUM  kxU*f Array of Chain No for FF Name Mapping                        CHN_CNT=0
        EXP_CNT  U*2   Count (k) of EXP_DATA array entries                          0
        EXP_DATA mxU*1 Array of expected vector data                                EXP_CNT=0
        CAP_CNT  U*2   Count (k) of CAP_DATA array entries                          0
        CAP_DATA kxU*1 Array of captured data                                       CAP_CNT=0
        NEW_CNT  U*2   Count (k) of NEW_DATA array entries                          0
        NEW_DATA kxU*1 Array of new vector data                                     NEW_CNT=0
        PAT_CNT  U*2   Count (k) of PAT_NUM array entries                           0
        PAT_NUM  kxU*f Array of pattern # (Ptn/Chn/Bit format)                      PAT_CNT=0
        BPOS_CNT U*2   Count (k) of BIT_POS array entries                           0
        BIT_POS  kxU*f Array of chain bit positions (Ptn/Chn/Bit format)            BPOS_CNT=0
        USR1_CNT U*2   Count (k) of USR1 array entries                              0
        USR1     kxU*f Array of user defined data for each logged fail              USR1_CNT=0
        USR2_CNT U*2   Count (k) of USR2 array entries                              0
        USR2     kxU*f Array of user defined data for each logged fail              USR2_CNT=0
        USR3_CNT U*2   Count (k) of USR3 array entries                              0
        USR3     kxU*f Array of user defined data for each logged fail              USR3_CNT=0
        TXT_CNT  U*2   Count (k) of USER_TXT array entries                          0
        USER_TXT kxC*f Array of user defined Cf strings for each logged fail        TXT_CNT=0
        ======== ===== ======================================== ====================
    """
    typ = 15
    sub = 30
    fieldMap = (
        ('CONT_FLG',    'B1', None),
        ('TEST_NUM',    'U4', None),
        ('HEAD_NUM',    'U1', None),
        ('SITE_NUM',    'U1', None),
        ('PSR_REF',     'U2', None),
        ('TEST_FLG',    'B1', None),
        ('LOG_TYP',     'Cn', ''),
        ('TEST_TXT',    'Cn', ''),
        ('ALARM_ID',    'Cn', ''),
        ('PROG_TXT',    'Cn', ''),
        ('RSLT_TXT',    'Cn', ''),
        ('Z_VAL',       'U1', None),
        ('FMU_FLG',     'B1', BN),
        ('MASK_MAP',    'Dn', ('FMU_FLG', B0 | B1)),
        ('FAL_MAP',     'Dn', ('FMU_FLG', B2 | B3)),
        ('CYC_CNT',     'U8', None),
        ('TOTF_CNT',    'U4', None),
        ('TOTL_CNT',    'U4', None),
        ('CYC_BASE',    'U8', None),
        ('BIT_BASE',    'U4', None),
        ('COND_CNT',    'U2', None),
        ('LIM_CNT',     'U2', None),
        ('CYC_SIZE',    'U1', 0),
        ('PMR_SIZE',    'U1', 0),
        ('CHN_SIZE',    'U1', 0),
        ('PAT_SIZE',    'U1', 0),
        ('BIT_SIZE',    'U1', 0),
        ('U1_SIZE',     'U1', 0),
        ('U2_SIZE',     'U1', 0),
        ('U3_SIZE',     'U1', 0),
        ('UTX_SIZE',    'U1', 0),
        ('CAP_BGN',     'U2', None),
        ('LIM_INDX', 'k21U2', []),
        ('LIM_SPEC', 'k21U4', []),
        ('COND_LST', 'k20Cn', []),
        ('CYCO_CNT',    'U2', 0),
        ('CYC_OFST', 'k35Uf', []),
        ('PMR_CNT',     'U2', 0),
        ('PMR_INDX', 'k37Uf', []),
        ('CHN_CNT',     'U2', 0),
        ('CHN_NUM',  'k39Uf', []),
        ('EXP_CNT',     'U2', 0),
        ('EXP_DATA', 'k41U1', []),
        ('CAP_CNT',     'U2', 0),
        ('CAP_DATA', 'k43U1', []),
        ('NEW_CNT',     'U2', 0),
        ('NEW_DATA', 'k45U1', []),
        ('PAT_CNT',     'U2', 0),
        ('PAT_NUM',  'k47Uf', []),
        ('BPOS_CNT',    'U2', 0),
        ('BIT_POS',  'k49Uf', []),
        ('USR1_CNT',    'U2', 0),
        ('USR1',     'k51Uf', []),
        ('USR2_CNT',    'U2', 0),
        ('USR2',     'k53Uf', []),
        ('USR3_CNT',    'U2', 0),
        ('USR3',     'k55Uf', []),
        ('TXT_CNT',     'U2', 0),
        ('USER_TXT', 'k57Cf', []),
    )
    sizeMap = {
        'CYC_OFST': 'CYC_SIZE',
        'PMR_INDX': 'PMR_SIZE',
        'CHN_NUM':  'CHN_SIZE',
        'PAT_NUM':  'PAT_SIZE',
        'BIT_POS':  'BIT_SIZE',
        'USR1':     'U1_SIZE',
        'USR2':     'U2_SIZE',
        'USR3':     'U3_SIZE',
        'USER_TXT': 'UTX_SIZE',
    }

@registerMe
class Bps(RecordType):
    """
    **Begin Program Section Record (BPS)**

    Function:
      Marks the beginning of a new program section (or sequencer) in the job
      plan.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(20)
      REC_SUB  U*1   Record sub-type (10)
      SEQ_NAME C*n   Program section (or sequencer) name      length byte = 0
      ======== ===== ======================================== ====================

    Frequency:
      Optional on each entry into the program segment.

    Location:
      Anywhere after thePIR and before the PRR.

    Possible Use:
      When performing analyses on a particular program segment's test.
    """
    typ = 20
    sub = 10
    fieldMap = (
        ('SEQ_NAME', 'Cn', ''),
        )

@registerMe
class Eps(RecordType):
    """
    **End Program Section Record (EPS)**

    Function:
      Marks the end of the current program section (or sequencer) in the job
      plan.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(20)
      REC_SUB  U*1   Record sub-type (20)
      ======== ===== ======================================== ====================

    Frequency:
      Optional on each exit from the program segment.

    Location:
      Following the corresponding BPS and before the PRR in the data stream.

    Possible Use:
      When performing analyses on a particular program segment's test.

      Note that pairs of BPS and EPS records can be nested: for example, when one
      sequencer calls another. In this case, the sequence of records could look
      like this:

        * BPS SEQ_NAME = sequence-1
        * BPS SEQ_NAME = sequence-2
        * EPS (end of sequence-2)
        * EPS (end of sequence-1)

      Because an EPS record does not contain the name of the sequencer, it should
      be assumed that each EPS record matches the last unmatched BPS record.
    """
    typ = 20
    sub = 20
    fieldMap = ()

@registerMe
class Gdr(RecordType):
    """
    **Generic Data Record (GDR)**

    Function:
      Contains information that does not conform to any other record type
      defined by the STDF specification. Such records are intended to be
      written under the control of job plans executing on the tester. This
      data may be used for any purpose that the user desires.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(50)
      REC_SUB  U*1   Record sub-type (20)
      FLD_CNT  U*2   Count of data fields in record
      GEN_DATA V*n   Data type code and data for one field
                     (Repeat GEN_DATA foreach data field)
      ======== ===== ======================================== ====================

    Notes on Specific Fields:
      GEN_DATA:
        Is repeated FLD_CNT number of times. Each GEN_DATA field consists of
        a data type code followed by the actual data. The data type code is
        the first unsigned byte of the field.
        Valid data types are:

          * 0  = B*0  Special pad field, of length 0 (See note below)
          * 1  = U*1  One byte unsigned integer
          * 2  = U*2  Two byte unsigned integer
          * 3  = U*4  Four byte unsigned integer
          * 4  = I*1  One byte signed integer
          * 5  = I*2  Two byte signed integer
          * 6  = I*4  Four byte signed integer
          * 7  = R*4  Four byte floating point number
          * 8  = R*8  Eight byte floating point number
          * 10 = C*n  Variable length ASCII character string
            (first byte is string length in bytes)
          * 11 = B*n  Variable length binary data string
            (first byte is string length in bytes)
          * 12 = D*n  Bit encoded data
            (first two bytes of string are length in bits)
          * 13 = N*1  Unsigned nibble

      Pad Field (Data Type 0):
        Data type 0, the special pad field, is used to force alignment of
        following data types in the record. In particular, it must be used
        to ensure even byte alignment of U*2, U*4, I*2, I*4, R*4,and R*8
        data types.
        The GDR is guaranteed to begin on an even byte boundary. The GDR
        header contains four bytes. The first GEN_DATA field therefore begins
        on an even byte boundary. It is the responsibility of the designer of
        a GDR record to provide the pad bytes needed to ensure data boundary
        alignment for the CPU on which it will run.

      Example:
        The following table describes a sample GDR that contains three data
        fields of different data types. The assumption is that numeric data
        of more than one byte must begin on an even boundary. Pad bytes will
        be used to meet this requirement.

        ==== ==== ===============================================================
        Data Code Alignment Requirement
        ==== ==== ===============================================================
        "AB" 10   A variable-length character string can begin on
                  any byte. This field will contain one data byte, one
                  length byte, and two data bytes, for a total length of
                  4 bytes. Because this field begins on an even byte, the
                  next field also begins on an even byte.
        255  1    A one-byte numeric value can begin on any byte. This field
                  contains two bytes, so the next field also begins on an
                  even byte.
        510  5    A two-byte numeric value must begin on an even byte. This
                  GEN_DATA field would begin on an even byte and, because
                  the first byte is the data code, the actual numeric value
                  would begin on an odd byte. This field must therefore be
                  preceded by a pad byte.
        ==== ==== ===============================================================

        The byte representation for this GDR is as follows. The byte ordering
        shown here is for sample purposes only. The actual data representation
        differs between CPUs. The byte values are shown in hexadecimal. The
        decimal equivalents are given in the description of the bytes.

        ========= ======== ==============================================
        Even Byte Odd Byte Description (with Decimal Values)
        ========= ======== ==============================================
        0c        00       Number of bytes following the header (12)
        32        0a       Record type (50); record subtype (10)
        04        00       Number of data fields (4)
        0a        02       Character string: code (10) and length (2)
        41        42       Character string: data bytes (*A* and *B*)
        01        ff       1-byte integer: code (1) and data (255 = 0xff)
        00        05       Pad byte(0); code(5) for next field
        fe        01       2-byte signed integer (510 = 0x01fe)
        ========= ======== ==============================================

    Frequency:
      A test data file may contain any number of GDR's.

    Location:
      Anywhere in the data stream after the initial sequence.

    Possible Use:
      User-written reports
    """
    typ = 50
    sub = 10
    fieldMap = (
        ('GEN_DATA', 'Vn', None),
        )

    #==============================================================================================
    def __init__(self, header=None, parser=None, values=None, **kwargs):
        super(Gdr, self).__init__(header=header, parser=parser, **kwargs)
        if not values:
            return
        vln = len(values)
        fm = [None] * (vln+1)
        fm[0] =('FLD_CNT', 'U2', None)
        vn = [vln] * (vln+1)
        for i in range(vln):
            fmt, val = encodeGdr(values[i])
            vName = '%s%d' % (GEN_DATA_, i)
            fm[i+1] = (vName, fmt, None)
            vn[i+1] = val
        self.setFieldMap(fm)            # replace the field map dynamically
        self.values = vn

@registerMe
class Dtr(RecordType):
    """
    **Datalog Text Record (DTR)**

    Function:
      Contains text information that is to be included in the datalog
      printout. DTR's may be written under the control of a job plan:
      for example, to highlight unexpected test results. They may also be
      generated by the tester executive software: for example, to indicate
      that the datalog sampling rate has changed. DTR's are placed as comments
      in the datalog listing.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      REC_LEN  U*2   Bytes of data following header
      REC_TYP  U*1   Record type(50)
      REC_SUB  U*1   Record sub-type (30)
      TEXT_DAT C*n   ASCII text string
      ======== ===== ======================================== ====================

    Frequency:
      A test data file may contain any number of DTR's.

    Location:
      Anywhere in the data stream after the initial sequence.

    Possible Use:
      * Datalog
    """
    typ = 50
    sub = 30
    fieldMap = (
        ('TEXT_DAT', 'Cn', None),
        )


if __name__ == '__main__':
    for key, recType in sorted(RecordRegistrar.items()):
        if isinstance(key, tuple):
            print repr(recType())