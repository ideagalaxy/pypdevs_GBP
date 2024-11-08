from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import Simulator

class GENState:
    def __init__(self, current="out"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class GEN(AtomicDEVS):
    def __init__(self, name = 'GEN', gen_time = 10):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = GENState("out")
        self.outport = self.addOutPort("GEN_outport")
        self.gen_time = gen_time

    def timeAdvance(self):
        state = self.state.get()

        if state == "out":
            return self.gen_time
        else:
            raise DEVSException(\
                "unknown state <%s> in GEN time advance transition function"\
                % state)
        
    def intTransition(self):
        state = self.state.get()
        
        if state == "out":
            self.state = GENState("out")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in GEN internal transition function"\
                % state)
        
    def outputFnc(self):
        state = self.state.get()

        if state == "out":
            return {self.outport : "out"}
        
class BUFState:
    def __init__(self, current=[0,"F"]):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return str(self.get())
    
class BUF(AtomicDEVS):
    def __init__(self, name = "BUF", max_length = INFINITY):
        AtomicDEVS.__init__(self, name)
        self.state = BUFState([0,"F"])    #[n,proc.state]
        self.max_length = max_length
        self.outport = self.addOutPort("BUF_outport")
        self.inport = self.addInPort("BUF_inport")
        self.response_inport = self.addInPort("BUF_response_inport")

        self.full = False

    def timeAdvance(self):
        state = self.state.get()
        n, proc_state = state

        if n == 0 or proc_state == "B":
            return INFINITY
        elif n != 0 and proc_state == "F":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in BUF time advance transition function"\
                % state)
        
    def intTransition(self):
        state = self.state.get()
        n, proc_state = state

        self.full = False
        n -= 1
        proc_state = "B"
        self.state = BUFState([n,proc_state])

        return self.state

        
    def extTransition(self, inputs):
        state = self.state.get()
        n, proc_state = state

        inport = inputs.get(self.inport, None)
        response_inport = inputs.get(self.response_inport, None)

        if inport:
            if inport == "out":
                if self.full == True:
                    return self.state
                else:
                    if n < self.max_length:
                        n += 1
                    self.state = BUFState([n,proc_state])
                    return self.state
            else:
                return self.state
        
        if response_inport:
            if response_inport == "F":
                proc_state = "F"
                self.state = BUFState([n,proc_state])
                return self.state
            
            else:
                return self.state
        
        raise DEVSException(\
                "unknown state <%s> in BUF external transition function"\
                % state)
    
    def outputFnc(self):
        return {self.outport : "out"}
            
class PROCState:
    def __init__(self, current="F"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class PROC(AtomicDEVS):
    def __init__(self, name = 'PROC', process_time = 12):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = PROCState("F")
        self.outport = self.addOutPort("PRCO_outport")
        self.inport = self.addInPort("PROC_inport")
        self.process_time = process_time

    def timeAdvance(self):
        state = self.state.get()

        if state == "F":
            return INFINITY
        elif state == "B":
            return self.process_time
        else:
            raise DEVSException(\
                "unknown state <%s> in PROC time advance transition function"\
                % state)
        
    def intTransition(self):
        state = self.state.get()
        
        if state == "B":
            self.state = PROCState("F")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in PROC internal transition function"\
                % state)
    
    def extTransition(self, inputs):
        state = self.state.get()

        inport = inputs[self.inport]

        if inport == "out":
            self.state = PROCState("B")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in PROC external transition function"\
                % state)
        
    def outputFnc(self):
            return {self.outport : "F"}
        
class BP(CoupledDEVS):
    def __init__(self, name):
        CoupledDEVS.__init__(self, name)

        self.buffer = self.addSubModel(BUF(name="BUF", max_length=4))
        self.processor = self.addSubModel(PROC(name="PROC", process_time=4))

        self.inport = self.addInPort("BP_inport")
        self.outport = self.addOutPort("BP_ouport")

        self.connectPorts(self.inport,self.buffer.inport)
        self.connectPorts(self.buffer.outport, self.processor.inport)
        self.connectPorts(self.processor.outport, self.outport)

        self.connectPorts(self.processor.outport, self.buffer.response_inport)

    def select(self, imm):
        if self.processor in imm:
            return self.processor
        
class GBP(CoupledDEVS):
    def __init__(self, name):
        CoupledDEVS.__init__(self, name)

        self.generator = self.addSubModel(GEN(name="GEN", gen_time=2))
        self.bp_model = self.addSubModel(BP(name="BP"))

        self.connectPorts(self.generator.outport, self.bp_model.inport)
    
    def select(self, imm):
        if self.bp_model in imm:
            return self.bp_model

sim = Simulator(GBP("GBP"))
sim.setVerbose()
sim.setTerminationTime(80) #test : 200sec
sim.setClassicDEVS()

sim.simulate()
