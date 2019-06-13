import sys
import struct
import json
import re
import datetime
from collections import defaultdict
sys.path.append('..')

from l5_index.l5 import (FORMAT_TO_LL, SIZE_OF_LL, FORMAT_TO_CHAR, SIZE_OF_CHAR, create_doc_id_files,
                         save_obj, load_obj, get_articles,
                         read_form_binary_doc_id,
                         write_n_digits_to_binary_doc_id, timer, get_articles_name, hash_str)
from l6_boolsearch.l6 import get_words

WORD = re.compile(r'\b\w+\b')


def get_words_for_quotes(input_string):
    return WORD.findall(input_string)


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
    for key_dict, value_dict in raw_invert_index.items():
        k = len(value_dict)
        offset_for_word = offset_in_file
        offset_in_file += k
        invert_index[key_dict] = (offset_for_word, k)
        with open('bin_file', 'ab') as f:

            for key_list, value_list in value_dict.items():
                frm = FORMAT_TO_LL + FORMAT_TO_LL + FORMAT_TO_LL
                offset_l = offset_in_bin_file
                len_l = len(value_list)
                offset_in_bin_file += len_l
                value_to_bin_file = struct.pack(frm, key_list, offset_l, len_l)
                f.write(value_to_bin_file)
                write_n_digits_to_binary_doc_id(value_list, 'offset_blocks')

    # print("expected_size: %s" % (offset_in_file * SIZE_OF_LL))
    return invert_index


def read_elements_from_bin_file(offset, file_name, pos_in_file):
    with open(file_name, 'rb') as f:
        f.seek(pos_in_file * SIZE_OF_LL)
        values = f.read(offset*SIZE_OF_LL)
        frm = str(3) + FORMAT_TO_LL
        return struct.unpack(frm, values)


def create_temp_dict(res_dict, current_dict, step=2):
    """
    Получить dict {doc_id: [pos_in_doc1, pos_in_doc2, pos_in_doc3, ...]}
    :param res_dict: словарь, полученный на предыдущих этапах обработки цитаты
    :param current_dict: словарь, полученный для текущего слова из цитаты
    :param step: определяет допустимые вкрапления в цитатный поиск
    :return: dict: {doc_id: [pos1, pos2, pos3, ...]}
    """
    current_answer_dict = dict()
    for key, list_value in current_dict.items():
        # Ищем общий ключ в том, что уже есть и новос dict-е
        if key in res_dict:
            list_from_res = res_dict[key]
            list_from_current = current_dict[key]
            answer_element_list = list()
            # Важно! Идем по позицияс в res_dict, так как он уже посчитан, и отталкиваемся от этих элеметов
            for pos in list_from_res:
                # Берем весь диапазон в step и запоминаем позиции совпадений
                for i in range(step):
                    if pos + i + 1 in list_from_current:
                        answer_element_list.append(pos + i + 1)
            # Если мы нашли
            if answer_element_list:
                current_answer_dict[key] = answer_element_list

    return current_answer_dict


@timer
def get_search_res_for_quotes(request):
    words = get_words_for_quotes(request)
    res_dict = dict()
    is_first = True
    t = datetime.datetime.now()
    for word in words:
        hash_word = hash_str(word)
        try:
            pos_in_file, offset = INDEX[hash_word]
        except:
            print(f"Нет слова. Запрос: {request}")
            return
        # аргументы умножаются на 3, так как в булевом поиске мы записывали по одному числу,
        # а теперь мы хотим считать offset елементов, какждый из которых состоит из 3-x чисел формата long long
        res_of_read = read_form_binary_doc_id(
            offset=3*offset, file_name='bin_file', pos_in_file=3*pos_in_file)
        dict_for_cur_word = dict()

        element = []
        for i in range(len(res_of_read)):
            if i and not i % 3:
                doc_id, offset_in_offset_block, elements_in_offset_block = element
                dict_for_cur_word[doc_id] = list(read_form_binary_doc_id(
                    offset=elements_in_offset_block, file_name='offset_blocks', pos_in_file=offset_in_offset_block))
                element = []
            element.append(res_of_read[i])

        if is_first:
            res_dict = dict_for_cur_word
            is_first = False
        else:
            res_dict = create_temp_dict(res_dict, dict_for_cur_word)
    print(f"Поиск выполнен за {datetime.datetime.now() - t}")
    get_articles(set(list(set(res_dict))[:5]))


if __name__ == '__main__':
    """
    INDEX.plk - инвертированный индекс
    doc_id - файл с id документа и title
    offset_block - позиции слова в документе
    bin_file - doc_id, offset_in_offset_block_file, elements_in_offset_block
    """
    # DOC_ID = create_doc_id_files()
    # INDEX = create_raw_invert_index(DOC_ID)
    # save_obj(INDEX, name='INDEX')

    INDEX = load_obj('INDEX')
    # while True:
    #     # request = input("Запрос: ")
    # request = 'мастер'
    # request = 'мастер спорта'
    # request = 'мастер по самбо'
    # request = "боевые искусства"
    # request = 'лёгкой спорта тренер'
    #     if request == "exit()":
    #         break

    # get_search_res_for_quotes(request=request)
    # print("\n")
    q = [
        "спорт экспресс",
        "виды спорта",
        "активный отдых",
        "хоккеная площадка",
        "трансфер кхл",
        "фигурное катание",
        "профессиональный бокс",
        "боевые искусства",
        "кхл",
        "спортивный клуб",
        "нхл",
        "физическая культура и спорт",
        "лучшие футболисты мира",
        "зимний спорт",
        "зимняя олимпиада",
        "кровавый спорт",
        "газета спорт",
        "министерство спорта",
        "зимние виды спорта",
        "федерация спорта",
        "мастер спорта",
        "олимпийский спорт",
        "команды кхл",
        "конькобежный спорт",
        "чемпионат мира по самбо",
        "лыжный спорт",
        "гиревой спорт",
        "водные виды спорта",
        "самбо",
        "летняя универсиада"
    ]

    # while True:
    #     request = input("Запрос: ")
    # request = "заслуженный мастер спорта"
    # request = "боевые искусства"
    # request = "оно | в | на | он | я"
    #     # if request == "exit()":
    #     #     break
    #
    for qs in q:
        request = qs
        print(f"Запрос: {request}")

        get_search_res_for_quotes(request=request)
        print("\n")
