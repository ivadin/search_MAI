import sys
import re
import datetime
sys.path.append('..')

from l5_index.l5 import load_obj, hash_str, read_form_binary_doc_id, get_articles, timer  # noqa

WORD = re.compile(r'\b\w+\b')


def parse_request(string):
    while "  " in string:
        string = string.replace("  ", " ")
    string = re.sub(r'\b \b', ' & ', string)
    string = re.sub(r'!', ' - ', string)
    return string


def replace_word_to_set(string, target_word, str_set):
    if not isinstance(str_set, str):
        str_set = str(set(str_set))

    string = re.sub(r'\b' + target_word + r'\b', str_set, string)
    return string


def get_words(input_string):
    words = WORD.findall(input_string)
    return {w for w in words if len(w)}


@timer
def get_search_res(request):
    request = parse_request(request.lower())
    t = datetime.datetime.now()
    words = get_words(request)
    for word in words:
        hash_word = hash_str(word)
        try:
            pos_in_file, offset = INV_INDEX[hash_word]
        except:
            print(f"Нет слова. Запрос: {request}")
            return
        ids_for_word = set(read_form_binary_doc_id(
            offset=offset, file_name='../l5_index/cord_blocks', pos_in_file=pos_in_file))
        request = replace_word_to_set(request, word, str(ids_for_word))

    res_ids = eval(request)
    print(f"Результат получен за {datetime.datetime.now() - t}")

    get_articles(set_of_ids=list(res_ids)[:5], file_name='../l5_index/doc_id')


if __name__ == '__main__':
    INV_INDEX = load_obj('../l5_index/INVERT_INDEX')

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

        get_search_res(request=request)
        print("\n")

