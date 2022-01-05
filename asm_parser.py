
from typing import List, Dict       # Used for type hinting
import copy                         # Used for non reference copies (shallow & deep)


# A class encapsulating the information in a compiled c file (.asm).
class FileData:

    # In this class when the term 'line(s)' is used the meaning is
    #   an array of strings originally separated by whitespace.

    # A class encapsulating the information in a 'text' segment
    class TextSegment:

        # A class representing the information about an x86 assembly instruction in x64 architecture
        class Instruction:
            def __init__(self, line):
                self.line = copy.deepcopy(line)
                self.changes = [False for _ in range(FileData.TextSegment.Instruction.NUM_UNITS)]
                self.uses = copy.deepcopy(self.changes)

                # Test against instructions we support and set 'changes' and 'uses' accordingly:
                # All unsupported instructions will be assumed to change and use everything.
                if len(line) == 0:
                    return

                ins = line[0]
                if ins == 'mov':
                    arg1, arg2 = (' '.join(line[1:])).split(',', 1)

                    if arg1.find('PTR') != -1:  # Pointer to memory
                        address = arg1[arg1.rfind('['): arg1.rfind(']')+1]
                        validNeighbors = ['[', '+', '-', '*', ']', ' ']
                        for unitIdx, names in FileData.TextSegment.Instruction.registerNames.items():
                            for name in names:
                                nameLen = len(name)
                                appearanceIdx = address.find(name)
                                while appearanceIdx != -1:
                                    if appearanceIdx > 0 and \
                                        address[appearanceIdx-1] in validNeighbors and \
                                        address[appearanceIdx+nameLen] in validNeighbors:

                                        self.uses[unitIdx] = True
                                        break

                                    appearanceIdx = address.find(name, appearanceIdx+nameLen) # Find next appearance

                                if self.uses[unitIdx]:
                                    break

                        self.changeAll() # During memory assignment we assume we change everything

                    else:
                        found = False
                        for unitIdx, names in FileData.TextSegment.Instruction.registerNames.items():
                            for name in names:
                                if name in arg1:
                                    self.changes[unitIdx] = True
                                    found = True
                                    break
                            if found:
                                break

                    if arg2.find('PTR') != -1:  # Pointer to memory
                        address = arg1[arg1.rfind('['): arg1.rfind(']') + 1]
                        validNeighbors = ['[', '+', '-', '*', ']', ' ']
                        for unitIdx, names in FileData.TextSegment.Instruction.registerNames.items():
                            for name in names:
                                nameLen = len(name)
                                appearanceIdx = address.find(name)
                                while appearanceIdx != -1:
                                    if appearanceIdx > 0 and \
                                            address[appearanceIdx - 1] in validNeighbors and \
                                            address[appearanceIdx + nameLen] in validNeighbors:
                                        self.uses[unitIdx] = True
                                        break

                                    appearanceIdx = address.find(name, appearanceIdx + nameLen)  # Find next appearance

                                if self.uses[unitIdx]:
                                    break

                        self.useAll()  # During memory reading we assume we use everything

                    else:
                        found = False
                        for unitIdx, names in FileData.TextSegment.Instruction.registerNames.items():
                            for name in names:
                                if name in arg1:
                                    self.uses[unitIdx] = True
                                    found = True
                                    break
                            if found:
                                break

                    # Change flags if necessary. In move no flags are changed or used.

            def changeAll(self):
                # Utility methode for assigning true to all flags of change.
                # Useful for instructions which we assume change everything like memory assignment.
                for i in range(FileData.TextSegment.Instruction.NUM_UNITS):
                    self.changes[i] = True

            def useAll(self):
                # Utility methode for assigning true to all flags of use.
                # Useful for instructions which we assume uses everything like calling another function.
                for i in range(FileData.TextSegment.Instruction.NUM_UNITS):
                    self.uses[i] = True

            # Array of control flow instruction mnemonics we assume change and use everything:
            CONTROL_FLOW_MNEMONICS = [
                'call', 'ret', 'jmp', 'je', 'jne', 'jg', 'jge', 'ja', 'jae', 'jl', 'jle',
                'jb', 'jbe', 'jo', 'jno', 'jz', 'jnz', 'js', 'jns', 'jcxz', 'jecxz', 'jrcxz',
                'loop', 'loope', 'loopne', 'loopnz', 'loopz']

            # Number of registers (or other memory units we may track):
            NUM_UNITS = 22

            # Register indices:
            RAX_IDX = 0
            RBX_IDX = 1
            RCX_IDX = 2
            RDX_IDX = 3
            RSI_IDX = 4
            RDI_IDX = 5
            RBP_IDX = 6
            RSP_IDX = 7
            R8_IDX = 8
            R9_IDX = 9
            R10_IDX = 10
            R11_IDX = 11
            R12_IDX = 12
            R13_IDX = 13
            R14_IDX = 14
            R15_IDX = 15

            # Flag bits indices:
            CF_IDX = 16
            PF_IDX = 17
            AF_IDX = 18
            ZF_IDX = 19
            SF_IDX = 20
            OF_IDX = 21

            # Dictionary mapping register index to portion names:
            registerNames = dict()
            registerNames[RAX_IDX] = ['rax', 'eax', 'ax', 'al']
            registerNames[RBX_IDX] = ['rbx', 'ebx', 'bx', 'bl']
            registerNames[RCX_IDX] = ['rcx', 'ecx', 'cx', 'cl']
            registerNames[RDX_IDX] = ['rdx', 'edx', 'dx', 'dl']
            registerNames[RSI_IDX] = ['rsi', 'esi', 'si', 'sil']
            registerNames[RDI_IDX] = ['rdi', 'edi', 'di', 'dil']
            registerNames[RBP_IDX] = ['rbp', 'ebp', 'bp', 'bpl']
            registerNames[RSP_IDX] = ['rsp', 'esp', 'sp', 'spl']
            registerNames[R8_IDX] = ['r8', 'r8d', 'r8w', 'r8b']
            registerNames[R9_IDX] = ['r9', 'r9d', 'r9w', 'r9b']
            registerNames[R10_IDX] = ['r10', 'r10d', 'r10w', 'r10b']
            registerNames[R11_IDX] = ['r11', 'r11d', 'r11w', 'r11b']
            registerNames[R12_IDX] = ['r12', 'r12d', 'r12w', 'r12b']
            registerNames[R13_IDX] = ['r13', 'r13d', 'r13w', 'r13b']
            registerNames[R14_IDX] = ['r14', 'r14d', 'r14w', 'r14b']
            registerNames[R15_IDX] = ['r15', 'r15d', 'r15w', 'r15b']

            # Dictionary mapping name of portion of register to register index:
            registerIndex = dict()
            for idx, names in registerNames.items():
                for name in names:
                    registerIndex[name] = idx

        def __init__(self):
            """Default constructor"""

            self.data = dict()  # Dictionary of data inside segment, each element in form of [name: value]

            # Dictionary of processes in segment
            self.processes: Dict[str, FileData.TextSegment.Instruction] = dict()

            self.labels: List[str] = []  # Array of labels used in this specific text segment-
            # (as opposed to labels in 'FileData')

    def __init__(self, file = None):

        """
        Constructor of 'FileData' object given file. Uses 'initialize' to parse the file contents.
        """

        def cutComments(line: [str]):
            """
                Utility function for cutting right-trailing comments of lines
                Assumes ';' of comments would be separated by whitespace, and-
                Assumes no ';' exists in contexts other than comments (suc as string)
            """
            # TODO: fix 2nd assumption of function

            res = []
            for part in line:
                if part != ';':
                    res.append(part)
                else:
                    break
            return res

        self.functions = dict()  # Dictionary mapping function names to
                                 # corresponding parent 'TextSegment' objects index in 'textSegments' array

        self.data: List[str] = []                    # Array of lines belonging to data segments
        self.textSegments: List[FileData.TextSegment] = []    # Array of text segments in file
        self.miscSegments = dict()                   # Dictionary of miscellaneous segments [name:lines]
        self.segmentlessLines: List[str] = []    # Array of all the lines (typically in the beginning of the file)-
                                                 # belonging to no particular segemnt

        self.labels: List[str] = []  # Array of labels used in entire file (as opposed to labels in 'TextSegment')

        if file is None:
            return

        lines = []
        with open(file) as f:
            # Sanitize empty lines and comments
            lines = [cutComments(line.split())
                     for line in f.read().splitlines() if
                     len(line) != 0 and len(line.split()) != 0 and line[0] != ';']

        self.initialize(lines)

    def initialize(self, lines: [[str]]):
        """
            Pseudo-Constructor of 'FileData' object given the lines in a give file.
            The lines are assumed not to include comments or empty lines.
        """

        currSegment = None          # Current segment being parsed
        textSegmentIdx = -1         # Index/count of current text segment being parsed (should there be one)
        inProcess = False           # Whether or not within a text segment we are currently parsing a process
        processName = None          # name of process being parsed (should there be one)

        for line in lines:
            if currSegment is None:                             # Segment-less code
                if line == ['END']:                             # End of file
                    break
                elif len(line) == 2 and line[1] == 'SEGMENT':   # Start of new segment
                    currSegment = line[0]

                    if currSegment == '_TEXT':                  # Start of text segment
                        self.textSegments.append(FileData.TextSegment())
                        textSegmentIdx += 1
                else:
                    self.segmentlessLines.append(line)

            elif currSegment == '_DATA':                        # Data segment
                if line == ['_DATA','ENDS']:                    # End of data segment
                    currSegment = None
                else:
                    self.data.append(line)

            elif currSegment == '_TEXT':                        # Text (code) segment
                if inProcess:
                    if line == [processName, 'ENDP']:           # End of process
                        inProcess = False
                        processName = None
                    else:

                        self.textSegments[textSegmentIdx].processes[processName].append(
                            FileData.TextSegment.Instruction([part for part in line if part != 'SHORT'])
                        )
                        if len(line) == 1 and line[0][-1:] == ':':  # A label
                            labelName = line[0][:-1]
                            self.textSegments[textSegmentIdx].labels.append(labelName)
                            self.labels.append(labelName)

                else:                                               # Not inside process
                    if line == ['_TEXT', 'ENDS']:                   # End of text segment
                        currSegment = None
                    elif len(line) == 2 and line[1] == 'PROC':      # Start of process
                        inProcess = True
                        processName = line[0]
                        self.textSegments[textSegmentIdx].processes[processName] = []
                        self.functions[processName] = textSegmentIdx
                    else:                                           # Data in current text segment
                        self.textSegments[textSegmentIdx].data[line[0]] = line[2]       # E.g. {num = 5}

            else:   # Miscellaneous segment
                if currSegment not in self.miscSegments:
                    self.miscSegments[currSegment] = []
                self.miscSegments[currSegment].append(line)

    def getLines(self) -> [[str]]:

        """
        Utility function/ getter method for-
         the 'lines' (as defined in the beginning of the 'FileData' class) of object
        """

        # Adding segmentless code:
        lines = self.segmentlessLines[:]

        # Adding miscellaneous segments:
        for name, miscLines in self.miscSegments.items():
            lines.append([name, 'SEGMENT'])
            lines.extend(miscLines)
            lines.append([name, 'ENDS'])

        # Adding data segment:
        lines.append(['_DATA', 'SEGMENT'])
        lines.extend(self.data)
        lines.append(['_DATA', 'ENDS'])

        # Adding text segments:
        for ts in self.textSegments:
            lines.append(['_TEXT', 'SEGMENT'])

            # Adding text section data:
            for dataName, dataValue in ts.data.items():
                lines.append([dataName, '=', dataValue])

            # Adding text section processes:
            for procName, procLines in ts.processes.items():
                lines.append([procName, 'PROC'])
                lines.extend(procLines)
                lines.append([procName, 'ENDP'])

            lines.append(['_TEXT', 'ENDS'])

        lines.append(['END'])   # End of file

        return lines

    def saveFile(self, location: str):
        lines = self.getLines()
        with open(location, 'w+') as file:
            for line in lines:
                for word in line:
                    file.write(word + ' ')
                file.write('\n')


