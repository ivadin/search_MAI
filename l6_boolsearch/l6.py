import sys
import re
sys.path.append('..')

from l5_index.l5 import load_obj, hash_str, read_form_binary_doc_id, get_articles  # noqa

WORD = re.compile(r'\w+')


def parse_request(string):
    while "  " in string:
        string = string.replace("  ", " ")
    return string


def replace_word_to_set(string, target_word, str_set):
    if not isinstance(str_set, str):
        str_set = str(set(str_set))

    string = re.sub(r'\b \b', ' & ', string)
    string = re.sub(r'\b' + target_word + r'\b', str_set, string)
    return string


def get_words(input_string):
    words = WORD.findall(input_string)
    return {w for w in words if len(w)}


if __name__ == '__main__':
    INV_INDEX = load_obj('../l5_index/INVERT_INDEX')
    while True:
        request = input("Запрос: ").lower()
        # request = "заслуженный мастер спорта"
        if request == "exit()":
            break

        words = get_words(request)
        for word in words:
            hash_word = hash_str(word)
            pos_in_file, offset = INV_INDEX[hash_word]
            ids_for_word = set(read_form_binary_doc_id(
                offset=offset, file_name='../l5_index/cord_blocks', pos_in_file=pos_in_file))
            request = replace_word_to_set(request, word, str(ids_for_word))

        res_ids = eval(request)

        get_articles(set_of_ids=res_ids, file_name='../l5_index/doc_id')
        print("\n")

