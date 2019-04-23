import sys
import struct
import json
from collections import defaultdict
sys.path.append('..')

from l5_index.l5 import (FORMAT_TO_LL, SIZE_OF_LL, FORMAT_TO_CHAR, SIZE_OF_CHAR, create_doc_id_files, save_obj,
                         read_form_binary_doc_id,
                         write_n_digits_to_binary_doc_id, timer, get_articles_name, hash_str)


def create_cord_block(list_of_digits, file_name='offset_pos'):
    with open(file_name, 'ab') as f:
        n = len(list_of_digits)
        frm = str(n) + FORMAT_TO_LL
        value_to_write = struct.pack(frm, *list_of_digits)
        f.write(value_to_write)


@timer
def create_raw_invert_index(doc_id):
    raw_invert_index = defaultdict(lambda: defaultdict(list))
    dir_name = 'data_url_tokens'
    for token in get_articles_name(dn=dir_name):
        with open("../" + dir_name + "/" + token, 'r') as f:
            tokens_list = json.load(f)
            title = token[:-4]
            my_id = doc_id[title]

            for i in range(len(tokens_list)):
                word_hash = hash_str(tokens_list[i])
                raw_invert_index[word_hash][my_id].append(i)

    invert_index = dict()

    # offset в файле считаем как количество записаных чисел, а не байт, так как при считывании нужно передавать
    # количество чисел(функция read_form_binary_doc_id)
    offset_in_file = 0
    offset_in_bin_file = 0
    for key, value_dict in raw_invert_index.items():
        k = len(value_dict)
        offset_for_word = offset_in_file
        offset_in_file += k
        invert_index[key] = (offset_for_word, k)
        with open('bin_file', 'ab') as f:

            for key, value_list in value_dict.items():
                frm = FORMAT_TO_LL + FORMAT_TO_LL + FORMAT_TO_LL
                offset_l = offset_in_bin_file
                len_l = len(value_list)
                offset_in_bin_file += len_l
                value_to_bin_file = struct.pack(frm, key, offset_l, len_l)
                f.write(value_to_bin_file)
                write_n_digits_to_binary_doc_id(value_list, 'offset_blocks')

    # print("expected_size: %s" % (offset_in_file * SIZE_OF_LL))
    return invert_index


if __name__ == '__main__':
    DOC_ID = create_doc_id_files()
    INDEX = create_raw_invert_index(DOC_ID)
    save_obj(INDEX, name='INDEX')
    print(read_form_binary_doc_id(offset=10, file_name='offset_blocks', pos_in_file=0))
