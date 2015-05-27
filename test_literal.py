# test_literal.py
#
from PICEmulator import PIC

def test_literal():
    FLASH_SIZE = 128
    RAM_SIZE = 32

    # instantiate a device
    pic = PIC( FLASH_SIZE, RAM_SIZE)

    # load test pattern
    pic.flash[0] = 0xC5A    # movlw 0x5A
    pic.flash[1] = 0xFFF    # xorlw 0xFF
    pic.flash[2] = 0x02F    # movwf 0x0f
    pic.flash[3] = 0x3AF    # swapf 0x0f

    # cycle 1
    print "PC = %x" % pic.pc
    pic.Tcy()   # first cycle (reset/skip)
    assert pic.ram[0xf] == 0    # ram initialized correctly

    # cycle 2
    pic.Tcy()   # movlw 
    assert pic.wreg == 0x5a    # wreg assigned 

    # cycle 3
    pic.Tcy()   # xorlw 0xff
    assert pic.wreg == 0xa5    # wreg xor-ed

    # cycle 4
    pic.Tcy()   # movwf 0xf
    assert pic.ram[0xf] == 0xa5

    # cycle 5
    pic.Tcy()   # swapf 0xf
    assert pic.ram[0xf] == 0x5a

    print "Literal Test completed successfully!"