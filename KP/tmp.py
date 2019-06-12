import typing
import datetime
import math
import struct
import json
from collections import defaultdict

import sys
sys.path.append('..')


from l5_index.l5 import (load_obj, timer, get_articles_name, hash_str, create_doc_id_files, save_obj,
                         read_index_title_and_url)
from l7_coordinate.l7 import get_words_for_quotes

FORMAT_TO_UI = 'I'
SIZE_OF_UI = 4

FORMAT_TO_FL = 'f'
SIZE_OF_FL = 4

FORMAT_TO_LL = 'q'
FORMAT_TO_CHAR = 's'
SIZE_OF_LL = 8
SIZE_OF_CHAR = 1

TOTAL_ARTICLE_COUNT: int = 0


def write_n_digits_to_binary_doc_id(list_of_digits, file_name):
    with open(file_name, 'ab') as f:
        n = len(list_of_digits)
        frm = str(n) + FORMAT_TO_UI
        value_to_write = struct.pack(frm, *list_of_digits)
        f.write(value_to_write)


@timer
def create_doc_id_files(file_name='doc_id'):
    doc_id = dict()
    index = 0
    for article in get_articles_name(dn='../data_raw'):
        title = article[:-4]
        if title in doc_id:
            print("Одинаковое название статей! Название: %s. Id: %s" % (title, doc_id[title]))
        else:
            doc_id[title] = index
            index += 1
    expect_size = 0
    with open(file_name, 'ab') as f:
        for title, id in doc_id.items():
            title = title.encode('utf-8')
            offset = len(title)
            expect_size += SIZE_OF_LL + SIZE_OF_LL + offset * SIZE_OF_CHAR
            frm = FORMAT_TO_LL + FORMAT_TO_LL + str(offset) + FORMAT_TO_CHAR
            f.write(struct.pack(frm, id, offset, title))
    # print("expected_size: %s" % expect_size)
    return doc_id

@timer
def create_raw_invert_index(doc_id):
    # raw_invert_index = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    raw_invert_index = {}
    dir_name = '../data_raw_tokens'
    step = 0
    tokens = get_articles_name(dn=dir_name)

    t = datetime.datetime.now()

    for token in tokens:
        with open("../" + dir_name + "/" + token, 'r') as f:
            tokens_list = json.load(f)
            title = token[:-4]
            my_id = doc_id[title]

            for i in range(len(tokens_list)):
                word_hash = hash_str(tokens_list[i])
                if word_hash not in raw_invert_index:
                    raw_invert_index[word_hash] = []
                raw_invert_index[word_hash].append(my_id)

            sys.stdout.write(f"\rОбработано в грязный обратный индекс: {step} / {len(tokens)}")
            sys.stdout.flush()
            step += 1

    print(f"\nГрязный обратный индекс создан. {datetime.datetime.now() - t}")

    """
    На этом этапе получен словарь вида
    {
        hash(word): [doc_id, doc_id, ...]
    }
    """
    del doc_id

    offset_in_file = 0

    step = 0

    generator = raw_invert_index.items()
    t = datetime.datetime.now()

    for word, value_list in generator:
        k = len(value_list)
        offset_for_word = offset_in_file
        offset_in_file += k

        raw_invert_index[word] = (offset_for_word, k)

        write_n_digits_to_binary_doc_id(value_list, 'doc_id')
        sys.stdout.write(f"\rСоздание обратного индекса: {step} / {len(raw_invert_index)}")
        sys.stdout.flush()
        step += 1

    print(f"\nОбратный индекс создан. {datetime.datetime.now() - t}")

    return raw_invert_index


def read_form_binary_doc_id(offset, file_name, pos_in_file=0):
    """
    Считывает offset чисел с pos_in_file
    :param offset:
    :param file_name:
    :param pos_in_file:
    :return:
    """
    with open(file_name, 'rb') as f:
        size_if_pair = SIZE_OF_UI + SIZE_OF_FL
        f.seek(pos_in_file * size_if_pair)
        values = f.read(offset * size_if_pair)
        frm = offset * f"{FORMAT_TO_UI}{FORMAT_TO_FL}"
        return struct.unpack(frm, values)


