
from typing import List     # Used for type hinting
import copy                 # Used for non reference copies (shallow & deep)


# A class encapsulating the information in a compiled c file (.asm).
class FileData:

    # In this class when the term 'line(s)' is used the meaning is
    #   an array of strings originally separated by whitespace.

    # A class encapsulating the information in a 'text' segment
    class TextSegment:
        def __init__(self):
            """Default constructor"""

            self.data = dict()  # Dictionary of data inside segment, each element in form of [name: value]
            self.processes = dict()  # Dictionary of processes in segment in form [name: lines]
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
                        self.textSegments[textSegmentIdx].processes[processName].append(line)
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

    neighbors = ['+', '[', ']', ',', ' ']

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
        return line

    if line[0][-1:] != ':':     # Incorrect format for a label line
        return line

    if line[0][:-1] == oldName:
        return [newName + ':']


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

        for procName, procLines in t.processes.items():
            tmpFunctions.append(procName)
            tmpProcLines = []
            for line in procLines:
                if line[0] == 'call':                       # Calling another function which we might inline
                    funcName = line[1]
                    if funcName in fd.functions:            # If function is defined locally then we can inline it
                        funcSeg = fd.textSegments[fd.functions[funcName]]
                        funcLines = funcSeg.processes[funcName]
                        tmpFuncLines = funcLines[:]         # Temporary array for storing lines after alterations

                        # Insert data:
                        for dataName, dataValue in funcSeg.data.items():
                            newName = dataName
                            while newName in tmpSeg.data:   # Name conflict
                                newName = increaseName(newName)

                            tmpSeg.data[newName] = dataValue

                            tmpFuncLines = [swapNames(line = funcLine, oldName = dataName, newName = newName) for funcLine in tmpFuncLines]

                        # Fix label conflicts:
                        for label in funcSeg.labels:
                            newName = label
                            while newName in tmpFileData.labels:
                                newName = increaseName(newName)

                            tmpSeg.labels.append(newName)
                            tmpFileData.labels.append(newName)
                            tmpFuncLines = [swapLabels(line = funcLine, oldName = label, newName = newName) for funcLine in tmpFuncLines]

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

                        # TODO: make sure code works on all frameworks. E.g. 'esp' might not be correct for non x32's.
                        #   Alternatively we can decide if we want to restrict the code to a specific framework-
                        #   I think prof might have said something about x64, needs checking.
                    else:
                        tmpProcLines.append(line)
                else:
                    tmpProcLines.append(line)

            tmpSeg.processes[procName] = tmpProcLines

        tmpFileData.textSegments.append(tmpSeg)
        index = len(tmpFileData.textSegments) - 1
        for funcName in tmpFunctions:
            tmpFileData.functions[funcName] = [True, index]

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
        self.techniqueOrder__.append('functionInlining')
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
