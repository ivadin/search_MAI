import sys
import struct
import json
import re
import typing
import datetime
import hashlib
import vbcode
import math
from pymystem3 import Mystem
from collections import defaultdict

sys.path.append('..')

from l5_index.l5 import (FORMAT_TO_LL, SIZE_OF_LL, FORMAT_TO_CHAR, SIZE_OF_CHAR, URL_PREFFIX, timer, get_articles_name)
from l6_boolsearch.l6 import get_words
from l7_coordinate.l7 import get_words_for_quotes

from l8_compression.l8 import get_vb_code_for_doc_ids


WORD = re.compile(r'\b\w+\b')
QUOTE = re.compile(r'«.+»')
SPLITTER = re.compile(r'(«.*?»)')
STEP = re.compile(r'»(/\d+|$| )')
USED_DIST = 0
steps = []
NUMBER = re.compile("/(\d+)")

morph = Mystem()

FORMAT_TO_UI = 'I'
SIZE_OF_UI = 4

FORMAT_TO_FL = 'f'
SIZE_OF_FL = 4

DIR_WITH_ARTICLES = 'data_url'
DIR_WITH_TOKENS = 'data_url_tokens'

TOTAL_ARTICLE_COUNT: int = 0


class LogicDict(dict):
    """
    Словарь, который поддерживает логические операции, суммируя value.
    Нужен для построения метрики TFIDF для запросов
    """
    def __and__(self, other):
        answer = LogicDict()
        for key, value in other.items():
            if key in self:
                self_value = self[key]
                if isinstance(self_value, (list, tuple)):
                    if len(self_value) == 2:
                        self_value = self_value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                    else:
                        self_value = sum(self_value)  # если структура doc_id: [tfidf, tfidf, ...]
                if isinstance(value, (list, tuple)):
                    if len(value) == 2:
                        value = value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                    else:
                        value = sum(value)  # если структура doc_id: [tfidf, tfidf, ...]

                answer[key] = self_value + value

        return answer

    def __or__(self, other):
        answer = LogicDict()
        for key, value in self.items():
            if isinstance(value, list):
                if len(value) == 2:
                    value = value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                else:
                    value = sum(value)  # если структура doc_id: [tfidf, tfidf, ...]
            answer[key] = value
        for key, value in other.items():
            if key in answer:
                self_value = self[key]
                if isinstance(self_value, (list, tuple)):
                    if len(self_value) == 2:
                        self_value = self_value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                    else:
                        self_value = sum(self_value)  # если структура doc_id: [tfidf, tfidf, ...]
                if isinstance(value, (list, tuple)):
                    if len(value) == 2:
                        value = value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                    else:
                        value = sum(value)  # если структура doc_id: [tfidf, tfidf, ...]
                answer[key] = self_value + value
            else:
                if isinstance(value, list):
                    if len(value) == 2:
                        value = value[0]  # если структура doc_id: [tfidf, [pos1, pos2, pos3, ....]]
                    else:
                        value = sum(value)  # если структура doc_id: [tfidf, tfidf, ...]
                answer[key] = value
        return answer

    def __str__(self):
        return f"{self.__class__.__name__}({super().__str__()})"


def create_temp_dict(res_dict, current_dict, step=3):
    """
    Получить dict {doc_id: (tfidf, [pos_in_doc1, pos_in_doc2, pos_in_doc3, ...])}
    :param res_dict: словарь, полученный на предыдущих этапах обработки цитаты
    :param current_dict: словарь, полученный для текущего слова из цитаты
    :param step: определяет допустимые вкрапления в цитатный поиск
    :return: dict: {doc_id: [pos1, pos2, pos3, ...]}
    """
    current_answer_dict = LogicDict()
    for key, list_value in current_dict.items():
        # Ищем общий ключ в том, что уже есть и новос dict-е
        if key in res_dict:
            tfidf_res, list_from_res = res_dict[key]
            tfidf_from_current, list_from_current = current_dict[key]

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
                total_ifidf = tfidf_res + tfidf_from_current
                current_answer_dict[key] = (total_ifidf, answer_element_list)

    return current_answer_dict


