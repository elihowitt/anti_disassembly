


class fileData:
    lines = []              #
    functions = {}          # func name -> is internal, lines



def functionInlining(fd):
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












def manager(file, settings):
    with open(file) as f:
        lines = f.read().splitlines()








def main():
    print("my main is name!")







if __name__ == "__main__":
    main()
