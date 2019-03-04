from os import walk, getcwd


def get_articles_name():
    mypath = getcwd() + '/data/'
    print(mypath)
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break

    files_name = ["~/stud/search/data/" + x for x in f]

    return files_name
