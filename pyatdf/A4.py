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

"""
======  ====================================
Record  Type
======  ====================================
ATR     Audit Trail Record
BPS     Begin Program Section Record
DTR     Datalog Text Record
EPS     End Program Section Record
FAR     File Attributes Record
FTR     Functional Test Record
GDR     Generic Data Record
HBR     Hardware Bin Record
MIR     Master Information Record
MPR     Multiple-Result Parametric Record
MRR     Master Results Record
PCR     Part Count Record
PGR     Pin Group Record
PIR     Part Information Record
PLR     Pin List Record
PMR     Pin Map Record
PRR     Part Results Record
PTR     Parametric Test Record
RDR     Retest Data Record
SBR     Software Bin Record
SDR     Site Description Record
TSR     Test Synopsis Record
WCR     Wafer Configuration Record
WIR     Wafer Information Record
WRR     Wafer Results Record
======  ====================================
"""

#**************************************************************************************************
#**************************************************************************************************
def listParser(valueList, caster, sep):
    values = valueList.split(sep)
    for i, value in enumerate(values):
        if value:
            values[i] = caster(value)
    return values

def fpr(valueList, sep=','):
    return listParser(valueList, float, sep)

def ipr(valueList, sep=','):
    return listParser(valueList, int, sep)

def spr(valueList, sep=','):
    return valueList.split(sep)

def xnt(s0x):
    return int(s0x, 16)

def xpr(valueList, sep=','):
    return listParser(valueList, xnt, sep)

       # these are the Gdr first character format character codes for vpr
castMap = dict(U=int, M=int, B=int, I=int, S=None, L=int, F=float, D=float, T=None, X=None, Y=None, N=xnt)

def vpr(value):
    typ, val = value[0], value[1:]
    caster = castMap.get(typ)
    return caster(val) if caster else val

arrayCasters = [fpr, ipr, spr, xpr]

