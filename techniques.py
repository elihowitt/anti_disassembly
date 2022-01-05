import random
from typing import List, Dict       # Used for type hinting
import copy                         # Used for non reference copies (shallow & deep)
from fileData import *
from usefulFunctions import *


class Techniques:
    """
    Class whos instances represent which techniques to apply.
    This class has the important role of dictating the order in which the techniques get applied.
    Intended usage: {instance.techniqueFunctions}.
    """
    # This class is a bit over-kill and convoluted however it achieves three important things:
    # 1) The 'user' can use the same instance in many places implicitly. (instead of a long list of booleans).
    # 2) The 'user' does not need to worry about string matches (as in other implementations of similar concepts).
    # 3) For 'Us', the programmers it is very modular and simple to change the order of techniques (see ctor).

    def __init__(self, applies_functionInlining = False, applies_junkCode = False):
        """
        Constructor method that specifies which technique instance will imply applying.
        """

        """
        Im not sure this kind of implementation is as convenient and flexible as explicitly appending each time.
        
        # Number of times to repeat each technique:
        repeat_functionInlining = 10    # >3 takes time even with even small recursive programs-
                                        # number of calls increases in fashion a(n+1) = a(n)^2 <=> a(n) = a(0)^(2^n))!
        repeat_junkCode = 3
        """        """self.techniqueOrder__.extend(['functionInlining'] * repeat_functionInlining)"""


        junkSize = 2

        # Variable initialization:
        self.techniqueOrder__ = []      # Array of names of techniques ordered correctly
        self.namedFunctions__ = dict()  # Dictionary mapping names of techniques to [isApplied, func]-
                                        # the former is a flag wether the technique is applied or not, and
                                        # the latter the function of corresponding technique

        self.techniqueFunctions = []    # Array of functions of techniques sorted in correct order


        # Setting methods for each technique and its name:
        self.namedFunctions__['functionInlining'] = [applies_functionInlining, functionInlining]
        self.namedFunctions__['junkCode'] = [applies_junkCode, getJunkCodeFunction(junkSize=junkSize)]


        # Ordering methods:
        self.techniqueOrder__.append('junkCode')
        self.techniqueOrder__.append('functionInlining')
        self.techniqueOrder__.append('junkCode')
        self.techniqueOrder__.append('functionInlining')
        self.techniqueOrder__.append('junkCode')

        for t in self.techniqueOrder__:
            applies, func = self.namedFunctions__[t]
            if applies:
                self.techniqueFunctions.append(func)


def functionInlining(fd : FileData) -> FileData:

    """
        Anti disassembly technique implementation that inlines all function calls in given 'FileData' object (once)
    """

    tmpFileData = FileData()
    tmpFileData.labels = fd.labels[:]
    tmpFileData.miscSegments = copy.deepcopy(fd.miscSegments)
    tmpFileData.segmentlessLines = fd.segmentlessLines[:]
    tmpFileData.data = copy.deepcopy(fd.data)

    for t in fd.textSegments:
        tmpSeg = FileData.TextSegment()        # Temporary segment for storing changes
        tmpSeg.data = copy.deepcopy(t.data)
        tmpSeg.labels = t.labels[:]

        tmpFunctions = []       # Array of functions processed in current segment, used to fix 'functions' dict

        for procName, procInstructions in t.processes.items():
            tmpFunctions.append(procName)
            tmpProcLines = []
            for instruction in procInstructions:
                line = instruction.line
                if line[0] == 'call':                       # Calling another function which we might inline
                    funcName = line[1]
                    if funcName in fd.functions:            # If function is defined locally then we can inline it
                        funcSeg = fd.textSegments[fd.functions[funcName]]
                        funcLines = [ins.line for ins in funcSeg.processes[funcName]]
                        tmpFuncLines = funcLines[:]         # Temporary array for storing lines after alterations

                        # Insert data:
                        for dataName, dataValue in funcSeg.data.items():
                            newName = dataName
                            isChanged = False
                            if newName in tmpSeg.data:
                                isChanged = True
                                newName = increaseName(newName, len(tmpSeg.data.keys())-1)  # Trying to avoid conflict
                                while newName in tmpSeg.data:   # Name conflict
                                    newName = increaseName(newName)

                            tmpSeg.data[newName] = dataValue

                            if isChanged:
                                tmpFuncLines = [swapNames(line = funcLine, oldName = dataName, newName = newName)
                                                for funcLine in tmpFuncLines]

                        # Fix label conflicts:
                        for label in funcSeg.labels:
                            newName = tmpFileData.labels[len(tmpFileData.labels)-1]
                            while newName in tmpFileData.labels:
                                newName = increaseName(newName)

                            tmpSeg.labels.append(newName)
                            tmpFileData.labels.append(newName)
                            tmpFuncLines = [swapLabels(line = funcLine, oldName = label, newName = newName)
                                            for funcLine in tmpFuncLines]

                        # Remove return lines:
                        newName = 'Co01Secr3tLabel' if len(tmpFileData.labels) == 0 else tmpFileData.labels[0]
                        while newName in tmpFileData.labels:
                            newName = increaseName(newName)

                        tmpSeg.labels.append(newName)
                        tmpFileData.labels.append(newName)

                        isCallerCleanUp: bool = False   # Whether the callee is cleaning the stack.
                                                        # We assume {ret imm} form indicates such a convention.

                        tmpFuncLines2 = [['sub', 'rsp,', '4']]   # Adding a stub in place of {push eip} of call
                        for funcLine in tmpFuncLines:
                            if funcLine[0] == 'ret':
                                if len(funcLine) == 2 and funcLine[1] != '0':
                                    # E.g. 'ret 8' <=> {return and pop 8 bytes from stack}
                                    tmpFuncLines2.append(['add', 'rsp,', funcLine[1]])
                                    isCallerCleanUp = True
                                tmpFuncLines2.append(['jmp', newName])
                            else:
                                tmpFuncLines2.append(funcLine)

                        tmpFuncLines2.append([newName+':'])     # The label itself

                        # Insert function:
                        tmpProcLines.extend(tmpFuncLines2)
                        if not isCallerCleanUp:                 # Removing stub {pop eip} of ret
                            tmpProcLines.append(['add', 'rsp,', '4'])

                    else:
                        tmpProcLines.append(line)
                else:
                    tmpProcLines.append(line)

            tmpSeg.processes[procName] = [(FileData.TextSegment.Instruction(tmpLine)) for tmpLine in tmpProcLines]

        tmpFileData.textSegments.append(tmpSeg)
        index = len(tmpFileData.textSegments) - 1
        for funcName in tmpFunctions:
            tmpFileData.functions[funcName] = index

    return tmpFileData

