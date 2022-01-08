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

            # A class representing the properties of an argument in an instruction
            class Argument:
                def __init__(self, arg: str):
                    self.isPointer: bool = False    # Whether argument is of pointer type
                    self.includes: List[int] = []   # Array of indices of registers included in argument

                    # TODO: correctly implement this!
                    # Parse argument:
                    if 'PTR' in arg:
                        self.isPointer = True
                        arg = arg[arg.rfind('['): arg.rfind(']') + 1]

                    else:       # to allow single check for pointer an non pointer.
                        arg = '[' + arg + ']'

                    validNeighbors = ['[', '+', '-', '*', ']', ' ']
                    for unitIdx, names in FileData.TextSegment.Instruction.registerNames.items():
                        for name in names:
                            nameLen = len(name)
                            appearanceIdx = arg.find(name)
                            while appearanceIdx != -1:
                                if appearanceIdx > 0 and \
                                        arg[appearanceIdx-1] in validNeighbors and \
                                        arg[appearanceIdx+nameLen] in validNeighbors:
                                    self.includes.append(unitIdx)
                                    break
                                appearanceIdx = arg.find(name, appearanceIdx + nameLen)

                            if unitIdx in self.includes:
                                break



            def __init__(self, line):
                self.line = copy.deepcopy(line)
                self.changes = [False for _ in range(FileData.TextSegment.Instruction.NUM_UNITS)]
                self.uses = copy.deepcopy(self.changes)

                # Test against instructions we support and set 'changes' and 'uses' accordingly:
                # All unsupported instructions will be assumed to change and use everything.
                if len(line) == 0:
                    return

                ins = line[0]

                if ins in FileData.TextSegment.Instruction.CONTROL_FLOW_MNEMONICS:
                    self.changeAll()
                    self.useAll()

                elif ins in FileData.TextSegment.Instruction.INSTRUCTIONS_NO_ARGS:
                    if ins == 'cdq':
                        self.uses[self.RAX_IDX] = True
                        self.changes[self.RDX_IDX] = True

                elif ins in FileData.TextSegment.Instruction.INSTRUCTIONS_ONE_ARG:
                    arg = FileData.TextSegment.Instruction.Argument(' '.join(line[1:]))

                    if ins == 'pop':
                        self.uses[self.RSP_IDX] = True
                        self.changes[self.RSP_IDX] = True
                        self.changes[self.MEM] = True
                        self.uses[self.MEM] = True

                        if arg.isPointer:
                            for unit in arg.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg.includes:
                                self.changes[unit] = True

                    elif ins == 'push':
                        self.uses[self.RSP_IDX] = True
                        self.changes[self.RSP_IDX] = True
                        self.changes[self.MEM] = True
                        self.uses[self.MEM] = True

                        for unit in arg.includes:
                            self.uses[unit] = True

                    elif ins == 'inc' or ins == 'dec':
                        self.changes[self.PF_IDX] = True
                        self.changes[self.AF_IDX] = True
                        self.changes[self.ZF_IDX] = True
                        self.changes[self.SF_IDX] = True
                        self.changes[self.OF_IDX] = True

                        if arg.isPointer:
                            self.uses[self.MEM] = True
                            self.changes[self.MEM] = True
                            for unit in arg.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg.includes:
                                self.changes[unit] = True
                                self.uses[unit] = True

                elif ins in FileData.TextSegment.Instruction.INSTRUCTIONS_TWO_ARGS:
                    linePart1, linePart2 = (' '.join(line[1:])).split(',')
                    arg1 = FileData.TextSegment.Instruction.Argument(linePart1)
                    arg2 = FileData.TextSegment.Instruction.Argument(linePart2)
                    if ins == 'mov':
                        if arg1.isPointer:
                            self.changes[self.MEM] = True
                            for unit in arg1.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg1.includes:
                                self.changes[unit] = True

                        if arg2.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg2.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg2.includes:
                                self.uses[unit] = True

                    elif ins == 'add' or ins == 'sub' or ins == 'xor' or ins == 'and' or ins == 'or':
                        self.changes[self.PF_IDX] = True
                        self.changes[self.CF_IDX] = True
                        self.changes[self.AF_IDX] = True
                        self.changes[self.ZF_IDX] = True
                        self.changes[self.SF_IDX] = True
                        self.changes[self.OF_IDX] = True

                        if arg1.isPointer:
                            self.changes[self.MEM] = True
                            self.uses[self.MEM] = True
                            for unit in arg1.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg1.includes:
                                self.changes[unit] = True
                                self.uses[unit] = True

                        if arg2.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg2.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg2.includes:
                                self.uses[unit] = True

                    elif ins == 'cmp':
                        self.changes[self.PF_IDX] = True
                        self.changes[self.CF_IDX] = True
                        self.changes[self.AF_IDX] = True
                        self.changes[self.ZF_IDX] = True
                        self.changes[self.SF_IDX] = True
                        self.changes[self.OF_IDX] = True

                        if arg1.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg1.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg1.includes:
                                self.uses[unit] = True

                        if arg2.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg2.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg2.includes:
                                self.uses[unit] = True

                    elif ins == 'test':
                        self.changes[self.PF_IDX] = True
                        self.changes[self.CF_IDX] = True
                        self.changes[self.AF_IDX] = True
                        self.changes[self.ZF_IDX] = True
                        self.changes[self.SF_IDX] = True
                        self.changes[self.OF_IDX] = True

                        if arg1.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg1.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg1.includes:
                                self.uses[unit] = True

                        if arg2.isPointer:
                            self.uses[self.MEM] = True
                            for unit in arg2.includes:
                                self.uses[unit] = True
                        else:
                            for unit in arg2.includes:
                                self.uses[unit] = True


                    elif ins == 'lea':
                        self.uses[self.MEM] = True

                        for unit in arg1.includes:
                            self.changes[unit] = True

                        for unit in arg2.includes:
                            self.uses[unit] = True



                else:   # unsupported instruction, assume 'the worst'.
                    self.changeAll()
                    self.useAll()

                # Array of units included in instruction regardless of what they do
                self.includes = [unit for unit in range(FileData.TextSegment.Instruction.NUM_UNITS)
                                 if self.uses[unit] or self.changes[unit]]

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

            # Arrays of instructions grouped by amount og arguments they take:
            INSTRUCTIONS_NO_ARGS = ['cdq']
            INSTRUCTIONS_ONE_ARG = ['pop', 'push', 'inc']
            INSTRUCTIONS_TWO_ARGS = ['mov', 'add', 'sub', 'lea', 'xor', 'cmp', 'test', 'and', 'or']

            # Array of control flow instruction mnemonics we assume change and use everything:
            CONTROL_FLOW_MNEMONICS = [
                'call', 'ret', 'jmp', 'je', 'jne', 'jg', 'jge', 'ja', 'jae', 'jl', 'jle',
                'jb', 'jbe', 'jo', 'jno', 'jz', 'jnz', 'js', 'jns', 'jcxz', 'jecxz', 'jrcxz',
                'loop', 'loope', 'loopne', 'loopnz', 'loopz', 'ret']

            # Number of registers (or other memory units we may track):
            NUM_UNITS = 15

            # Register indices:
            RAX_IDX = 0
            RBX_IDX = 1
            RCX_IDX = 2
            RDX_IDX = 3
            RSI_IDX = 4
            RDI_IDX = 5
            RBP_IDX = 6
            RSP_IDX = 7

            # Flag bits indices:
            CF_IDX = 8
            PF_IDX = 9
            AF_IDX = 10
            ZF_IDX = 11
            SF_IDX = 12
            OF_IDX = 13

            # Memory
            MEM = 14

            # Dictionary mapping register index to portion names:
            registerNames = dict()
            registerNames[RAX_IDX] =   ['eax', 'ax', 'ah', 'al']
            registerNames[RBX_IDX] =   ['ebx', 'bx', 'bh', 'bl']
            registerNames[RCX_IDX] =   ['ecx', 'cx', 'ch', 'cl']
            registerNames[RDX_IDX] =   ['edx', 'dx', 'dh', 'dl']
            registerNames[RSI_IDX] =   ['esi', 'si']
            registerNames[RDI_IDX] =   ['edi', 'di']
            registerNames[RBP_IDX] =   ['ebp', 'bp']
            registerNames[RSP_IDX] =   ['esp', 'sp']


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
                    self.miscSegments[currSegment] = [line]
                elif len(line) == 2 and line[1] == 'ENDS':
                    currSegment = None
                else:
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
            for procName, procInstructions in ts.processes.items():
                lines.append([procName, 'PROC'])
                lines.extend([ins.line for ins in procInstructions])
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
