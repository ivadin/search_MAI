import matplotlib.pyplot as plt
import string
from collections import Counter
from os import walk
import json
import re
import numpy as np

PUNCTUATION = string.punctuation + '—«»'
WORD = re.compile(r'\w+')
counter_file = 'counter_for_all.json'


def get_articles_name():
    mypath = '../data/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    files_name = ["~/stud/search/data/" + x for x in f]

    return files_name


if __name__ == "__main__":
    articles = get_articles_name()

    with open(counter_file, 'r') as cf:
        sorted_list = json.load(cf)
    x_point = []
    y_point = []

    x_point_count = 1
    for el in sorted_list:
        y_point.append(np.log(el[1]) * 100)
        x_point.append(np.log(x_point_count) * 100)
        x_point_count += 1

    fig = plt.figure()
    plt.plot(x_point, y_point)
    plt.grid(True)
    plt.title(u'Закон Ципфа')
    plt.xlabel(u'РАНГ')
    plt.ylabel(u'ЧАСТОТА')
    plt.show()
