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

    def __init__(self, applies_functionInlining = False, applies_technique1 = False, applies_technique2 = False):
        """
        Constructor method that specifies which technique instance will imply applying.
        """
        # Techniques 'technique1' and 'technique2' are added here as comments-
        # to indicate the intended implementation of class should there be more techniques

        # Number of times to repeat each technique:
        repeat_functionInlining = 10     # >3 takes time even with small programs-
                                        # number of calls increases in fashion a(n+1) = a(n)^2 <=> a(n) = a(0)^(2^n))!
        # repeat_technique1 = 1
        # repeat_technique2 = 4

        # Variable initialization:
        self.techniqueOrder__ = []      # Array of names of techniques ordered correctly
        self.namedFunctions__ = dict()  # Dictionary mapping names of techniques to [isApplied, func]-
                                        # the former is a flag wether the technique is applied or not, and
                                        # the latter the function of corresponding technique

        self.techniqueFunctions = []    # Array of functions of techniques sorted in correct order


        # Setting methods for each technique and its name:
        self.namedFunctions__['functionInlining'] = [applies_functionInlining, functionInlining]
            # self.namedFunctions['technique1'] = [applies_technique1, funcTechnique1]
            # self.namedFunctions['technique2'] = [applies_technique2, funcTechnique2]


        # Ordering methods: (in this example [technique1 -> function inlining -> technique2])
        # self.techniqueOrder.append('technique1')
        self.techniqueOrder__.extend(['functionInlining'] * repeat_functionInlining)
        # self.techniqueOrder.append('technique2'')

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

