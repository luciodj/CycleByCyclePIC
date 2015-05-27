# IncrementTest.py
#
from PICEmulator import PIC

def test_increment():
    FLASH_SIZE = 128
    RAM_SIZE = 32

    # instantiate a device
    pic = PIC( FLASH_SIZE, RAM_SIZE)

    # load test pattern
    pic.flash[0] = 0x2AF    # incf 0xf,F
    pic.flash[1] = 0xA00    # goto 0x000
    pic.flash[2] = 0xFFF    # marker

    # cycle 1
    print "PC = %x" % pic.pc
    pic.Tcy()   # first cycle (reset/skip)
    assert pic.ram[0xf] == 0    # ram initialized correctly

    # cycle 2
    pic.Tcy()   # incf 
    assert pic.ram[0xf] == 1    # ram incremented 

    # cycle 3
    pic.Tcy()   # goto

    # cycle 4 
    pic.Tcy()   # skip

    # cycle 5
    pic.Tcy()   # incf
    assert pic.ram[0xf] == 2    # ram incremented again

    print "Increment Test completed successfully!"