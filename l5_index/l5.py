import pickle
import struct
import json
from os import walk
from datetime import datetime
from collections import defaultdict

FORMAT_TO_BINARY = 'q'
SIZE_OF_ONE_ELEM = 8
URL_PREFFIX = 'https://ru.wikipedia.org/wiki/'


def timer(func):
    def wraper(*args, **kwargs):
        t1 = datetime.now()
        res = func(*args, **kwargs)
        print("%s works %s" % (func.__name__, datetime.now() - t1))
        return res
    return wraper


def get_articles_name(dn):
    mypath = '../' + dn + '/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    files_name = f

    return files_name


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def write_n_digits_to_binary_doc_id(list_of_digits, file_name):
    with open(file_name, 'wb') as f:
        n = len(list_of_digits)
        frm = str(n) + FORMAT_TO_BINARY
        value_to_write = struct.pack(frm, *list_of_digits)
        f.write(value_to_write)


def read_form_binary_doc_id(offset, file_name, pos_in_file=0):
    with open(file_name, 'rb') as f:
        f.seek(pos_in_file * SIZE_OF_ONE_ELEM)
        values = f.read(offset*SIZE_OF_ONE_ELEM)
        frm = str(offset) + FORMAT_TO_BINARY
        return struct.unpack(frm, values)


@timer
def create_doc_id_files():
    doc_id = dict()
    index = 0
    for article in get_articles_name(dn='data_url'):
        title = article[:-4]
        if title in doc_id:
            print("Одинаковое название статей! Название: %s. Id: %s" % (title, doc_id[title]))
        else:
            doc_id[title] = index
            index += 1
    return doc_id


@timer
def create_raw_index(doc_id):
    raw_index = defaultdict(list)
    dir_name = 'data_url_tokens'
    for token in get_articles_name(dn=dir_name):
        with open("../" + dir_name + "/" + token, 'r') as f:
            tokens_list = json.load(f)
            title = token[:-4]
            my_id = doc_id[title]
            for t in tokens_list:
                raw_index[t].append(my_id)
    return raw_index


DOC_ID = create_doc_id_files()
RAW_INDEX = create_raw_index(DOC_ID)
