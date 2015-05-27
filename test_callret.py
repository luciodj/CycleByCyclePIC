# test_callret.py
#
from PICEmulator import PIC

def test_callret():
    FLASH_SIZE = 128
    RAM_SIZE = 32

    # instantiate a device
    pic = PIC( FLASH_SIZE, RAM_SIZE)

    # load test pattern
    pic.flash[0] = 0x910    # call 0x010
    pic.flash[1] = 0x02F    # mowf 0xf
    pic.flash[2] = 0x22F    # movf 0xf,F
    pic.flash[3] = 0x743    # BTFSS STATUS,Z
    pic.flash[4] = 0xA00    # GOTO  0
    pic.flash[5] = 0xA01    # GOTO  1

    pic.flash[0x10] = 0x801 # retlw 1

    # cycle 1
    print "PC = %x" % pic.pc
    pic.Tcy()   # first cycle (reset/skip)
    assert pic.ram[0xf] == 0    # ram initialized correctly

    # cycle 2
    pic.Tcy()   # call 10
    assert pic.pc == 0x10

    # cycle 3
    pic.Tcy()   # call Skip

    # cycle 4
    pic.Tcy()   # retlw
    assert pic.pc == 1

    # cycle 5
    pic.Tcy()   # ret skip

    # cycle 6
    pic.Tcy()   # movwf 0xf
    assert  pic.ram[0xf] == 1

    # cycle 7
    pic.Tcy()   # movf 0xf,F
    assert not pic.z    # Z clr

    # cycle 8
    pic.Tcy()   # btfss
    assert not pic.skip    # skip set

    # cycle 9
    pic.Tcy()   # goto 0
    print pic.pc
    assert pic.pc == 0


    print "CallRet Test completed successfully!"