def write_data():
    """
    Использовать перед первым запуском
    :return:
    """
    global TOTAL_ARTICLE_COUNT

    DOC_ID: typing.Dict = create_doc_id_files()
    TOTAL_ARTICLE_COUNT = len(DOC_ID)
    INDEX = create_raw_invert_index(DOC_ID)
    save_obj(INDEX, name='INDEX')


def create_temp_dict(res_dict, current_dict):
    """
    теперь хотим получить следующее: берем уже рассчитаный res_dict и current_dict для нового слова.
    результатом будет новый словарь элементом которго является пересечение ключей res_dict и current_dict,
    а значения - список соответвующих значений tf*idf.
    :param res_dict: словарь, полученный на предыдущих этапах обработки цитаты
    :param current_dict: словарь, полученный для текущего слова из цитаты
    :return: dict: {common_doc_id: [*tf*idf_res_dict, *tf*idf_current_dict]}
    """
    current_answer_dict = dict()
    for key, list_value in current_dict.items():
        if key in res_dict:
            answer = res_dict[key] + current_dict[key]
            current_answer_dict[key] = answer

    return current_answer_dict


def make_articles_rang(res_dict):
    """
    получаем результат, теперь его нужно отсортировать по сумме значений, а не по ключу!
    :param res_dict: {}
    :return:
    """
    return sorted(res_dict.items(), key=lambda kv: sum(kv[1]), reverse=True)


def get_articles_with_metric(sorted_by_metric, file_name='doc_id'):
    """
    :param sorted_by_metric: отсортированный список с doc_id
    :param file_name:
    :param res_dict: для посмотра значения метрики
    :return:
    """
    for doc_id, tfidf in sorted_by_metric:
        title, url = read_index_title_and_url(doc_id, file_name)
        print(f"Id: {doc_id}. Заголовок: {title}. Url: {url}. TfIdf: {tfidf[0]}")
    print(f'Articles count: {len(sorted_by_metric)}')


@timer
def get_search_res_for_quotes(request):
    words = get_words_for_quotes(request)
    res_dict = dict()
    is_first = True
    for word in words:
        hash_word = hash_str(word)
        pos_in_file, offset, idf = INDEX[hash_word]

        res_of_read = read_form_binary_doc_id(
            offset=offset, file_name='docid_tf', pos_in_file=pos_in_file)

        dict_for_cur_word = dict()

        """
        мы считали [doc_id, tf_for_doc_id, doc_id1, tf_for_doc_id1,...] теперь, считываем элементы так, что бы получить 
        словари вида {doc_id: tf_for_doc_id, ...}
        """

        for i in range(len(res_of_read)):
            """
            берем каждую нечетную позицию - на них стоит tf_for_doc_id, на i - 1 соответсвующий doc_id
            """
            if i % 2:
                doc_id = res_of_read[i - 1]
                tf_for_doc_id = res_of_read[i]
                dict_for_cur_word[doc_id] = [tf_for_doc_id * idf]

        if is_first:
            res_dict = dict_for_cur_word
            is_first = False
        else:
            res_dict = create_temp_dict(res_dict, dict_for_cur_word)

    """
    после всех манипуляций получили результат, в следуюзем виде
    {
        doc_id: [itidf_for_word1, tfidf_for_word2, ...],
        ...
    }
    """

    sorted_by_metric = make_articles_rang(res_dict)

    get_articles_with_metric(sorted_by_metric)


if __name__ == '__main__':
    write_data()

    # INDEX = load_obj('INDEX')
    #
    # request = 'мастер'
    # request = 'мастер спорта'
    # request = 'мастер по самбо'
    # request = 'лёгкой спорта тренер'
    # get_search_res_for_quotes(request=request)
