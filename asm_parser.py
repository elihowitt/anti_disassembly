
from typing import List, Dict       # Used for type hinting
import copy                         # Used for non reference copies (shallow & deep)
from fileData import *
from techniques import *

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

    techniques = Techniques(applies_functionInlining=False, applies_junkCode=True, applies_permuteLines=False)
    applyTechniques(location, newLocation, techniques)


if __name__ == "__main__":
    main()
