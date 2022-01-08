from usefulFunctions import *

class Techniques:
    """
    Class whos instances represent which techniques to apply.
    This class has the important role of dictating the order in which the techniques get applied.
    Intended usage: {instance.techniqueFunctions}.
    """

    TECHNIQUE_FUNCTION_INLINING = 0
    TECHNIQUE_JUNK_CODE = 1
    TECHNIQUE_PERMUTE_LINES = 2

    NUM_TECHNIQUES = 3

    def __init__(self, applies_functionInlining = False, applies_junkCode = False,
                 applies_permuteLines = False, junkSize = 2,
                 pipeline = [TECHNIQUE_JUNK_CODE, TECHNIQUE_FUNCTION_INLINING, TECHNIQUE_PERMUTE_LINES,
                             TECHNIQUE_JUNK_CODE, TECHNIQUE_FUNCTION_INLINING, TECHNIQUE_PERMUTE_LINES]):
        """
        Constructor method that specifies which technique instance will imply applying.
        argument 'junkSize': a measurement of how much junk code will be injected.
        argument 'pipeline': an ordered list of technique indices to apply.
        """

        appliesFunc = [None for _ in range(Techniques.NUM_TECHNIQUES)]
        appliesFunc[Techniques.TECHNIQUE_FUNCTION_INLINING] = [applies_functionInlining, functionInlining]
        appliesFunc[Techniques.TECHNIQUE_JUNK_CODE] = [applies_junkCode, getJunkCodeFunction(junkSize)]
        appliesFunc[Techniques.TECHNIQUE_PERMUTE_LINES] = [applies_permuteLines, permuteLines]

        self.techniqueFunctions = []    # Array of functions of techniques sorted in correct order

        for t in pipeline:
            applies, func = appliesFunc[t]
            if applies:
                self.techniqueFunctions.append(func)


