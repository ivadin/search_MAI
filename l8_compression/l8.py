import sys
import struct
import json
import datetime
from collections import defaultdict
import vbcode  # noqa

sys.path.append('..')

from l5_index.l5 import (load_obj, get_articles, timer, get_articles_name, hash_str, create_doc_id_files, save_obj)
from l7_coordinate.l7 import get_words_for_quotes


FORMAT_TO_UI = 'I'
SIZE_OF_UI = 4


def get_vb_code_for_doc_ids(doc_ids):
    """
    :param doc_ids:
    :return: (отсортированные doc_ids, vbcode)
    """
    sorted_doc_ids = sorted(doc_ids)
    vb_code = vbcode.encode(sorted_doc_ids)
    return sorted_doc_ids, vb_code


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
    offset_in_bin_file = 0
    for key_dict, value_dict in raw_invert_index.items():
        offset_for_word = offset_in_bin_file

        sorted_doc_ids, vbcode_doc_ids = get_vb_code_for_doc_ids(value_dict.keys())
        # длина кода vb
        len_of_vbcode_doc_ids = len(vbcode_doc_ids)

        freqs = list()
        for_write_pos_in_file = b''
        for elem in sorted_doc_ids:
            pos_in_file = value_dict[elem]
            freqs.append(len(pos_in_file))
            for_write_pos_in_file += vbcode.encode(sorted(pos_in_file))
        # длина позиций в документе в vb
        len_of_vbcode_for_pos_in_files = len(for_write_pos_in_file)

        # форматируем частоты в файле
        frm = str(len(freqs)) + FORMAT_TO_UI
        write_freq = struct.pack(frm, *freqs)

        res = vbcode_doc_ids + write_freq + for_write_pos_in_file
        total_len = len(res)
        with open('bin_file', 'ab') as f:
            f.write(res)
        # if hash_str('мастер') == key_dict:
        #     import pdb
        #     pdb.set_trace()
        invert_index[key_dict] = (offset_for_word, len_of_vbcode_doc_ids, len_of_vbcode_for_pos_in_files)
        offset_in_bin_file += total_len

    # print("expected_size: %s" % (offset_in_file * SIZE_OF_LL))
    return invert_index


def create_temp_dict(res_dict, current_dict, step=1):
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
            # import pdb
            # pdb.set_trace()
            answer_element_list = list()
            # Важно! Идем по позицияс в res_dict, так как он уже посчитан, и отталкиваемся от этих элеметов
            for pos in list_from_res:
                # Берем весь диапазон в step и запоминаем позиции совпадений
                next_pos = pos + 1
                for i in range(step):
                    if next_pos + i in list_from_current:
                        answer_element_list.append(pos + i + 1)
            # Если мы нашли
            if answer_element_list:
                current_answer_dict[key] = answer_element_list

    return current_answer_dict


def read_bin_struct(pos_in_file, offset_for_doc, offset_for_freq, file_name='bin_file'):
    """
    Считываем структуру из бинарного файла
    vb(doc_id1, doc_id2, ...)(freq_in_doc_id1, freq_in_doc_id2, ...)
            ([pos1_in_doc1, pos2_in_doc1, ...][pos1_in_doc2, pos2_in_doc2, ...] ...)
    :param pos_in_file: смещение в байтах от начала
    :param offset_for_doc: длина в байтах закодированных doc_ids
    :param offset_for_freq: длинна в байтах закодированных позиций для каждого документа
    :param file_name:
    :return:
    """
    answer = dict()

    with open(file_name, 'rb') as f:
        f.seek(pos_in_file)
        vb_doc_ids = f.read(offset_for_doc)
        doc_ids = vbcode.decode(vb_doc_ids)

        bin_freqs = f.read(len(doc_ids) * SIZE_OF_UI)
        frm = str(len(doc_ids)) + FORMAT_TO_UI

        freqs = struct.unpack(frm, bin_freqs)
        vb_list_of_positions = f.read(offset_for_freq)
        list_of_positions = vbcode.decode(vb_list_of_positions)

    first_slice = 0
    for i in range(len(doc_ids)):
        second_slice = first_slice + freqs[i]
        # берем i-ый doc_id, i-ый freq и берем срез с из массива с частотами
        answer[doc_ids[i]] = list_of_positions[first_slice:second_slice]
        first_slice += freqs[i]

    return answer


@timer
def get_search_res_for_quotes(request):
    words = get_words_for_quotes(request)
    res_dict = dict()
    is_first = True
    t = datetime.datetime.now()
    for word in words:
        hash_word = hash_str(word)
        try:
            pos_in_file, offset_for_doc, offset_for_freq = INDEX[hash_word]
        except:
            print(f"Нет слова. Запрос: {request}")
            return
        dict_for_cur_word = read_bin_struct(pos_in_file, offset_for_doc, offset_for_freq)

        if is_first:
            res_dict = dict_for_cur_word
            is_first = False
        else:
            res_dict = create_temp_dict(res_dict, dict_for_cur_word)

    print(f"Поиск выполнен за {datetime.datetime.now() - t}")
    get_articles(set(list(set(res_dict))[:5]))


def write_data():
    """
    Добавить при первом запуске, что бы создались данные
    :return:
    """
    DOC_ID = create_doc_id_files()
    INDEX = create_raw_invert_index(DOC_ID)
    save_obj(INDEX, name='INDEX')


if __name__ == '__main__':
    """
    INDEX.plk - инвертированный индекс
    doc_id - файл с id документа и title
    bin_file - в файле структура: 
    vb(doc_id1, doc_id2, ...)(freq_in_doc_id1, freq_in_doc_id2, ...)
            ([pos1_in_doc1, pos2_in_doc1, ...][pos1_in_doc2, pos2_in_doc2, ...] ...)
    """
    INDEX = load_obj('INDEX')
    # request = 'мастер'
    # request = 'мастер спорта'
    # request = 'мастер по самбо'
    # request = 'лёгкой спорта тренер'
    # get_search_res_for_quotes(request=request)
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

    for qs in q:
        request = qs
        print(f"Запрос: {request}")

        get_search_res_for_quotes(request=request)
        print("\n")