# Utility function for changing names to avoid conflicts
def increaseName(name: str) -> str:
    l = len(name)
    if l == 0:
        return '0'

    i = 0                   # Length of number at end of name
    t = 0                   # Length of trialing zeros to the left
    while i+t < l-1 and (ord(name[l-1 - (i+t)]) - ord('0')) in range(0, 10):
        if name[l-1 - (i+t)] == '0':  # Trailing zero
            t += 1
        else:
            i += t + 1
            t = 0

    if i == 0:              # No number was found at end of name
        return name + '1'

    num = 0
    for j in name[l - i:]:
        num *= 10
        num += ord(j) - ord('0')

    return name[:l - i] + str(num+1)


def swapNames(line, oldName, newName):
    """
        Utility function to replace old names with new ones in a line of code.

    arg 'line': the line of code in which to search for replacements
    arg oldName: the old name of the variable
    arg newName: the newName of the variable

    returns: the line after the swaps (if any)
    """

    neighbors = ['+', '-', '*', '[', ']', ',', ' ']

    length = len(oldName)
    line = ' '.join(line)
    i = line.find(oldName)
    newLine = ''
    while i != -1:
        if i > 0 and line[i-1] in neighbors and line[i+length] in neighbors:
            newLine += line[:i] + newName
            line = line[i + length:]
        else:
            newLine += line[:i+length]
            line = line[i+length:]
        i = line.find(oldName)

    newLine += line[:]
    return newLine.split()


