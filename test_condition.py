# test_condition.py
#
from PICEmulator import PIC

def test_condition():
    FLASH_SIZE = 128
    RAM_SIZE = 32

    # instantiate a device
    pic = PIC( FLASH_SIZE, RAM_SIZE)

    # load test pattern
    pic.flash[0] = 0x22F    # movf 0xF,F (set Z)
    pic.flash[1] = 0x743    # BTFSS STATUS,Z
    pic.flash[2] = 0xA00    # GOTO  0
    pic.flash[3] = 0xA01    # GOTO  1

    # cycle 1
    print "PC = %x" % pic.pc
    pic.Tcy()   # first cycle (reset/skip)
    assert pic.ram[0xf] == 0    # ram initialized correctly

    # cycle 2
    pic.Tcy()   # movf 0xf,F
    assert pic.z    # Z set

    # cycle 3
    pic.Tcy()   # btfss
    assert pic.skip    # skip set

    # cycle 4
    pic.Tcy()   # skipped

    # cycle 5
    pic.Tcy()   # goto 1
    assert pic.pc == 1

    print "Conditional Test completed successfully!"