def getJunkCodeFunction(junkSize=2):

    def junkCode(fd: FileData) -> FileData:
        """
            Anti disassembly technique implementation that adds junk code to given 'FileData' object.
            This function adds 'junkSize' lines that change a register in every place possible (per each register).
            The code added actually runs but doesnt change the functionality of the program. (As opposed to the opposite).
        """

        for tsIdx, ts in enumerate(fd.textSegments):
            for procName, procInstructions in ts.processes.items():

                # The following is a utility matrix such that-
                #   isNextUse[reg][i] = is the next occurrence of reg is the process an instruction that uses reg.
                # This is useful for determining where a junk instruction that changes reg can be inserted-
                #   only if the next occurrence is not a use of reg (as opposed to an instruction that only changes reg).
                isNextUse = [[True for __ in range(len(procInstructions + 1))] for _ in range(16)]

                # Calculating matrix values:
                for idx, ins in enumerate(reversed(procInstructions)):
                    for regIdx in range(16):
                        occurred = False

                        if regIdx in ins.uses:  # Is used in this line
                            occurred = True
                            isNextUse[regIdx] = True

                        if not occurred and regIdx in ins.changes:  # Is only changed in this line
                            occurred = True
                            isNextUse[regIdx][idx] = False

                        if not occurred:  # Otherwise the next is same as proceeding instruction
                            isNextUse[regIdx][idx] = isNextUse[regIdx][idx + 1]

                # New list of instructions after adding junk code
                tmpInstructions: List[FileData.TextSegment.Instruction] = []
                for idx, ins in enumerate(procInstructions):
                    for regIdx in range(16):
                        if isNextUse[regIdx][idx]:  # I.e. can we insert changes to reg before current instruction
                            tmpInstructions.extend([getJunkInstruction(regIdx) for _ in range(junkSize)])

                    tmpInstructions.append(ins)  # Adding original instruction

                fd.textSegments[tsIdx].processes[procName] = copy.deepcopy(tmpInstructions)

        return fd

    return junkCode


def getJunkInstruction(reg):
    # Utility function for creating junk instructions that change 'reg' register

    changingCommands = ['mov']      #, 'add', 'sub', 'imul', 'shl', 'shr', 'mul', 'xor']
    # TODO: add support for more intricate instructions (& pass to funct available flags!),-
    #  and pointer type arguments.

    randCommand = changingCommands[random.randint(0, len(changingCommands)-1)]

    secondArgument = None   # Represents the second argument in the instruction


    registerNameIndex = random.randint(0, 3)    # There are 4 names(parts) for each register.
                                                # Both must match to match sizes

    # The probability the second argument will be a number-
    #   theres a preference to use numbers since they wont add 'usage' restriction on the otherwise register.
    probNum = 0.8

    if  random.random() < probNum:
        secondArgument = str(random.randint(-64, 64))

    else:
        secondArgument = \
            FileData.TextSegment.Instruction.Argument.registerNames[random.randint(0, 15)][registerNameIndex]

    return FileData.TextSegment.Instruction(
        [randCommand,
         FileData.TextSegment.Instruction.Argument.registerNames[reg][registerNameIndex],
         secondArgument])