def functionInlining(fd : FileData) -> FileData:

    """
        Anti disassembly technique implementation that inlines all function calls in given 'FileData' object (once).
        Warning: recursive functions with inner calls>1 increase very fast! (a_n = a_0^(2^n))
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

                        tmpFuncLines2 = [['sub', 'esp,', '4']]   # Adding a stub in place of {push eip} of call
                        for funcLine in tmpFuncLines:
                            if funcLine[0] == 'ret':
                                if len(funcLine) == 2 and funcLine[1] != '0':
                                    # E.g. 'ret 8' <=> {return and pop 8 bytes from stack}
                                    tmpFuncLines2.append(['add', 'esp,', funcLine[1]])
                                    isCallerCleanUp = True
                                tmpFuncLines2.append(['jmp', newName])
                            else:
                                tmpFuncLines2.append(funcLine)

                        tmpFuncLines2.append([newName+':'])     # The label itself

                        # Insert function:
                        tmpProcLines.extend(tmpFuncLines2)
                        if not isCallerCleanUp:                 # Removing stub {pop eip} of ret
                            tmpProcLines.append(['add', 'esp,', '4'])

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
                registerRange = 14   # testing on x32
                matrixWidth = len(procInstructions)
                isNextUse = [[True for __ in range(matrixWidth + 1)] for _ in range(registerRange + 1)]

                # Calculating matrix values:
                for idx, ins in enumerate(reversed(procInstructions)):
                    for regIdx in range(registerRange + 1):
                        occurred = False

                        if ins.uses[regIdx]:  # Is used in this line
                            occurred = True
                            isNextUse[regIdx][matrixWidth-idx-1] = True

                        if not occurred and ins.changes[regIdx]:  # Is only changed in this line
                            occurred = True
                            isNextUse[regIdx][matrixWidth-idx-1] = False

                        if not occurred:  # Otherwise the next is same as proceeding instruction
                            isNextUse[regIdx][matrixWidth-idx-1] = isNextUse[regIdx][matrixWidth-idx]

                # New list of instructions after adding junk code
                tmpInstructions: List[FileData.TextSegment.Instruction] = []
                for idx, ins in enumerate(procInstructions):
                    canChange = []
                    regChangeFlag = False
                    for regIdx in range(registerRange + 1):
                        if not isNextUse[regIdx][idx]:  # I.e. can we insert changes to reg before current instruction
                            canChange.append(regIdx)
                            if regIdx <= 7:
                                regChangeFlag = True

                    if regChangeFlag:
                        numJunk = random.randint(0, junkSize)
                        instrs = []
                        for _ in range(numJunk):
                            instrs += getJunkInstruction(canChange)
                        tmpInstructions.extend(instrs)

                    tmpInstructions.append(ins)  # Adding original instruction

                fd.textSegments[tsIdx].processes[procName] = copy.deepcopy(tmpInstructions)

        return fd

    return junkCode


def permuteLines(fd: FileData) -> FileData:
    """
            Anti disassembly technique implementation that
            permutes all order-invariant instructions in given 'FileData' object.
    """

    # Enumeration of states of chunks of a unit, more details in inner loop.
    UNIT_STATE_EMPTY = 0
    UNIT_STATE_USES = 1
    UNIT_STATE_CHANGES = 2
    UNIT_STATE_LAST_CHANGE = 3
    UNIT_STATE_USES_AND_CHANGES = 4

    for tsIdx, ts in enumerate(fd.textSegments):
        for procName, procInstructions in ts.processes.items():
            tmpProcInstructions = []

            # This matrix represents for each unit the groups of instructions that as far as the unit cares-
            #   are order-invariant. Looks like~ unitChunks[unit] = [{instruction1, instruction5}, {instruction13},...].
            # Where chunks are { a bunch of uses }, { a bunch of changes },
            # { single change (cannot be moved relative to previous changes or next group of uses) }, { uses }...
            # unitChunks[unit] will be treated as stack

            unitChunks = [[] for _ in range(FileData.TextSegment.Instruction.NUM_UNITS)]

            # Array of previous states per unit
            unitState = [UNIT_STATE_EMPTY for _ in range(FileData.TextSegment.Instruction.NUM_UNITS)]

            numInstructions = len(procInstructions)

            # Computing unitChunks
            for idx, procInstruction in enumerate(reversed(procInstructions)):
                for unit in procInstruction.includes:
                    if procInstruction.changes[unit]:
                        if procInstruction.uses[unit]:
                            unitChunks[unit].append(set([numInstructions-idx-1]))
                            unitState[unit] = UNIT_STATE_USES_AND_CHANGES

                        elif unitState[unit] == UNIT_STATE_EMPTY or  unitState[unit] == UNIT_STATE_USES or  \
                                unitState[unit] == UNIT_STATE_USES_AND_CHANGES:
                            unitChunks[unit].append(set([numInstructions-idx-1]))
                            unitState[unit] = UNIT_STATE_LAST_CHANGE

                        elif unitState[unit] == UNIT_STATE_LAST_CHANGE:
                            unitChunks[unit].append(set([numInstructions - idx - 1]))
                            unitState[unit] = UNIT_STATE_CHANGES

                        else:   # Join a chnages group
                            unitChunks[unit][-1].add(numInstructions - idx - 1)
                            unitState[unit] = UNIT_STATE_CHANGES

                    else:   # Must be in uses:
                        if unitState[unit] == UNIT_STATE_USES:  # Join uses group
                            unitChunks[unit][-1].add(numInstructions-idx-1)

                        else:   # create new uses group
                            unitChunks[unit].append(set([numInstructions - idx - 1]))
                            unitState[unit] = UNIT_STATE_USES

            availableInstructions = ListDict(range(numInstructions))
            notReady = [0 for _ in range(numInstructions)]  # notReady[ins] = how many units are not ready fo ins

            # Loop over all chunks of units that are not the first chunk and update notReady
            for unit in range(FileData.TextSegment.Instruction.NUM_UNITS):
                for chunk in unitChunks[unit][:-1]:
                    for ins in chunk:
                        if notReady[ins] == 0:
                            availableInstructions.remove_item(ins)   # At least 'unit' isn't ready for 'ins'
                        notReady[ins] += 1

            # Adding in available commands at random:
            while len(availableInstructions) != 0:
                ins = availableInstructions.choose_random_item()
                availableInstructions.remove_item(ins)
                chosenInstruction = copy.deepcopy(procInstructions[ins])

                tmpProcInstructions.append(chosenInstruction)    # Adding chosen instruction

                # Updating units chunks:
                for unit in chosenInstruction.includes:
                    unitChunks[unit][-1].remove(ins)

                    # If we removed last instructions in chunk then unit is ready for next chunk-
                    if len(unitChunks[unit][-1]) == 0:
                        unitChunks[unit].pop()
                        if len(unitChunks[unit]) != 0:
                            for readyIns in unitChunks[unit][-1]:
                                notReady[readyIns] -= 1
                                if notReady[readyIns] == 0:     # Now every unit is ready
                                    availableInstructions.add_item(readyIns)

            fd.textSegments[tsIdx].processes[procName] = tmpProcInstructions

    return fd


def applyTechniques(file: str, newLocation: str, techniques: Techniques):

    """
        Function to apply given techniques to a file and save the result.

        arg 'file': the location of the file to which to apply the techniques
        arg 'newLocation': the location to which to save the resulting file
        arg 'techniques': instance of 'Techniques' object specifying which techniques to apply
    """

    fd = FileData(file)
    for technique in techniques.techniqueFunctions:
        fd = technique(fd)

    fd.saveFile(newLocation)