#**************************************************************************************************
#**************************************************************************************************
class RecordType(object):

    def __init__(self, fieldTuple):
        self.fieldCount = len(fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      CPU_TYPE C*1  A - to indicate an ATDF File
      STDF_VER U*1  4 - STDF version number
      ATDF_VER U*1  2 - ATDF version number
      SCAL_FLG C*1  S - Scaling flag
      ======== ==== ========================================= ====================

    Sample: FAR:A|4|2|U

    Notes on Specific Fields:
      Scaling Flag:
        This character indicates whether parametric
        test results in the PTRs and MPRs are scaled
        or unscaled. Valid values for this field are:
        S = Scaled
        U = Unscaled
        If the flag is missing, the data is assumed to be scaled.

    Location:
      Required as the first record of the file.
    """
    fieldTuple = (
        ('CPU_TYPE', None),
        ('STDF_VER', int),
        ('ATDF_VER', int),
        ('SCAL_FLG', None)
    )
    def __init__(self):
        RecordType.__init__(self, Far.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      MOD_TIM  C*n  Date and time of file modification
      CMD_LINE C*n  Command line of program
      ======== ==== ========================================= ====================

    Sample: ATR:0:03:00 3-SEP-1992|bin_filter 7,9-12

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
    fieldTuple = (
        ('MOD_TIM', None),
        ('CMD_LINE', None)
    )
    def __init__(self):
        RecordType.__init__(self, Atr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      SETUP_T  C*n  Date and time of job setup
      START_T  C*n  Date and time first part tested
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
      TEST_COD C*n  Test phaseorstepcode                      length byte = 0
      TST_TEMP C*n  Test temperature                          length byte = 0
      USER_TXT C*n  Genericusertext                           length byte = 0
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

    Sample: MIR:A3002B|80386|80386HOT|akbar|J971|8:14:59 23-JUL-1992|8:23:02 23-JUL-1992|Sandy|P|1|2B|HOT|N|3.1.2|IG900|2.4|||300|100||
            386_data.txt|ceramic|386|wk23||MPU2||||||386HOT|3S|||A42136S|JOAN_S  (this sample is in the ATDF order...)

    Frequency:
      Always required. One per data stream.

    Location:
      Immediately after the File Attributes Record (FAR) and the Audit Trail
      Records (ATR), if ATR's are used.

    Possible Use:
      Header information for all reports
    """
    fieldTuple = (
        ('LOT_ID', None),
        ('PART_TYP', None),
        ('JOB_NAM', None),
        ('NODE_NAM', None),
        ('TSTR_TYP', None),
        ('SETUP_T', None),
        ('START_T', None),
        ('OPER_NAM', None),
        ('MODE_COD', None),
        ('STAT_NUM', int),
        ('SBLOT_ID', None),
        ('TEST_COD', None),
        ('RTST_COD', None),
        ('JOB_REV', None),
        ('EXEC_TYP', None),
        ('EXEC_VER', None),
        ('PROT_COD', None),
        ('CMOD_COD', None),
        ('BURN_TIM', int),
        ('TST_TEMP', None),
        ('USER_TXT', None),
        ('AUX_FILE', None),
        ('PKG_TYP', None),
        ('FAMILY_ID', None),
        ('DATE_COD', None),
        ('FACIL_ID', None),
        ('FLOOR_ID', None),
        ('PROC_ID', None),
        ('OPER_FRQ', None),
        ('SPEC_NAM', None),
        ('SPEC_VER', None),
        ('FLOW_ID', None),
        ('SETUP_ID', None),
        ('DSGN_REV', None),
        ('ENG_ID', None),
        ('ROM_COD', None),
        ('SERL_NUM', None),
        ('SUPR_NAM', None),
    )
    def __init__(self):
        RecordType.__init__(self, Mir.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      FINISH_T C*n  Date and time last part tested
      DISP_COD C*1  Lot disposition code                      space
      USR_DESC C*n  Lot description supplied by user          length byte = 0
      EXC_DESC C*n  Lot description supplied by exec          length byte = 0
      ======== ==== ========================================= ====================

    Sample: MRR:12:17:12 23-JUL-1992|H|Handler problems|Yield Alarm

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
    fieldTuple = (
        ('FINISH_T', None),
        ('DISP_COD', None),
        ('USR_DESC', None),
        ('EXC_DESC', None)
    )
    def __init__(self):
        RecordType.__init__(self, Mrr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      PART_CNT U*4  Number of parts tested
      RTST_CNT U*4  Number of parts retested                  4,294,967,295
      ABRT_CNT U*4  Number of aborts during testing           4,294,967,295
      GOOD_CNT U*4  Number of good (passed) parts tested      4,294,967,295
      FUNC_CNT U*4  Number of functional parts tested         4,294,967,295
      ======== ==== ========================================= ====================

    Samples: PCR:2|1|497|5|11|212|481 (for Head 2, Site 1)
             PCR:||3976|54|76|2311|3809 (for all test sites)

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('PART_CNT', int),
        ('RTST_CNT', int),
        ('ABRT_CNT', int),
        ('GOOD_CNT', int),
        ('FUNC_CNT', int)
    )
    def __init__(self):
        RecordType.__init__(self, Pcr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      HBIN_NUM U*2  Hardware bin number
      HBIN_CNT U*4  Number of parts in bin
      HBIN_PF  C*1  Pass/fail indication                      space
      HBIN_NAM C*n  Name of hardware bin                      length byte = 0
      ======== ==== ========================================= ====================

    Samples: HBR:2|1|6|212|F|SHORT (for Head 2, Site 1)
             HBR:||1|1346|P|PASSED (for all test sites)

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('HBIN_NUM', int),
        ('HBIN_CNT', int),
        ('HBIN_PF', None),
        ('HBIN_NAM', None)
    )
    def __init__(self):
        RecordType.__init__(self, Hbr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1  Test head number                          See note
      SITE_NUM U*1  Test site number
      SBIN_NUM U*2  Software bin number
      SBIN_CNT U*4  Number of parts in bin
      SBIN_PF  C*1  Pass/fail indication                      space
      SBIN_NAM C*n  Name of software bin                      length byte = 0
      ======== ==== ========================================= ====================

    Samples: SBR:1|2|74|14|F|NOTIFY PRODUCT ENG (for Head 1, Site 2)
             SBR:||1|1346|P|PASSED (for all test sites)

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('SBIN_NUM', int),
        ('SBIN_CNT', int),
        ('SBIN_PF', None),
        ('SBIN_NAM', None)
    )
    def __init__(self):
        RecordType.__init__(self, Sbr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      PMR_INDX U*2  Unique index associated with pin
      CHAN_TYP U*2  Channel type                              0
      CHAN_NAM C*n  Channel namei                             length byte = 0
      PHY_NAM  C*n  Physical name of pin                      length byte = 0
      LOG_NAM  C*n  Logical name of pin                       length byte = 0
      HEAD_NUM U*1  Head number associated with channel       1
      SITE_NUM U*1  Site number associated with channel       1
      ======== ==== ========================================= ====================

    Sample: PMR:2|A|1-7|GND|MAIN GROUND|2|1

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
    fieldTuple = (
        ('PMR_INDX', int),
        ('CHAN_TYP', int),
        ('CHAN_NAM', None),
        ('PHY_NAM', None),
        ('LOG_NAM', None),
        ('HEAD_NUM', int),
        ('SITE_NUM', int)
    )
    def __init__(self):
        RecordType.__init__(self, Pmr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
class Pgr(RecordType):
    """
    **Pin Group Record (PGR)**

    Function:
      Associates a name with a group of pins.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      GRP_INDX U*2   Unique index associated with pin group
      GRP_NAM  C*n   Name of pin group                        length byte = 0
      PMR_INDX kU*2  Array of indexes for pins in the group   INDX_CNT=0
      ======== ===== ======================================== ====================

    Sample: PGR:12|Data Out|5,6,7,8,9,10,11,12

    Notes on Specific Fields:
      GRP_INDX:
        The range of legal group index numbers is 32,768 - 65,535.
      PMR_INDX:
        PMR_INDX is an array of PMR indexes.
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
    fieldTuple = (
        ('GRP_INDX', int),
        ('GRP_NAM', None),
        ('PMR_INDX', ipr)
    )
    def __init__(self):
        RecordType.__init__(self, Pgr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
class Plr(RecordType):
    """
    **Pin List Record (PLR)**

    Function:
      Defines the current display radix and operating mode for a pin or pin group.

    Data Fields:
      ======== ===== ======================================== ====================
      Name     Type  Description                              Missing/Invalid Flag
      ======== ===== ======================================== ====================
      GRP_INDX k*2   Array of pin or pin group indexes
      GRP_MODE kU*2  Operating mode of pin group              0
      GRP_RADX kU*1  Display radix of pin group0
      PGM_CLCR kC*n  Program state encoding characters        length byte = 0
      RTN_CLCR kC*n  Return state encoding characters         length byte = 0
      ======== ===== ======================================== ====================

    Sample:
        PLR:2,3,6|20,20,21|H,H,H|H,L,L/H,H,H/L,L,L|1,0,M/1,0,H/M,L,H

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
            B = Display in Binary
            O = Display in Octal
            D = Display in Decimal
            H = Display in Hexadecimal
            S = Display as symbolic

      PGM_CHAR, PGM_CHAL:
        Programmed state codes are used to display the
        programmed state in the FTR or MPR record.
        Use of this field makes it possible to store tester dependent
        display representations in a tester independent
        format.
        The programmed state field consists of an array
        of lists of state codes. One or two characters may
        be used to represent each entry in a
        programmed state list (one for each state for
        which the pin or pin group can be programmed).
        If one character is used, then on conversion to
        STDF, it will be stored in the PGM_CHAR field. If
        two characters are used, then the first will be
        stored in PGM_CHAL and the second will be
        stored in PGM_CHAR. If more than two
        characters are in the item, only the first two will
        be used. Entries in the programmed state list
        must be separated by commas.
        The programmed state array will have one list for
        each entry of the Index Array. Lists will be
        separated within the array using the slash /
        character.
      RTN_CHAR, RTN_CHAL:
        Returned state codes are used to display the
        returned state in the FTR or MPR record. Use of
        this array makes it possible to store tester dependent
        display representations in a tester independent
        format.
        The returned state field consists of an array of
        lists of state codes. One or two characters may
        be used to represent each entry in a returned
        state list (one for each state for which the pin or
        pin group can output). If one character is used,
        then on conversion to STDF, it will be stored in
        the RTN_CHAR field. If two characters are used,
        then the first will be stored in RTN_CHAL and the
        second will be stored in RTN_CHAR. If more
        than two characters are in the item, only the first
        two will be used. Entries in the returned state list
        must be separated by commas.
        The returned state array will have one list for
        each entry of the Index Array. Lists will be
        separated within the array using the slash /
        character.

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
    fieldTuple = (
        ('GRP_INDX', ipr),
        ('GRP_MODE', ipr),
        ('GRP_RADX', spr),
        ('PGM_CLCR', spr),
        ('RTN_CLCR', spr)
    )
    def __init__(self):
        RecordType.__init__(self, Plr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      RTST_BIN kU*2 Array of retest bin numbers              NUM_BINS=0
      ======== ===== ======================================== ====================

    Sample: RDR:4,5,7

    Notes on Specific Fields:
      RTST_BIN:
        Array of bin numbers being retested. Bin numbers in the
        array will be separated by commas. If all bins are being
        retested, this field should be omitted and the record will
        consist of only the record header. Otherwise the field is
        required.

    Frequency:
      Optional. One per data stream.

    Location:
      If this record is used, it must appear immediately after the Master
      Information Record (MIR).

    Possible Use:
      Tells data filtering programs how to handle retest data.
    """
    fieldTuple = (
        ('RTST_BIN', ipr),
    )
    def __init__(self):
        RecordType.__init__(self, Rdr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1   Test head number
      SITE_GRP U*1   Site group number
      SITE_CNT U*1   Number (k) of test sites in site group
      SITE_NUM kU*1  Array of test site numbers
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

    Sample: SDR:2|4|5,6,7,8|Delta Flex|D511||B101|17

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_GRP', int),
        ('SITE_NUM', ipr),
        ('HAND_TYP', None),
        ('HAND_ID', None),
        ('CARD_TYP', None),
        ('CARD_ID', None),
        ('LOAD_TYP', None),
        ('LOAD_ID', None),
        ('DIB_TYP', None),
        ('DIB_ID', None),
        ('CABL_TYP', None),
        ('CABL_ID', None),
        ('CONT_TYP', None),
        ('CONT_ID', None),
        ('LASR_TYP', None),
        ('LASR_ID', None),
        ('EXTR_TYP', None),
        ('EXTR_ID', None)
    )
    def __init__(self):
        RecordType.__init__(self, Sdr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1   Test head number
      SITE_GRP U*1   Site group number                        255
      START_T  C*n   Date and time first part tested
      WAFER_ID C*n   Wafer ID                                 length byte = 0
      ======== ===== ======================================== ====================

    Sample: WIR:1|8:23:02 23-JUL-1992|2

    Notes on Specific Fields:
      SITE_GRP:
        Refers to the site group in the SDR .Thisisa meansof relating the wafer
        information to the configuration of the equipment used to test it. If
        this information is not known, or the tester does not support the
        concept of site groups, this field should be set to 255.
      WAFER_ID:
        Is optional, but is strongly recommended in order to make the resultant
        data files as useful as possible.

    Frequency:
      One per wafer tested.

    Location:
      Anywhere in the data stream after the initial sequence and before the
      MRR.
      Sent before testing each wafer.

    Possible Use:
      * Wafer Summary Sheet
      * Datalog
      * Wafer Map
    """
    fieldTuple = (
        ('HEAD_NUM', int),
        ('START_T', None),
        ('SITE_GRP', int),
        ('WAFER_ID', None)
    )
    def __init__(self):
        RecordType.__init__(self, Wir.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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

    Sample: WRR:1|11:02:42 23-JUL-1992|492|W01|3|102|214|2|131|MOS-4|F54|S3-1|Glass buildup on prober|Yield alarm on wafer W01

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('FINISH_T', None),
        ('PART_CNT', int),
        ('WAFER_ID', None),
        ('SITE_GRP', int),
        ('RTST_CNT', int),
        ('ABRT_CNT', int),
        ('GOOD_CNT', int),
        ('FUNC_CNT', int),
        ('FABWF_ID', None),
        ('FRAME_ID', None),
        ('MASK_ID', None),
        ('USR_DESC', None),
        ('EXC_DESC', None)
    )
    def __init__(self):
        RecordType.__init__(self, Wrr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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

    Sample: WCR:D|R|D|5|.3|.25|1|23|19      # The ATDF spec has different order than the STDF spec # TODO verify

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
      POS_X: Positive X direction on the wafer. Valid values are:
        L = Left
        R = Right
        If more than one character appears in this field, it
        will be truncated to the first character during
        conversion to STDF.
      POS_Y Positive Y direction on the wafer. Legal values are:
        U = Up
        D = Down
        If more than one character appears in this field, it
        will be truncated to the first character during
        conversion to STDF.
    """
    fieldTuple = (
        ('WF_FLAT', None),
        ('POS_X', None),
        ('POS_Y', None),
        ('WAFR_SIZ', float),
        ('DIE_HT', float),
        ('DIE_WID', float),
        ('WF_UNITS', int),
        ('CENTER_X', int),
        ('CENTER_Y', int),
    )
    def __init__(self):
        RecordType.__init__(self, Wcr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      ======== ===== ======================================== ====================

    Sample: PIR:2|1

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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int)
    )
    def __init__(self):
        RecordType.__init__(self, Pir.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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

    PRR:2|1|13|78|F|0|17|-2|7|||644|Device at edge of wafer|F13C20

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
      PART_FLG: bits 3 & 4
        Legal values for the pass/fail code are:
        P = Part passed
        F = Part failed
      PART_FLG: bits 0 or 1
        The presence of a value in this field indicates
        that this is a retested device, and that the data
        in this record supersedes data for the device
        with the same identifier. The actual value of this
        field indicates that the superseded device data
        is identified by:
        I = Same Part ID
        C = Same X/Y Coordinates
        If not a retest, this field is empty.
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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('PART_ID', None),
        ('NUM_TEST', int),
        ('PF_FLG', None),
        ('HARD_BIN', int),
        ('SOFT_BIN', int),
        ('X_COORD', int),
        ('Y_COORD', int),
        ('RETEST', None),
        ('ABRT_COD', None),
        ('TEST_T', None),
        ('PART_TXT', None),
        ('PART_FIX', None),        # Was a Bn
    )
    def __init__(self):
        RecordType.__init__(self, Prr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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

    Sample: TSR:2|2|600|Leakage|P|413|92|3||DC_TESTS|0.005|0.1|7.2|1280.3|4329.5

    Notes on Specific Fields:
      HEAD_NUM:
        If this TSR contains a summary of the test counts for all test sites,
        this field must be set to 255.
      TEST_TYP:
        Indicates what type of test this summary data is for. Valid values are:

          * P = Parametrictest
          * F = Functionaltest
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
    fieldTuple = (
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('TEST_NUM', int),
        ('TEST_NAM', None),
        ('TEST_TYP', None),
        ('EXEC_CNT', int),
        ('FAIL_CNT', int),
        ('ALRM_CNT', int),
        ('SEQ_NAME', None),
        ('TEST_LBL', None),
        ('TEST_TIM', float),
        ('TEST_MIN', float),
        ('TEST_MAX', float),
        ('TST_SUMS', float),
        ('TST_SQRS', float),
    )
    def __init__(self):
        RecordType.__init__(self, Tsr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      C_RESFMT C*n   ANSI C result format string              length byte = 0
      C_LLMFMT C*n   ANSI C low limit format string           length byte = 0
      C_HLMFMT C*n   ANSI C high limit format string          length byte = 0
      LO_SPEC  R*4   Low specification limit value            OPT_FLAG bit 2 = 1
      HI_SPEC  R*4   High specification limit value           OPT_FLAG bit 3 = 1
      ======== ===== ======================================== ====================

    Sample: PTR:23|2|1|997.3|F|AOH|Check 2nd layer|||A|-1.7|45.2| %9.4f|%7.2f|%7.2f|-1.75|45.25|3|3|4       # ATDF spec order

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
    fieldTuple = (
        ('TEST_NUM', int),
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('RESULT', float),
        ('PF_FLG', None),
        ('ALRM_FLG', None),
        ('TEST_TXT', None),
        ('ALARM_ID', None),
        ('LIMT_CMP', None),
        ('UNITS', None),
        ('LO_LIMIT', float),
        ('HI_LIMIT', float),
        ('C_RESFMT', None),
        ('C_LLMFMT', None),
        ('C_HLMFMT', None),
        ('LO_SPEC', float),
        ('HI_SPEC', float),
        ('RES_SCAL', int),
        ('LLM_SCAL', int),
        ('HLM_SCAL', int),
    )
    def __init__(self):
        RecordType.__init__(self, Ptr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      RTN_INDX jxU*2 Array ofPMR indexes                      RTN_ICNT = 0
      UNITS    C*n   Units of returned results                length byte = 0
      UNITS_IN C*n   Input condition units                    length byte = 0
      C_RESFMT C*n   ANSI Cresultformatstring                 length byte = 0
      C_LLMFMT C*n   ANSI C low limit format string           length byte = 0
      C_HLMFMT C*n   ANSI C high limit format string          length byte = 0
      LO_SPEC  R*4   Low specification limit value            OPT_FLAG bit 2 = 1
      HI_SPEC  R*4   High specification limit value           OPT_FLAG bit 3 = 1
      ======== ===== ======================================== ====================

    MPR:143|2|4||001.3,0009.6,001.5|F|D|||LH|mA|001.0|002.0| 4.5|.1|V|3,4,5|%6.1f|%6.1f|%6.1f|0009.75|002.25

    Notes on Specific Fields:
      Default Data:
        All MPR data starting with the Test Units: field has a special function in the ATDF file. The
        first MPR for each test will have these fields filled in. The values in these fields will be the
        default values for each subsequent MPR with the same test number. If the field is filled in
        for subsequent MPRs, that value will override the default. Otherwise the default will be used.
        For character strings, it is possible to override the default with a null value by setting the
        string to a single space.
        Unless the default has been overridden, omit the default data fields to save space in the
        ATDF file.

      TEST_NUM:
        The test number does not implicitly increment for successive values in
        the result array.

      HEAD_NUM, SITE_NUM:
        If a test system does not support parallel testing, and does not have a
        standard way of identifying its single test site or head, these fields
        should be set to 1.
        When parallel testing, these fields are used to associate individual
        data logged results with a PIR/PRR pair. An MPR belongs to the PIR/PRR
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
    fieldTuple = (
        ('TEST_NUM', int),
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('RTN_STAT', xpr),
        ('RTN_RSLT', fpr),
        ('PF_FLAG', None),
        ('ALRM_FLG', None),
        ('TEST_TXT', None),
        ('ALARM_ID', None),
        ('LIMT_CMP', None),
        ('UNITS', None),
        ('LO_LIMIT', float),
        ('HI_LIMIT', float),
        ('START_IN', float),
        ('INCR_IN', float),
        ('UNITS_IN', None),
        ('RTN_INDX', ipr),
        ('C_RESFMT', None),
        ('C_LLMFMT', None),
        ('C_HLMFMT', None),
        ('LO_SPEC', float),
        ('HI_SPEC', float),
        ('RES_SCAL', int),
        ('LLM_SCAL', int),
        ('HLM_SCAL', int),
    )
    def __init__(self):
        RecordType.__init__(self, Mpr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      TEST_NUM U*4   Test number
      HEAD_NUM U*1   Test head number
      SITE_NUM U*1   Test site number
      TEST_FLG B*1   Test flags (fail, alarm, etc.)
      OPT_FLAG B*1   Optional data flagSee note
      CYCL_CNT U*4   Cycle count of vector                    OPT_FLAG bit0 = 1
      REL_VADR U*4   Relative vector address                  OPT_FLAG bit1 = 1
      REPT_CNT U*4   Repeat count of vector                   OPT_FLAG bit2 = 1
      NUM_FAIL U*4   Number of pins with 1 or more failures   OPT_FL            # TEST_NUM AG bit3 = 1
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

    Sample: FTR:27|2|1|P||CHECKERBOARD|A1|5|16|2|3|6|3|0|10,2,8,12|0,1,1,4|4,5,6,7|0,0,0,0|8|DRV|Check Driver||||2|2,3,4,6

    Notes on Specific Fields:
      Default Data:
        All FTR data starting with the Generator Num: field has a special function in the ATDF file.
        The first FTR for each test will have these fields filled in. The values in these fields will be
        the default values for each subsequent FTR with the same test number. If the field is filled
        in for subsequent FTRs, that value will override the default. Otherwise the default will be
        used. Unless the default has been overridden, omit the default data fields to save space in the
        ATDF file.

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
    fieldTuple = (
        ('TEST_NUM', int),
        ('HEAD_NUM', int),
        ('SITE_NUM', int),
        ('PF_FLAG', None),
        ('ALRM_FLG', None),
        ('VECT_NAM', None),
        ('TIME_SET', None),
        ('CYCL_CNT', int),
        ('REL_VADR', int),
        ('REPT_CNT', int),
        ('NUM_FAIL', int),
        ('XFAIL_AD', int),
        ('YFAIL_AD', int),
        ('VECT_OFF', int),
        ('RTN_INDX', ipr),
        ('RTN_STAT', xpr),
        ('PGM_INDX', ipr),
        ('PGM_STAT', xpr),
        ('FAIL_PIN', None),       # Was a Dn
        ('OP_CODE', None),
        ('TEST_TXT', None),
        ('ALARM_ID', None),
        ('PROG_TXT', None),
        ('RSLT_TXT', None),
        ('PATG_NUM', int),
        ('SPIN_MAP', None),       # Was a Dn
    )
    def __init__(self):
        RecordType.__init__(self, Ftr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      SEQ_NAME C*n   Program section (or sequencer) name      length byte = 0
      ======== ===== ======================================== ====================

    Sample: BPS:DC_TESTS

    Frequency:
      Optional on each entry into the program segment.

    Location:
      Anywhere after thePIR and before the PRR.

    Possible Use:
      When performing analyses on a particular program segment's test.
    """
    fieldTuple = (
        ('SEQ_NAME', None),
    )
    def __init__(self):
        RecordType.__init__(self, Bps.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      ======== ===== ======================================== ====================

    Sample: EPS:

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
    fieldTuple = ()

    def __init__(self):
        RecordType.__init__(self, Eps.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      GEN_DATA V*n   Data type code and data for one field
                     (Repeat GEN_DATA for each data field)
      ======== ===== ======================================== ====================

    Sample: GDR:TThis is text|L-435|U255|F645.7110|XFFE0014C

    Notes on Specific Fields:
      GEN_DATA:
        Is repeated some number of times. Each GEN_DATA field consists of
        a data type code followed by the actual data. The data type code is
        the first unsigned byte of the field.
        Valid data types are:
            The first character of the field is the format
            character and will indicate how the ASCII text to
            follow should be treated. This field may be
            repeated as many times as desired. Legal values
            for the first character are:
            U = U*1 - One byte unsigned integer.
            M = U*2 - Two byte unsigned integer.
            B = U*4 - Four byte unsigned integer.
            I = I*1 - One byte signed integer.
            S = I*2 - Two byte signed integer.
            L = I*4 - Four byte signed integer.
            F = R*4 - Four byte floating point number.
            D = R*8 - Eight byte floating point number.
            T = C*n - Variable length ASCII string.
            X = B*n - Variable length binary data (in hexadecimal). Max length is 255 bytes.
            Y = D*n - Variable length binary data (in hexadecimal). Max length is 65535 bits.
            N = N*1 - Unsigned nibble.

      Note on Pad Bytes:
        No pad byte is defined because byte alignment is not a problem in the ATDF format. Pad
        bytes are inserted as necessary on conversion to STDF.

    Frequency:
      A test data file may contain any number of GDR's.

    Location:
      Anywhere in the data stream after the initial sequence.

    Possible Use:
      User-written reports
    """
    fieldTuple = (
        ('GEN_DATA', vpr),
        )

    def __init__(self):
        RecordType.__init__(self, Gdr.fieldTuple)

#**************************************************************************************************
#**************************************************************************************************
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
      TEXT_DAT C*n   ASCII text string
      ======== ===== ======================================== ====================

    Sample: DTR:Datalog sampling rate is now 1 in 10

    Frequency:
      A test data file may contain any number of DTR's.

    Location:
      Anywhere in the data stream after the initial sequence.

    Possible Use:
      * Datalog
    """
    fieldTuple = (
        ('TEXT_DAT', None),
        )

    def __init__(self):
        RecordType.__init__(self, Dtr.fieldTuple)

far = Far()
atr = Atr()
mir = Mir()
mrr = Mrr()
pcr = Pcr()
hbr = Hbr()
sbr = Sbr()
pmr = Pmr()
pgr = Pgr()
plr = Plr()
rdr = Rdr()
sdr = Sdr()
wir = Wir()
wrr = Wrr()
wcr = Wcr()
pir = Pir()
prr = Prr()
tsr = Tsr()
ptr = Ptr()
mpr = Mpr()
ftr = Ftr()
bps = Bps()
eps = Eps()
gdr = Gdr()
dtr = Dtr()

records = (
    far,
    atr,
    mir,
    mrr,
    pcr,
    hbr,
    sbr,
    pmr,
    pgr,
    plr,
    rdr,
    sdr,
    wir,
    wrr,
    wcr,
    pir,
    prr,
    tsr,
    ptr,
    mpr,
    ftr,
    bps,
    eps,
    gdr,
    dtr
    )