def read_bin_struct_for_quotes(pos_in_file, offset_for_doc, offset_for_freq, file_name='bin_file'):
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
    answer = LogicDict()

    with open(file_name, 'rb') as f:
        f.seek(pos_in_file)
        vb_doc_ids = f.read(offset_for_doc)
        doc_ids = vbcode.decode(vb_doc_ids)

        bin_tfidf = f.read(len(doc_ids) * SIZE_OF_FL)
        frm = str(len(doc_ids)) + FORMAT_TO_FL
        tfidf = struct.unpack(frm, bin_tfidf)

        bin_freqs = f.read(len(doc_ids) * SIZE_OF_UI)
        frm = str(len(doc_ids)) + FORMAT_TO_UI
        freqs = struct.unpack(frm, bin_freqs)

        vb_list_of_positions = f.read(offset_for_freq)
        list_of_positions = vbcode.decode(vb_list_of_positions)

    first_slice = 0
    for i in range(len(doc_ids)):
        second_slice = first_slice + freqs[i]
        # берем i-ый doc_id, i-ый freq и берем срез с из массива с частотами
        answer[doc_ids[i]] = (tfidf[i], list_of_positions[first_slice:second_slice])
        first_slice += freqs[i]

    return answer


def read_bin_struct_for_bool(pos_in_file, offset_for_doc, file_name='bin_file'):
    """
    Считываем структуру из бинарного файла и возвращаем doc_ids
    vb(doc_id1, doc_id2, ...)(freq_in_doc_id1, freq_in_doc_id2, ...)
            ([pos1_in_doc1, pos2_in_doc1, ...][pos1_in_doc2, pos2_in_doc2, ...] ...)
    :param pos_in_file: смещение в байтах от начала
    :param offset_for_doc: длина в байтах закодированных doc_ids
    :param file_name:
    :return:
    """
    answer = LogicDict()
    with open(file_name, 'rb') as f:
        f.seek(pos_in_file)
        vb_doc_ids = f.read(offset_for_doc)
        doc_ids = vbcode.decode(vb_doc_ids)

        bin_tfidf = f.read(len(doc_ids) * SIZE_OF_FL)
        frm = str(len(doc_ids)) + FORMAT_TO_FL
        tfidf = struct.unpack(frm, bin_tfidf)

    for i in range(len(doc_ids)):
        # берем i-ый doc_id, i-ый freq и берем срез с из массива с частотами
        answer[doc_ids[i]] = tfidf[i]

    return answer


@timer
def get_search_res_for_quotes(request, step):
    """
    Координатный поиск
    :param request:
    :param step:
    :return:
    """
    words = get_words_for_quotes(request)
    res_dict = LogicDict()
    is_first = True
    for word in words:
        hash_word = hash_str(word)
        pos_in_file, offset_for_doc, offset_for_freq = INDEX[hash_word]

        dict_for_cur_word = read_bin_struct_for_quotes(pos_in_file, offset_for_doc, offset_for_freq)

        if is_first:
            res_dict = dict_for_cur_word
            is_first = False
        else:
            res_dict = create_temp_dict(res_dict, dict_for_cur_word, step)

    """
    res_dict имеет слудующую структуру:
    {
        doc_id: (tfidf, [pos_in_file, ...]),
        ...
    }
    """
    return str(res_dict)


def hash_str(s):
    """
    На данном этапе сделаем леммизацию
    :param s:
    :return:
    """
    lemm = morph.lemmatize(s)[0]
    return int(hashlib.sha1(lemm.encode('utf-8')).hexdigest(), 16) % (10 ** 8)


def parse_request(string):
    parsed_str = re.sub(r" +", " ", string)
    parsed_str = re.sub(r'\b \b', ' & ', parsed_str)
    parsed_str = re.sub(r'!', ' - ', parsed_str)
    return parsed_str.lower()


def replace_word_to_set(string, target_word, str_set):
    if not isinstance(str_set, str):
        str_set = str(set(str_set))

    string = re.sub(r'\b' + target_word + r'\b', str_set, string)
    return string


def get_quotes(input_string):
    return QUOTE.findall(input_string.lower())


