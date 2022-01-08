import tkinter
from tkinter import *
from tkinter.filedialog import askopenfilename
from techniques import *

def main():

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

    def funcGenerate():
        if defaultRemoveStr in selectedFiles:
            selectedFiles.remove(defaultRemoveStr)

        outLocation = txtTarget.get("1.0", 'end-1c')

        techniques = Techniques(applies_functionInlining=varFI.get(),
                                applies_junkCode=varJC.get(), applies_permuteLines=varPL.get())

        for file in selectedFiles:
            filename = file[file.rfind('/')+1: file.rfind('.asm')]
            newLocation = outLocation + '\\\\' + filename + '_nudnik.asm'
            applyTechniques(file, newLocation, techniques)

    defaultRemoveStr = 'select file to remove'
    selectedFiles = set([defaultRemoveStr])

    root = Tk()
    root.title('Nudnik')
    root.geometry('800x200')

    # Variables regarding which techniques to implement
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

    btnAddFile = Button(root, text="Add file", command=funcAddFile)
    removeMenue = OptionMenu(root, varRemove, *selectedFiles)
    btnRemove = Button(root, text="Remove file", command=funcRemoveFile)

    btnAddFile.place(x=200, y=0)
    removeMenue.place(x=200, y=30)
    btnRemove.place(x=200, y=60)

    txtTarget = Text(root, width = 40, height = 2, bg = "light gray")
    txtTarget.place(x=420, y=60)

    btnGenExe = Button(root, text="Generate files", command=funcGenerate)
    btnGenExe.place(x=420, y=30)

    refreshFiles()

    root.mainloop()




if __name__ =='__main__':
    main()
