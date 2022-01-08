import random
from fileData import *

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


def getJunkInstruction(canChange):
        # Utility function for creating junk instructions that change 'reg' register

        changeFlagsPCAZSO = ['add', 'sub', 'xor', 'and', 'or', 'cmp', 'test']
        changeFlagsPAZSO_oneArg = ['inc', 'dec']

        # TODO: add support for more intricate instructions (& pass to funct available flags!),-
        #  and pointer type arguments.

        registerRange = 7
        smallOptionRegisters = [FileData.TextSegment.Instruction.RSP_IDX, FileData.TextSegment.Instruction.RBP_IDX,
            FileData.TextSegment.Instruction.RSI_IDX, FileData.TextSegment.Instruction.RDI_IDX]

        registers = [i for i in canChange if i <= registerRange]

        probOnearg = 0.15
        if all(flagIdx in canChange
                for flagIdx in [
                FileData.TextSegment.Instruction.CF_IDX,
                FileData.TextSegment.Instruction.PF_IDX,
                FileData.TextSegment.Instruction.AF_IDX,
                FileData.TextSegment.Instruction.ZF_IDX,
                FileData.TextSegment.Instruction.SF_IDX,
                FileData.TextSegment.Instruction.OF_IDX]
            ) and random.random() > probOnearg:
            randCommand = random.choice(changeFlagsPCAZSO)
        elif all(flagIdx in canChange
                for flagIdx in [
                FileData.TextSegment.Instruction.PF_IDX,
                FileData.TextSegment.Instruction.AF_IDX,
                FileData.TextSegment.Instruction.ZF_IDX,
                FileData.TextSegment.Instruction.SF_IDX,
                FileData.TextSegment.Instruction.OF_IDX]
            ):
            randCommand = random.choice(changeFlagsPAZSO_oneArg)
            reg = random.choice(registers)

            nameCeil = 1 if reg in smallOptionRegisters else 3
            arg = FileData.TextSegment.Instruction.registerNames[reg][random.randint(0, nameCeil)]

            return [FileData.TextSegment.Instruction(
                [randCommand, arg])]
        else:
            probNothing = 0.2   # probability that nothing will be inserted whatsoever
            probMov = 0.7       # probability that 'mov' command will be used
            if FileData.TextSegment.Instruction.RSP_IDX not in registers or random.random() > 0.1:
                if random.random() < probNothing:
                    return []
                if random.random() < probNothing + probMov:
                    randCommand = 'mov'
                else:
                    if len(registers) > 1:
                        reg1, reg2 = random.sample(registers, 2)
                        arg1 = FileData.TextSegment.Instruction.registerNames[reg1][0]
                        arg2 = FileData.TextSegment.Instruction.registerNames[reg2][0]
                        randCommand = 'xchg'
                        return[randCommand, arg1+',', arg2]
                    else:
                        return []

            else:
                reg = random.randint(0, registerRange)
                arg = FileData.TextSegment.Instruction.registerNames[reg][0]

                return [FileData.TextSegment.Instruction(
                    ['push', arg]), FileData.TextSegment.Instruction(
                    ['pop', arg])]

        # The probability the second argument will be a number-
        #   theres a preference to use numbers since they wont add 'usage' restriction on the otherwise register.
        probNum = 0.2


        if not registers:
            return [FileData.TextSegment.Instruction([])]
        else:
            reg1 = random.choice(registers)

        if random.random() < probNum:
            nameCeil = 1 if reg1 in smallOptionRegisters else 3
            arg1 = FileData.TextSegment.Instruction.registerNames[reg1][random.randint(0, nameCeil)]
            arg2 = str(random.randint(-64, 64))

        else:

            reg2 = random.randint(0, registerRange) if reg1 not in smallOptionRegisters else \
                random.choice(smallOptionRegisters)

            nameCeil = 1 if (reg1 in smallOptionRegisters or reg2 in smallOptionRegisters) else 3

            nameIdx = random.randint(0, nameCeil)   # Must be same across both registers to match argument size
            arg1 = FileData.TextSegment.Instruction.registerNames[reg1][nameIdx]
            arg2 = FileData.TextSegment.Instruction.registerNames[reg2][nameIdx]

        return [FileData.TextSegment.Instruction(
            [randCommand, arg1 + ',', arg2])]


# Taken from https://stackoverflow.com/questions/15993447/python-data-structure-for-efficient-add-remove-and-random-choice
class ListDict(object):
    def __init__(self):
        self.item_to_position = {}
        self.items = []

    def __init__(self, numRange):
        self.item_to_position = {}
        self.items = []
        for i in numRange:
            self.add_item(i)

    def add_item(self, item):
        if item in self.item_to_position:
            return
        self.items.append(item)
        self.item_to_position[item] = len(self.items)-1

    def remove_item(self, item):
        position = self.item_to_position.pop(item)
        last_item = self.items.pop()
        if position != len(self.items):
            self.items[position] = last_item
            self.item_to_position[last_item] = position

    def choose_random_item(self):
        return random.choice(self.items)

    def __contains__(self, item):
        return item in self.item_to_position

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)