def read_direct_index(offset, file_name='doc_id'):
    """
    В файле doc_id храниться структура : [size_of_title, title], нужно получать title для нужного offset
    :param offset: на сколько нужно сместиться в файле
    :param file_name:
    :return:
    """
    with open(file_name, 'rb') as f:
        f.seek(offset)
        binary_len_of_title = f.read(SIZE_OF_UI)
        len_of_title = struct.unpack(FORMAT_TO_UI, binary_len_of_title)[0]

        binary_title = f.read(len_of_title * SIZE_OF_CHAR)

        frm_for_title = str(len_of_title) + FORMAT_TO_CHAR
        title = struct.unpack(frm_for_title, binary_title)[0].decode('utf-8')
        return title


@timer
def dump_invert_index(invert_index, file_name='INDEX'):
    with open(file_name, 'ab') as f:
        total_size = len(invert_index)
        bs = struct.pack(FORMAT_TO_LL, total_size)
        f.write(bs)
        for word, values in invert_index.items():
            # хеш(лемма(слово)) + смещение для слова +
            # длина закодированной последовательности doc_id + длина закодированной последовательности pos_in_file
            frm = FORMAT_TO_UI + FORMAT_TO_UI + FORMAT_TO_UI + FORMAT_TO_UI

            binary_struct = struct.pack(frm, word, *values)

            f.write(binary_struct)


@timer
def dump_direct_index(doc_ids, file_name='DIRECT_INDEX'):
    """
    Хотим записать полученную структура
        { title: [doc_id, offset] }
    в файл для считывания в формате
        { doc_id: offset}
    Который потом будет грузиться в прямой индекс и использоваться для поисковой выдачи
    :param doc_ids:
    :param file_name:
    :return:
    """
    direct_index = {}
    with open(file_name, 'ab') as f:
        total_size = len(doc_ids)
        bs = struct.pack(FORMAT_TO_LL, total_size)
        f.write(bs)
        for title, value in doc_ids.items():
            doc_id = value[0]
            offset_for_title = value[1]
            direct_index[doc_id] = offset_for_title
            frm = FORMAT_TO_UI + FORMAT_TO_UI

            binary_struct = struct.pack(frm, doc_id, offset_for_title)

            f.write(binary_struct)

    del doc_ids
    return direct_index


@timer
def create_direct_index(file_name='doc_id'):
    doc_ids = dict()
    index = 0
    for article in get_articles_name(dn=DIR_WITH_ARTICLES):
        title = article[:-4]
        if title in doc_ids:
            print(f"Одинаковое название статей! Название: {title}. Id: {doc_ids[title][0]}")
        else:
            doc_ids[title] = [index, 0]  # второе число - позиция для оффсета
            index += 1

    """
    Получили структуру 
    {
        title: [doc_id, offset_in_bin_file], value - всегда list из двух значений, на данном этапе value[1] = 0
        ...
    }
    """

    offset_in_file = 0
    with open(file_name, 'ab') as f:
        for title, d_id in doc_ids.items():
            doc_ids[title][1] = offset_in_file

            title = title.encode('utf-8')
            offset = len(title)

            frm = FORMAT_TO_UI + str(offset) + FORMAT_TO_CHAR

            binary_struct = struct.pack(frm, offset, title)

            f.write(binary_struct)

            offset_in_file += len(binary_struct)

    """
    Пытались получить следущее - записать в файл file_name последовательность: 
    [длинну заголовка, заголовок]. в словарь doc_ids добавляем значение смещения
    """

    direct_index = dump_direct_index(doc_ids)

    return direct_index


