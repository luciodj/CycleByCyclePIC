# 
# Cycle by cycle PIC (baseline) Emulator
#

class Sfr:
    INDF    = 0
    TMR0    = 1
    PCL     = 2
    STATUS  = 3
    FSR     = 4


class Alu:
    MOW = 0;  CLR = 1;  SUB = 2;  DEC = 3
    IOR = 4;  AND = 5;  XOR = 6;  ADD = 7
    MOV = 8;  COM = 9;  INC = 10; DSZ = 11
    RRF = 12; RLF = 13; SWA = 14; ISZ = 15

class Ir:
    OP_MASK   = 0xC00
    BYTE_MATCH= 0x000
    BIT_MATCH = 0x400
    CG_MATCH  = 0x800
    LIT_MATCH = 0xC00

class itype:
    BYTE = 0; BIT = 1; GOTO = 2; LIT = 3

class PIC:
    def __init__( self, max_flash, max_ram):
        self.flash = [ 0 for i in range( max_flash)]
        self.ram = [ 0 for i in range( max_ram)]

        self.max_flash = max_flash
        self.max_ram = max_ram
        # special function registers
        self.wreg = 0       # working register
        self.tris = 0
        self.option = 0
        self.tmr0 = 0
        self.pc   = 0       # start with reset vector at 0 
        self.z = 0          # zero flag
        self.cy = 0         # carry flag
        self.pa0 = 0        # page bit
        self.fsr = 0        # file selection register
        self.stack1 = 0
        self.stack2 = 0
        self.nextpc = 0
        # decoding and intermediate latches
        self.ir = 0         # pre-fetched, next instruction (start with a NOP)
        self.op = 0         # decoded operation in process
        self.r = 0          # value read / alu temp
        self.m = 0          # alu mux 0 = literal, 1 = file
        self.d = 0          # 0 = wreg, 1 = file
        self.f = 0          # file (register)
        self.b = 0          # bit selector
        self.l = 0          # literal value
        self.w = False      # write back result
        self.skip = False   # skip the next (fetched) instruction

    def Tcy( self):
        # execute one instruction cycle
        self.Q1()
        self.Q2()
        self.Q3()
        self.Q4()

    def Q1( self):
        if self.skip:
            self.ir = 0                 # execute a NOP instead
            self.skip = False
            print "Skip"
        else:
            print "Decode: %x" % self.ir 
        self.decode(self.ir)

    def Q2( self):
        # read
        if self.m: # file
            self.r = self.fileRead( self.f)
            print "Read file: [%x]: %x" % ( self.f, self.r)
        else:      # literal
            self.r = self.l
        # fetch
        self.ir = self.flashFetch()
        print "Fetching: [%x]: %x" % (self.pc, self.ir)

    def Q3( self):
        self.nextpc = self.pcIncrement()
        self.modify()

    def Q4( self):
        # write
        if self.w:
            if self.d == 0:
                self.wreg = self.r
                print "W = %x" % self.wreg
            else:
                self.fileWrite( self.f, self.r)
                print "File [ %x] <= %x" % ( self.f, self.r)
        self.pc = self.nextpc

    def decode( self, ir):
        self.op = ir                    # save a copy for Q3 
        i = ir & Ir.OP_MASK;
        if  i == Ir.BIT_MATCH:    
            self.type = itype.BIT
            self.b = ( ir >> 5 ) & 0x7  # bit selector 
            self.f =  ir & 0x1f         # 5-bit file selector
        elif i == Ir.LIT_MATCH:
            self.type = itype.LIT
            self.m = 0                  # literal
            self.d = 0                  # all lit operations write to wreg
            self.l = ir & 0xff          # 8 bit literal
        elif i == Ir.BYTE_MATCH:
            self.type = itype.BYTE      # and control operations (sleep, clrwdt...)
            # file/byte operation do read file, control operations don't
            self.m =  1 if ( self.op & 0xff0) != 0 else 0
            self.d = (ir >> 5) & 1      # write back selector
            self.f = ir & 0x1f          # 5-bit file selector
        else:   # goto/call/retlw
            self.type = itype.GOTO      # goto/return/call operation
            self.l = ir & 0x1ff         # 9-bit literal

    def modify( self):
        if self.type == itype.BIT:      # bit operation
            self.op = (self.op >> 8) & 0x3
            print "BIT operation %x" % self.op
            print "bit %d of %d  " % (self.b, self.r)
            if self.op == 0:            # BCF
                self.r &= not( 1 << self.b)
                self.w = True
            elif self.op == 1:          # BSF
                self.r |= (1 << self.b)
                self.w = True
            elif self.op == 2:          # BTSC
                self.skip = ( ( self.r & (1 << self.b)) == 0)
                self.w = False
            else:                       # BTSS
                self.skip = ( ( self.r & (1 << self.b)) != 0)
                self.w = False
        elif self.type == itype.GOTO:
            self.w = False              # no value write back in Q4
            self.op = (self.op >> 8) & 0x3
            print "GOTO/CALL/RET opeation %x" % self.op
            if self.op == 0:            # retlw
                self.nextpc = self.pcPop()  
                self.skip = True        
                self.r = self.l & 0xff  
                self.d = 0              #  wreg  
                self.w = True   
            elif self.op == 1:          # call
                self.pcPush()           # push pc on hardware stack
                self.nextpc = (0x200 if self.pa0 else 0) + (self.l & 0xff)
                self.skip = True
            else:                       # goto
                self.nextpc = ( 0x200 if self.pa0 else 0) + (self.l & 0x1ff)
                self.skip = True
        elif self.type == itype.LIT:
            self.w = True               # write back result of literal operations
            self.op = (self.op >> 8) & 0x3
            print "LITERAL operation %x" % self.op
            if self.op == 0:            # MOVLW
                self.compute( Alu.MOV)
            elif self.op == 1:          # IORLW
                self.compute( Alu.IOR)
            elif self.op == 2:          # ANDLW
                self.compute( Alu.AND)
            else:                       # XORLW
                self.compute( Alu.XOR)
        else:                           #itype.BYTE: 
            self.w = False
            # first separate control instructions
            if ( self.op & 0xff0) == 0:
                if self.op != 0:
                    print "Control operation %x" % self.op
                    if self.op == 0x004:    # clrwdt
                        self.wdt = 0
                    elif self.op == 0x002:  # option
                        self.option = self.wreg
                    elif self.op == 0x003:  # sleep
                        self.sleep = True
                    else:                   # tris
                        self.tris = self.wreg
                else:
                    pass        # NOP
            else:
                self.op = (self.op >> 6) & 0xf
                print "BYTE operation %x" % self.op
                self.compute( self.op)
                self.w = True               # write back result in Q4

    def compute( self, op): 
        if op == Alu.MOW:
            self.r = self.wreg
        elif op == Alu.CLR:
            self.r = 0
            self.z = True
        elif op == Alu.SUB:
            self.cy = ( self.r >= self.wreg)
            self.r = (self.r - self.wreg) & 0xff
            self.z = (self.r == 0)
        elif op == Alu.DEC:
            self.r = (self.r - 1) & 0xff
            self.z = (self.r == 0)
        elif op == Alu.IOR:
            self.r = self.wreg | self.r
        elif op == Alu.AND:
            self.r = self.wreg & self.r
            self.z = (self.r == 0)
        elif op == Alu.XOR:
            self.r = self.wreg ^ self.r
            self.z = (self.r == 0)
        elif op == Alu.ADD:
            self.r = self.wreg + self.r
            self.cy = ( self.r > 0xff)
            self.r &= 0xff
            self.z = (self.r == 0)
        elif op == Alu.MOV:
            self.r = self.r
            self.z = (self.r == 0)
        elif op == Alu.COM:
            self.r = (-self.r) & 0xff 
            self.z = (self.r == 0)
        elif op == Alu.INC:
            self.r = self.r + 1
            self.r &= 0xff
            self.z = (self.r == 0)
        elif op == Alu.DSZ:
            self.r = ( self.r - 1) & 0xff
            self.skip = ( self.r == 0)
        elif op == Alu.RRF:
            temp = self.r & 1
            self.r = self.r >> 1
            self.r += (self.cy<<7)
            self.cy = ( temp == 1)
        elif op == Alu.RLF:
            temp = self.r >> 7
            self.r = (self.r << 1) & 0xff
            self.r += 1 if self.cy else 0
            self.cy = ( temp == 1)
        elif op == Alu.SWA:
            self.r = ( (self.r & 0xf0) >> 4) | ( (self.r & 0xf) << 4)
        else :     # op == Alu.ISZ:
            self.r =  (self.r + 1) & 0xff
            self.skip = ( self.r == 0)

    def fileRead( self, f):
        if f == Sfr.PCL :
            return self.pc & 0xff
        elif f == Sfr.FSR:
            return self.fsr
        elif f == Sfr.INDF:
            if self.fsr == Sfr.FSR:     # indirectly reading FSR reads 0
                return 0                
            else:
                return self.ram[ self.fsr & (max_ram-1)]
        elif f == Sfr.STATUS:
            t = 4 if self.z else   0
            t += 1 if self.cy else 0
            t += 32 if self.pa0 else 0
            return t
        else:   
            return self.ram[ (f & 0x1f) + (self.fsr & 0x60)]

    def fileWrite( self, f, data):
        if f == Sfr.FSR:
            self.fsr = data & 0x1f          # fsr can only address 
        elif f == Sfr.INDF:
            if self.fsr != Sfr.FSR:         # indirectly writing to FSR is a NOP
                self.ram[ self.fsr & (max_ram-1)] = data  
        elif f == Sfr.PCL:
            self.nextpc = data + ( 0x200 if self.pa0 else 0) # move pa0 to bit 9
        elif f == Sfr.STATUS:
            self.z = data & 4
            self.cy = data & 1
            self.pa0 = data & 32
        else:
            self.ram[ (f & 0x1f) + (self.fsr & 0x60)] = data

    def pcIncrement( self):
        npc = self.pc + 1
        if npc >= self.max_flash:
            npc = 0
        return npc

    def flashFetch( self):
        return self.flash[ self.pc]

    def pcPush( self):
        self.stack2 = self.stack1
        self.stack1 = self.pc 

    def pcPop( self):
        temp = self.stack1
        self.stack1 = self.stack2
        return temp