def swapLabels(line, oldName, newName):
    """
        Utility function to replace old label names with new ones in a line of code.

    arg 'line': the line of code in which to search for replacements
    arg oldName: the old name of the label
    arg newName: the newName of the label

    returns: the line after the swaps (if any)
    """

    if len(line) != 1:          # Too many or too few parts to be a label
        line = [(newName if part == oldName else part) for part in line]#    if part != 'SHORT']
        return line

    if line[0][-1:] != ':':     # Incorrect format for a label line
        return line

    if line[0][:-1] == oldName:
        return [newName + ':']

    return line

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
            tmpProcInstructions = []
            for instruction in procInstructions:
                line = instruction.line
                if line[0] == 'call':                       # Calling another function which we might inline
                    funcName = line[1]
                    if funcName in fd.functions:            # If function is defined locally then we can inline it
                        funcSeg = fd.textSegments[fd.functions[funcName]]
                        funcInstructions = funcSeg.processes[funcName]

                        # Temporary array for storing instructions after alterations
                        tmpFuncinstructions = funcInstructions[:]

                        # Insert data:
                        for dataName, dataValue in funcSeg.data.items():
                            newName = dataName
                            while newName in tmpSeg.data:   # Name conflict
                                newName = increaseName(newName)

                            tmpSeg.data[newName] = dataValue

                            tmpFuncinstructions = \
                                [
                                    FileData.TextSegment.Instruction
                                    (
                                        swapNames(line = funcIns.line, oldName = dataName, newName = newName)
                                    )
                                    for funcIns in tmpFuncinstructions
                                ]

                        # Fix label conflicts:
                        for label in funcSeg.labels:
                            newName = tmpFileData.labels[len(tmpFileData.labels)-1]
                            while newName in tmpFileData.labels:
                                newName = increaseName(newName)

                            tmpSeg.labels.append(newName)
                            tmpFileData.labels.append(newName)
                            tmpFuncinstructions = \
                                [
                                    FileData.TextSegment.Instruction
                                    (
                                        swapLabels(line = funcIns.line, oldName = label, newName = newName)
                                    )
                                    for funcIns in tmpFuncinstructions
                                ]

                        # Remove return lines:
                        newName = 'Co01Secr3tLabel' if len(tmpFileData.labels) == 0 else tmpFileData.labels[0]
                        while newName in tmpFileData.labels:
                            newName = increaseName(newName)

                        tmpSeg.labels.append(newName)
                        tmpFileData.labels.append(newName)

                        isCallerCleanUp: bool = False   # Whether the callee is cleaning the stack.
                                                        # We assume {ret imm} form indicates such a convention.

                        # Adding a stub in place of {push eip} of call
                        tmpFuncinstructions2 = [FileData.TextSegment.Instruction(['sub', 'esp,', '4'])]
                        for funcIns in tmpFuncinstructions:
                            funcLine = funcIns.line
                            if funcLine[0] == 'ret':
                                if len(funcLine) == 2 and funcLine[1] != '0':
                                    # E.g. 'ret 8' <=> {return and pop 8 bytes from stack}
                                    tmpFuncinstructions2.append(
                                        FileData.TextSegment.Instruction(['add', 'esp,', funcLine[1]]))

                                    isCallerCleanUp = True
                                tmpFuncinstructions2.append(FileData.TextSegment.Instruction(['jmp', newName]))
                            else:
                                tmpFuncinstructions2.append(funcIns)

                        # End-of-inline label
                        tmpFuncinstructions2.append(FileData.TextSegment.Instruction([newName+':']))

                        # Insert function:
                        tmpProcInstructions.extend(tmpFuncinstructions2)
                        if not isCallerCleanUp:                 # Removing stub {pop eip} of ret
                            tmpProcInstructions.append(FileData.TextSegment.Instruction(['add', 'esp,', '4']))

                        # TODO: make sure code works on all frameworks. E.g. 'esp' might not be correct for non x32's.
                        #   Alternatively we can decide if we want to restrict the code to a specific framework-
                        #   I think prof might have said something about x64, needs checking.
                    else:
                        tmpProcInstructions.append(instruction)
                else:
                    tmpProcInstructions.append(instruction)

            tmpSeg.processes[procName] = tmpProcInstructions

        tmpFileData.textSegments.append(tmpSeg)
        index = len(tmpFileData.textSegments) - 1
        for funcName in tmpFunctions:
            tmpFileData.functions[funcName] = index

    return tmpFileData


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
        repeat_functionInlining = 2     # >3 takes time even with small programs-
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


def main():
    print("my main is name!")

    print("\nEnter location of file to apply function inlining to: ")
    location = input()

    print("\nEnter location to which the file would be saved after applying said change(s): ")
    newLocation = input()

    techniques = Techniques(applies_functionInlining=True)
    applyTechniques(location, newLocation, techniques)


if __name__ == "__main__":
    main()
