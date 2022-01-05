
# Utility function for changing names to avoid conflicts
def increaseName(name: str, boost=1) -> str:
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

    return name[:l - i] + str(num+boost)


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


