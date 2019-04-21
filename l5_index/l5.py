import pickle
import struct
import json
from os import walk
from datetime import datetime
from collections import defaultdict
import hashlib

FORMAT_TO_LL = 'q'
FORMAT_TO_CHAR = 's'
SIZE_OF_LL = 8
SIZE_OF_CHAR = 1
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


@timer
def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def read_doc_id_and_length(file_descriptor):
    values = file_descriptor.read(2 * SIZE_OF_LL)
    return struct.unpack("2" + FORMAT_TO_LL, values)


def move_in_index(file_descriptor):
    doc_id, length = read_doc_id_and_length(file_descriptor)
    file_descriptor.seek(length * SIZE_OF_CHAR, 1)


def read_index_title_and_url(id, file_name):
    with open(file_name, 'rb') as f:
        for i in range(id):
            move_in_index(f)
        doc_id, length = read_doc_id_and_length(file_descriptor=f)
        if doc_id != id:
            print("Внимание! Искомый индекс не соответсвует считаному! %s != %s" % (doc_id, id))
        bin_title = f.read(length * SIZE_OF_CHAR)
        frm = str(length) + FORMAT_TO_CHAR
        title = struct.unpack(frm, bin_title)[0].decode('utf-8')
        return title, URL_PREFFIX + title


def get_articles(set_of_ids, file_name='doc_id'):
    for id in set_of_ids:
        print("Заголовок: %s. Url: %s" % read_index_title_and_url(id, file_name))


def write_n_digits_to_binary_doc_id(list_of_digits, file_name):
    with open(file_name, 'ab') as f:
        n = len(list_of_digits)
        frm = str(n) + FORMAT_TO_LL
        value_to_write = struct.pack(frm, *list_of_digits)
        f.write(value_to_write)


def read_form_binary_doc_id(offset, file_name, pos_in_file=0):
    with open(file_name, 'rb') as f:
        f.seek(pos_in_file * SIZE_OF_LL)
        values = f.read(offset*SIZE_OF_LL)
        frm = str(offset) + FORMAT_TO_LL
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
    expect_size = 0
    with open('doc_id', 'ab') as f:
        for title, id in doc_id.items():
            # frm = id + len(title) + len(title) sizeof(char)
            title = title.encode('utf-8')
            offset = len(title)
            expect_size += SIZE_OF_LL + SIZE_OF_LL + offset * SIZE_OF_CHAR
            frm = FORMAT_TO_LL + FORMAT_TO_LL + str(offset) + FORMAT_TO_CHAR
            f.write(struct.pack(frm, id, offset, title))
    print("expected_size: %s" % expect_size)
    return doc_id


def hash_str(s):
    return int(hashlib.sha1(s.encode('utf-8')).hexdigest(), 16) % (10 ** 8)


@timer
def create_raw_invert_index(doc_id):
    raw_invert_index = defaultdict(list)
    dir_name = 'data_url_tokens'
    for token in get_articles_name(dn=dir_name):
        with open("../" + dir_name + "/" + token, 'r') as f:
            tokens_list = json.load(f)
            title = token[:-4]
            my_id = doc_id[title]
            for t in tokens_list:
                word_hash = hash_str(t)
                raw_invert_index[word_hash].append(my_id)

    invert_index = dict(raw_invert_index)

    # offset в файле считаем как количество записаных чисел, а не байт, так как при считывании нужно передавать
    # количество чисел(функция read_form_binary_doc_id)
    offset_in_file = 0
    for key, value in raw_invert_index.items():
        k = len(value)
        offset_for_word = offset_in_file
        offset_in_file += k
        invert_index[key] = (offset_for_word, k)

        write_n_digits_to_binary_doc_id(value, 'cord_blocks')

    print("expected_size: %s" % (offset_in_file * SIZE_OF_LL))
    return invert_index


if __name__ == '__main__':
    DOC_ID = create_doc_id_files()
    INVERT_INDEX = create_raw_invert_index(DOC_ID)
    save_obj(INVERT_INDEX, name='INVERT_INDEX')
