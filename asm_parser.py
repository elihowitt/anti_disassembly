
from typing import List, Dict       # Used for type hinting
import copy                         # Used for non reference copies (shallow & deep)
from fileData import *
from techniques import *


def main():
    print("my main is name!")

    print("\nEnter location of file to apply function inlining to: ")
    location = input()

    print("\nEnter location to which the file would be saved after applying said change(s): ")
    newLocation = input()

    techniques = Techniques(applies_functionInlining=False, applies_junkCode=True, applies_permuteLines=True)
    applyTechniques(location, newLocation, techniques)


if __name__ == "__main__":
    main()
