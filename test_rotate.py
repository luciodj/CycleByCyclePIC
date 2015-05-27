# RotateTest.py
#
from PICEmulator import PIC

def test_Rotate():
    FLASH_SIZE = 128
    RAM_SIZE = 32

    # instantiate a device
    pic = PIC( FLASH_SIZE, RAM_SIZE)

    # load test pattern
    pic.flash[0] = 0xC01    # movlw 1 
    pic.flash[1] = 0x02F    # movwf 0xf
    pic.flash[2] = 0x32F    # rrf 0xf,F
    pic.flash[3] = 0x32F    # rrf 0xf,F
    pic.flash[4] = 0x36F    # rlf 0xf,F
    pic.flash[5] = 0x36F    # rlf 0xf,F

    # cycle 0
    print "PC = %x" % pic.pc
    pic.Tcy()   # first cycle (reset/skip)
    assert pic.ram[0xf] == 0    # ram initialized correctly

    # cycle 1
    pic.Tcy()   # movlw 1 
    assert pic.wreg == 1    # wreg <= lit

    # cycle 2
    pic.Tcy()   # movwf 0xf
    assert pic.ram[0xf] == 1

    # cycle 3 
    pic.Tcy()   # rrf
    assert pic.cy 
    assert pic.ram[0xf] == 0
    # cycle 4 
    pic.Tcy()   # rrf
    assert not pic.cy 
    assert pic.ram[0xf] == 0x80

    # cycle 5
    pic.Tcy()   # rlf
    assert pic.ram[0xf] == 0
    assert pic.cy

    # cycle 6
    pic.Tcy()   # rlf
    assert pic.ram[0xf] == 1
    assert not pic.cy  

    print "Rotate Test completed successfully!"