@timer
def create_raw_invert_index(direct_index):
    raw_invert_index = defaultdict(lambda: defaultdict(lambda: [int, []]))
    """
    raw_invert_index:
    {
        word: 
        {
            doc_id: (кол-во токенов в докумене, [позиции, на которых слово встретиловсь])
            # частотсу слова в документе, для расчета idf можно получить как len([позиции])
        }
    }
    """
    dir_name = DIR_WITH_TOKENS

    step = 0
    t = datetime.datetime.now()

    for doc_id, offset_for_title in direct_index.items():
        token = read_direct_index(offset_for_title)
        with open(f"../{dir_name}/{token}.txt", 'r') as f:
            tokens_list = json.load(f)

            for i in range(len(tokens_list)):
                word_hash = hash_str(tokens_list[i])
                raw_invert_index[word_hash][doc_id][0] = len(tokens_list)
                raw_invert_index[word_hash][doc_id][1].append(i)

            sys.stdout.write(f"\rОбработано в сырой обратный индекс: {step} / {len(direct_index)}")
            sys.stdout.flush()
            step += 1

    print(f"\nСырой обратный индекс создан. {datetime.datetime.now() - t}.\nНачинаем обработку индекса")

    # Этот каст делается для того, что бы raw_invert_index стал обычным словарем
    raw_invert_index = dict(raw_invert_index)
    len_raw_invert_index = len(raw_invert_index)
    step = 0
    t = datetime.datetime.now()

    offset_in_bin_file = 0

    total_files_in_corp = len(direct_index)

    for key_dict, value_dict in raw_invert_index.items():

        IDF = math.log10(total_files_in_corp / len(value_dict))

        offset_for_word = offset_in_bin_file

        # Преобразование doc_id
        sorted_doc_ids, vbcode_doc_ids = get_vb_code_for_doc_ids(value_dict.keys())
        # длина кода vb
        len_of_vbcode_doc_ids = len(vbcode_doc_ids)

        # Преобразование [pos_in_file, ...], подсчет частот(freq), а так же подсчет метрики TFIDF
        freqs = []
        tfidf = []
        for_write_pos_in_file = b''
        for elem in sorted_doc_ids:
            total_tokens_in_file, pos_in_file = value_dict[elem]

            current_freq = len(pos_in_file)
            freqs.append(current_freq)

            TF = current_freq / total_tokens_in_file
            TFIDF = TF * IDF
            tfidf.append(TFIDF)

            for_write_pos_in_file += vbcode.encode(sorted(pos_in_file))
        # длина позиций в документе в vb
        len_of_vbcode_for_pos_in_files = len(for_write_pos_in_file)

        # Форматируем частоты в файле
        frm = str(len(freqs)) + FORMAT_TO_UI
        write_freq = struct.pack(frm, *freqs)

        # Формируем TFIDF в файле
        frm = str(len(tfidf)) + FORMAT_TO_FL
        write_tfidf = struct.pack(frm, *tfidf)

        res = vbcode_doc_ids + write_tfidf + write_freq + for_write_pos_in_file
        total_len = len(res)
        with open('bin_file', 'ab') as f:
            f.write(res)

        raw_invert_index[key_dict] = (offset_for_word, len_of_vbcode_doc_ids, len_of_vbcode_for_pos_in_files)
        offset_in_bin_file += total_len

        sys.stdout.write(f"\rСоздание обратного индекс: {step} / {len_raw_invert_index}")
        sys.stdout.flush()
        step += 1

    print(f"\nОбратный индекс создан. {datetime.datetime.now() - t}")
    return raw_invert_index


def make_articles_rang(res_dict):
    """
    получаем результат, теперь его нужно отсортировать по сумме значений, а не по ключу!
    :param res_dict: {}
    :return:
    """
    return sorted(
        res_dict.items(), key=lambda kv: kv[1][0] if isinstance(kv[1], (list, tuple)) else kv[1], reverse=True)


@timer
def get_search_res(request: str):
    i = 0
    request = preprocessing_request(request)
    print(request)
    for words_or_quote in filter(None, SPLITTER.split(request)):
        m = QUOTE.match(words_or_quote)
        if m:
            if NUMBER.match(steps[i]):
                step = int(NUMBER.search(steps[i]).group(1))
            else:
                step = len(WORD.findall(words_or_quote))
            search_res = get_search_res_for_quotes(words_or_quote, step)
            request = request.replace(words_or_quote, search_res)
            i += 1
        else:
            request = request.replace(words_or_quote, get_search_res_for_words(words_or_quote))

    res_ids = eval(request)
    sorted_by_metric = make_articles_rang(res_ids)

    get_articles(set_of_ids=sorted_by_metric)


