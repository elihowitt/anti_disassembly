import tkinter
from tkinter import *
from tkinter.filedialog import askopenfilename
import os
from techniques import *

def main():

    defaultRemoveStr = 'select file to remove'

    # Refreshes the files dropdown menu.
    def refreshFiles():
        varRemove.set(defaultRemoveStr)
        removeMenue['menu'].delete(0, 'end')

        for file in selectedFiles:
            removeMenue['menu'].add_command(label=file, command=tkinter._setit(varRemove, file))

    def funcAddFile():
        location = askopenfilename()
        if location not in selectedFiles:
            selectedFiles.add(location)
            refreshFiles()

    def funcRemoveFile():
        if varRemove == defaultRemoveStr:
            return
        else:
            selectedFiles.remove(varRemove.get())
            refreshFiles()

    def funcGenExe():
        # for vs 2022
        os.system("C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars32.bat")
        os.system("cl /FA " + ' '.join(selectedFiles))

        techniques = Techniques(applies_functionInlining=varFI, applies_junkCode=varJC, applies_permuteLines=varPL)

        newLocations =[]
        for i in selectedFiles:
            location = i[:]
            newLocation = i.removesuffix('.asm') + "AD.asm"
            newLocations += [newLocation]
            applyTechniques(location, newLocation, techniques)


        os.system("ml /c " + ' '.join(newLocations))
        newLocationsOBJ = []
        for i in newLocations[:]:
            newLocation = i.removesuffix('.asm') + ".obj"
            newLocationsOBJ += [newLocation]

        name = "junky.exe" #############################################  make better way change name
        os.system("link /FORCE:MULTIPLE /OUT:" + name + ' '.join(newLocationsOBJ))

        location = txtTarget.get("1.0", 'end-1c')
        print(location)

    selectedFiles = set([defaultRemoveStr])

    root = Tk()
    root.title('Nudnik')
    root.geometry('800x200')

    varFI = IntVar()
    varJC = IntVar()
    varPL = IntVar()

    cbFunctionInlining = Checkbutton(root, text="Function Inlining", variable=varFI)
    cbJunkCode = Checkbutton(root, text="Junk Code", variable=varJC)
    cbPermuteLines = Checkbutton(root, text="Permute Lines", variable=varPL)

    cbFunctionInlining.place(x=0, y=0)
    cbJunkCode.place(x=0, y=30)
    cbPermuteLines.place(x=0, y=60)

    varRemove = StringVar(root)
    varRemove.set("Select file to remove")

    btnAddFile = Button(root, text="Add file", command=funcAddFile).place(x=200, y=0)
    btnRemove = Button(root, text="Remove file", command=funcRemoveFile).place(x=200, y=60)

    removeMenue = OptionMenu(root, varRemove, *selectedFiles)
    removeMenue.place(x=200, y=30)

    txtTarget = Text(root, width = 40, height = 2, bg = "light gray")
    txtTarget.place(x=420, y=60)

    btnGenExe = Button(root, text="generate executable", command=funcGenExe)
    btnGenExe.place(x=420, y=30)

    refreshFiles()



    root.mainloop()




if __name__ =='__main__':
    main()
