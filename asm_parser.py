
# A class encapsulating the information in a compiled c file (.asm).
class FileData:

    # In this class when the term 'line(s)' is used the meaning is
    #   an array of strings originally separated by whitespace.

    # A class encapsulating the information in a 'text' section
    class Text:

        # data = []          # Array of lines of data in section

        data = dict()       # Dictionary of data inside section, each element in form of [(str)name: (str)value]
        processes = dict()  # Dictionary of processes in section in form [name: lines]

    '''
    lines = []
    functions = {}      # func name -> is internal, lines
    '''

    functions = dict()  # Dictionary mapping function names to
                        # corresponding parent 'Text' objects index in 'texts' array and
                        # a flag representing whether the function is local to the file in the form [isLocal, index]

    data = []           # Array of lines belonging to data sections
    texts = []          # Array of text section information in form of 'Text' objects


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
    # TODO: implement this function.
    """
        Utility function to replace old names with new ones in a line of code.

    arg 'line': the line of code in which to search for replacements
    arg oldName: the old name of the variable
    arg newName: the newName of the variable

    returns: the line after the swaps (if any)
    """

    pass

def functionInlining(fd : FileData):
    '''
    lines_ = fd.lines[:]
    for k,v in fd.functions.items():
        if v[0]:
            [i, j] = v[1:]
            while i < j:
                parts = lines_[i].split()
                if parts[0] == 'call':
                    name = parts[1]
                    a = fd.functions[name]
                    if a[0]:
                        lines_ = lines_[:i] + fd.lines[a[1][0], a[1][1]] + lines_[i:]
                        i += a[1][1] - a[1][0]
                        j += a[1][1] - a[1][0]
                    else:
                        i += 1
                else:
                    i += 1
    fd.lines = lines_
    return fd
    '''

    tmpFileData = FileData()

    for t in fd.texts:
        tmpSec = FileData.Text()        # Temporary section for storing changes
        tmpSec.data = t.data[:]

        tmpFunctions = []               # Array of functions processed in current section, used to fix 'functions' dict

        for procName, procLines in t.processes.items():
            tmpFunctions.append(procName)
            tmpProcLines = []
            for line in procLines:
                if line[0] == 'call':                       # Calling another function which we might inline
                    f = fd.functions[line[1]]
                    if f[0]:                                # If function is defined locally then we can inline
                        funcName = f[1]
                        funcSec = fd.texts[funcName]
                        funcLines = funcSec.processes[funcName]
                        tmpFuncLines = funcLines[:]         # Temporary array for storing lines after alterations

                        # Insert data:
                        for dataName, dataValue in funcSec.data.items():
                            newName = dataName
                            while newName in tmpSec.data:   # Name conflict
                                newName = increaseName(newName)

                            tmpSec.data[newName] = dataValue

                            tmpFuncLines = [swapNames(line = funcLine, oldName = dataName, newName = newName) for funcLine in tmpFuncLines]

                        # Insert function:
                        tmpProcLines.append(tmpFuncLines)
                        # TODO: fix issue with 'return' command in inlined function code
                        #  also, I like how TODOs are yellow so I added another comment here
                    else:
                        tmpProcLines.append(line)
                else:
                    tmpProcLines.append(line)

            tmpSec.processes[procName] = tmpProcLines

        tmpFileData.texts.append(tmpSec)
        index = len(tmpFileData.texts) - 1
        for funcName in tmpFunctions:
            tmpFileData.functions[funcName] = [True, index]

    # TODO: sort other parts of file data e.g. other sections.
    return tmpFileData





def manager(file, settings):

    with open(file) as f:
        # Sanitize empty lines and comments
        lines = [line.split() for line in f.read().splitlines() if
                 len(line) != 0 and len(line.split()) != 0 and line[0] != ';']

    # TODO: parse lines and determine a 'FileData' object to use in different techniques.





def main():
    print("my main is name!")


if __name__ == "__main__":
    main()