def get_search_res_for_words(request: str) -> str:
    """
    Булев поиск
    :param request:
    :return:
    """

    words = get_words(request)
    for word in words:
        hash_word = hash_str(word)
        pos_in_file, offset_for_doc, offset_for_freq = INDEX[hash_word]

        dict_for_cur_word = read_bin_struct_for_bool(pos_in_file=pos_in_file, offset_for_doc=offset_for_doc)

        request = replace_word_to_set(request, word, str(dict_for_cur_word))

    return request


def delete_steps_from_request(request: str):
    return STEP.sub("»", request)


def write_data():
    """
    Использовать перед первым запуском
    :return:
    """
    global TOTAL_ARTICLE_COUNT

    DIRECT_INDEX: typing.Dict = create_direct_index()
    TOTAL_ARTICLE_COUNT = len(DIRECT_INDEX)
    INDEX = create_raw_invert_index(DIRECT_INDEX)
    dump_invert_index(INDEX)


def preprocessing_request(raw_request):
    global steps

    request = parse_request(raw_request)
    steps = STEP.findall(request)
    request = delete_steps_from_request(request)

    return request


@timer
def load_direct_index(file_name='DIRECT_INDEX'):
    direct_index = {}
    with open(file_name, 'rb') as f:
        total_binary = f.read(SIZE_OF_LL)

        total = struct.unpack(FORMAT_TO_LL, total_binary)[0]
        # print(f"Total {total}")
        for i in range(total):
            dict_items_binary = f.read(SIZE_OF_UI + SIZE_OF_UI)

            frm = FORMAT_TO_UI + FORMAT_TO_UI
            key, value = struct.unpack(frm, dict_items_binary)

            direct_index[key] = value

    return direct_index


@timer
def load_invert_index(file_name='INDEX'):
    invert_index = {}
    with open(file_name, 'rb') as f:
        total_binary = f.read(SIZE_OF_LL)

        total = struct.unpack(FORMAT_TO_LL, total_binary)[0]

        for i in range(total):
            dict_items_binary = f.read(SIZE_OF_UI + SIZE_OF_UI + SIZE_OF_UI + SIZE_OF_UI)

            frm = FORMAT_TO_UI + FORMAT_TO_UI + FORMAT_TO_UI + FORMAT_TO_UI

            word, offset_for_word, len_of_vbcode_doc_ids, len_of_vbcode_for_pos_in_files = struct.unpack(
                frm, dict_items_binary
            )

            invert_index[word] = (offset_for_word, len_of_vbcode_doc_ids, len_of_vbcode_for_pos_in_files)

    return invert_index


def get_snippet(filename):
    with open(f'../data_url/{filename}.txt', 'r') as f:
        f.seek(0)
        return f.readline()


def get_articles(set_of_ids):
    for item in set_of_ids:
        doc_id = item[0]
        offset = DIRECT_INDEX[doc_id]
        title = read_direct_index(offset)
        TFIDF = item[1][0] if isinstance(item[1], (list, tuple)) else item[1]
        print(f"Id: {doc_id}. Заголовок: {title}. Url: {URL_PREFFIX}{title}. TFIDF: {TFIDF}")
        snippet = get_snippet(title)
        print(snippet)
    print('Articles count: %s' % len(set_of_ids))


if __name__ == '__main__':
    """
    INDEX.plk - инвертированный индекс
    doc_id - файл с id документа и title
    offset_block - позиции слова в документе
    bin_file - doc_id, offset_in_offset_block_file, elements_in_offset_block
    """
    # write_data()

    DIRECT_INDEX = load_direct_index()
    INDEX = load_invert_index()

    # request = '«мастер»/1'
    # request = 'мастер спорта'
    # request = 'мастер спорта по самбо'
    # get_search_res_for_quotes(request)
    # request = '«мастер спорта по самбо»/1'
    # INDEX = load_obj('INDEX')
    # request = 'мастер по самбо'
    # request = "мастер спорта федерации"
    # get_search_res_for_quote(request=request, step=3)
    #
    # while True:
    #     # request = "«другой мир»/10 | (двигатель & сгорания) | «гоночные автомобили»/5"
    #
    request = "((мастер) & «по самбо»/1)"
    # request = "«мастер спорта федерации»/3 | «по самбо»/6"
        # request = "«мастер по самбо»/3"
    #
    get_search_res(request)
    #     break
