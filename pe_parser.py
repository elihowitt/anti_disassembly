"""
    The purpose of this module is to provide the functionality of
        extracting a PE's code segment, disassembling the segment and separating its processes into code sections.

    Authors: Eli Howitt & Malachi Machpod.
"""

import pefile               # Used for parsing PEs.
from capstone import *      # Used for disassembly.
import bintrees             # Used for AVL data structure to store code sections.

LONGEST_INSTRUCTION_LENGTH = 15  # Length of longest asm x86 instruction in bytes.

# Control flow instruction mnemonics. Taken from https://en.wikibooks.org/wiki/X86_Assembly/Control_Flow.

controlFlowMnemonics = ['call', 'ret', 'jmp', 'je', 'jne', 'jg', 'jge', 'ja', 'jae', 'jl', 'jle',
                        'jb', 'jbe', 'jo', 'jno', 'jz', 'jnz', 'js', 'jns', 'jcxz', 'jecxz', 'jrcxz',
                        'loop', 'loope', 'loopne', 'loopnz', 'loopz']

conditionalJumpMnemonics = ['je', 'jne', 'jg', 'jge', 'ja', 'jae', 'jl', 'jle',
                        'jb', 'jbe', 'jo', 'jno', 'jz', 'jnz', 'js', 'jns', 'jcxz', 'jecxz', 'jrcxz',
                        'loop', 'loope', 'loopne', 'loopnz', 'loopz']


# Taken from https://portingguide.readthedocs.io/en/latest/comparisons.html.
def cmp(x, y):
    """
    Replacement for built-in function cmp that was removed in Python 3

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    """

    return (x > y) - (x < y)


class CodeSection:
    startAddress = -1  # Start address relative to beginning of code section.
    endAddress = -1  # End address relative to beginning of code section.
    isInitialized = False  #

    # For now assume no overlap, otherwise a field like the following might be necessary:
    # instructionAddresses = []     # Addresses of all instructions, used to check if -
    # - a jump is made to mid-command.

    instructions = []       # The instructions themselves.
    references = set()      # References to section.
    connection = -1         # Address of section that is a connection to this (i.e. an immediate continuation.

    def __cmp__(self, other):
        return cmp(self.startAddress, other.startAddress)


def getCodeSections(codeStr, codeAddress, entryAddress, md):
    """
    Divides the code into independent 'CodeSection's.

    :param codeStr: byte string of code sections.
    :param codeAddress: offset of code section relative to file.
    :param entryAddress: offset of entry point relative to file.
    :param md: capstone Cs object to disassemble with.
    :return: list of 'CodeSection's of program.
    """

    # Address of last byte in code section, used to check if target is inside section.
    lastAddress = codeAddress + len(codeStr)


    # Class representing data about a target.
    class Target:
        loc = -1
        reference = -1

        def __init__ (self, loc_, reference_):
            self.loc = loc_
            self.reference = reference_

    # AVL for fast search and insert, where starting location is the key and the CodeSection is the value.
    sections = bintrees.AVLTree()

    # 'Stack' of targets to analyze.
    targets = [Target(loc_=entryAddress, reference_=None)]

    while len(targets) > 0:
        t = targets.pop()

        # TODO: check that target is in code section and not some imported function.
        # TODO NT: maybe this is enough for now -
        if t.loc < codeAddress or t.loc > lastAddress:
            continue

        isNewSection = False    # If target is a new section to be analyzed.
        isFirst = False         # If target points the to vey first section (in order of analysis).
        isLast = False          # If target points to section last in order of address (so as to know if it could connect with the next).
        comingAddress = -1      # The start of the next section starting after target.
        comingSection = -1      # The section starting after target.


        if sections.is_empty():     # First section in order of analysis
            isNewSection = True
            isFirst = True

        elif t.loc < sections.min_key():    # First section in order of address
            isNewSection = True
            comingAddress, comingSection = sections.min_item()

        elif sections.__contains__(t.loc):      # Section already analyzed
            sections[t.loc].references.add(t.reference)

        else:
            prevStart, prevSection = sections.floor_item(t.loc)
            if t.loc <= prevSection.endAddress:     # Target mid-section
                split = CodeSection()               # The second half of the section being split
                split.startAddress = t.loc
                split.endAddress = prevSection.endAddress
                split.references.add(t.reference)
                split.connection = prevSection.connection

                # TODO: binary search instructions (or save them in set) and split them. | I think it's done
                #  and set new endAddress for prevSection.
                #   prevSection | split
                section_help = prevSection.instructions[:]

                index = 0
                for i in range(len(section_help)):
                    if section_help[i].address == t.loc:
                        index = i
                        break

                prevSection.instructions = section_help[:index]
                split.instructions = section_help[index:]

                prevSection.connection = t.loc
                sections.insert(t.loc, split)
                sections[prevStart] = prevSection


            else:
                isNewSection = True
                if t.loc > sections.max_key():  # Last condition checked if it was inside a section.
                    isLast = True
                else:
                    comingAddress, comingSection = sections.ceil_key(t.loc)

        if isNewSection:    # Analyse new code section.
            s = CodeSection()
            ins = None
            loc = t.loc
            while ins is None or ins.mnemonic not in controlFlowMnemonics:

                ins = md.disasm(codeStr[loc - codeAddress], loc, 1)      # disassemble one instruction at a time
                s.instructions.append(ins)
                if ins.mnemonic in controlFlowMnemonics:

                    # TODO: find targetAddress -
                    # TODO NOT: does this work?
                    targetAddress = int(ins.op_str, 16)  # look weird

                    if ins.mnemonic == 'jmp':
                        s.endAddress = ins.address
                        s.isInitialized = True
                        targets.insert(Target(loc_=targetAddress, reference_=ins.address))

                    elif ins.mnemonic in conditionalJumpMnemonics:
                        s.endAddress = ins.address
                        s.isInitialized = True
                        targets.insert(Target(loc_=targetAddress, reference_=ins.address))
                        s.connection = loc + ins.size
                        targets.insert(Target(loc_=s.connection, reference_=ins.address))

                    elif ins.mnemonic == 'call':
                        targets.insert(Target(loc_=targetAddress, reference_=ins.address))
                    else:       # 'ret'
                        s.endAddress = ins.address
                        s.isInitialized = True

                if s.isInitialized:
                    break

                if not isFirst and not isLast and loc+ins.size == comingAddress: # reached another section (
                    s.endAddress = loc
                    s.connection = loc + ins.size
                    s.isInitialized = True
                    break

                else:
                    loc += ins.size  # Increment ;instruction pointer'

    return sections






def main():
    print('My main is name', end='\n')

    loc = "./test_file.exe"

    pe = pefile.PE(loc)
    code = pe.sections[0].get_data()

    md = Cs(CS_ARCH_X86, CS_MODE_64)


if __name__ == '__main__':
    main()
