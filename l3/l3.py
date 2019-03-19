import json
import re

import wikipedia
from googlesearch import search
from urllib.parse import unquote


queries = "q.json"
wikipedia_mark_data = "wikipedia_mark_data.json"
google_mark_data = "google_mark_data.json"

wikipedia_mark_data_list = []
google_mark_data = []

regex = re.compile(r'[^https://ru.wikipedia.org/wiki/]+')

query_list = []

with open(queries, 'r') as my_file:
    raw_query = my_file.read()
    query_list = json.loads(raw_query)


def get_marked_data(query_list, search):
    """
    Создает list_of_ditc для запросов из файла и конкретной поисковой системы
    :param query_list:
    :param search:
    :return: list_of_dict
    """
    mark_data = []
    for query in query_list:
        dict_data = {
            "query": query,
            "search": search,
        }

        marks = [int(x) for x in input("input mark: ").split(" ")]
        dict_data["marks"] = marks

        mark_data.append(dict_data)

    return mark_data


def get_articles_from_google(query):
    article = []
    limit = 10
    for g in search(query + "site:wikipedia.org", tld="co.in", num=limit, stop=limit, pause=2, lang="ru"):
        title = unquote(g).replace("https://ru.wikipedia.org/wiki/", "")
        if title:
            article.append(title)

    return article


for q in query_list:
    print(q, get_articles_from_google(q))
