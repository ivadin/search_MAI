import pickle
from indexr.buildr import SPIMI, build_index, BSB

import os
from shutil import copyfile
from os import walk
import datetime
import sys

sys.path.append('..')

from l5_index.l5 import timer, save_obj, load_obj, read_index_title_and_url


class CustomSPIMI(SPIMI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.postings = None
        self.dictionary = None
        self.files = None

    def initialize(self, files, index_path):
        super().initialize(files, index_path)
        with open(self.get_index_path(), 'rb') as handle:
            self.postings, self.dictionary, self.files = pickle.load(handle)

    def search(self, token, **kwargs):
        frequencies = kwargs.get('frequencies', False)
        if frequencies:
            result = {}
        else:
            result = []
        # Check whether the token is in the dictionary
        if token not in self.dictionary.keys():
            return []
        token_id = self.dictionary[token]
        token_postings = self.postings[token_id]
        doc_id = 0
        # Loop through all document gaps
        for doc_gap in token_postings:
            doc_id += doc_gap
            file = self.files[doc_id]
            if frequencies:
                # Case for frequencies
                if doc_gap == 0 and doc_id > 0:
                    result[doc_id] += 1
                else:
                    result[doc_id] = 1
            else:
                # Case for occurrences
                if doc_gap > 0:
                    result.append(doc_id)
        return result


@timer
def main():
    total_count = 6000000 * 40

    max_count = int(total_count * 0.005)

    my_dict = {}

    read_index_title_and_url()
    t_start = datetime.datetime.now()

    for i in range(max_count):
        my_dict[i] = [1, 2, 3]

        if not i % 10000:
            print(f"Выполнено {100 * i // max_count}%. Время {datetime.datetime.now() - t_start}")
    print("Выполнено 100%. Сохраняем объект")
    save_obj(my_dict, 'INDEX')
    print("Объект сохранен")


@timer
def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def get_articles_name(dn, is_absolute=False):
    if not is_absolute:
        mypath = '../' + dn + '/'
    else:
        mypath = dn
    f = []
    # import pdb
    # pdb.set_trace()
    for (dirpath, dirnames, filenames) in walk(mypath):
        for filename in filenames:
            f.append(mypath + filename)
        break
    files_name = f

    return files_name


@timer
def gen_files(dn):
    mypath = '../' + dn + '/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        j = 0
        additional = 4
        for i in range(max(1, additional)):
            for filename in filenames:
                j += 1
                filename_wothour_ext = filename[:len(filename) - 4]
                new_filename = f"../../data_raw/{filename_wothour_ext}({i}).txt"
                copyfile(mypath+filename, new_filename)

                sys.stdout.write("\rCreating: " + f'{j} / {additional*len(filenames)}')
                sys.stdout.flush()

        print("\nComplete")
        break
    files_name = f

    return files_name


def old_search(files):
    index = SPIMI()
    index.initialize(files, './index')
    t = datetime.datetime.now()
    print(len(index.find('мастер', frequencies=True)))
    print(datetime.datetime.now() - t)
    print(len(index.find('мастер', frequencies=True)))
    print(datetime.datetime.now() - t)
    print(len(index.find('мастер', frequencies=True)))


def new_search(files):

    index = BSB()
    index.initialize(files, './indexBSB')
    t = datetime.datetime.now()
    print(len(index.find('мастер', frequencies=True)))
    print(datetime.datetime.now() - t)
    # print(len(index.search('мастер', frequencies=True)))
    # print(datetime.datetime.now() - t)
    # print(len(index.search('мастер', frequencies=True)))


if __name__ == '__main__':
    # main()
    gen_files('../Статьи_КП')

    # t = datetime.datetime.now()
    # files = get_articles_name('../../data_raw/', is_absolute=True)

    # print(len(files))
    # build_index(files, 'indexBSB', force_rebuild=True, indexer=BSB(show_progress=True))

    # old_search(files)
    # print("---------------")
    # new_search(files)






