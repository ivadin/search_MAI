import json
from datetime import datetime

import wikipedia
from googlesearch import search as google_search
from urllib.parse import unquote

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wikipedia.set_lang('ru')
queries = "q.json"
wikipedia_mark_data_file = "wikipedia_mark_data.json"
google_mark_data_file = "google_mark_data.json"

wikipedia_mark_data_list = []
google_mark_data = []
limit = 10


def dump_not_marked_data(query_list, search_sys):
    """
    Создает list_of_ditc и грузит его в json для того, что бы можно было проерить поисковую выдачу и отрефакторить ее
    и потом проставить оценки
    :param query_list:
    :param search:
    :return:
    """
    if search_sys == "google":
        search_resource = get_articles_from_google
        json_file = google_mark_data_file
    elif search_sys == "wiki":
        search_resource = get_articles_from_wiki
        json_file = wikipedia_mark_data_file

    unmark_data = []
    for query in query_list:
        dict_data = {
            "query": query,
            "search_sys": search_sys,
            "search_result": search_resource(query)
        }
        unmark_data.append(dict_data)

    with open(json_file, 'w') as gmd:
        json.dump(unmark_data, gmd, ensure_ascii=False, indent=4, separators=(',', ': '))


def get_articles_from_google(query):
    article = []
    for url in google_search(query + "site:wikipedia.org", tld="co.in", num=limit, stop=limit, pause=2, lang="ru"):
        # вырезаем только первое взождение url (больше быть не должно, но мало ли)
        title = unquote(url).replace("https://ru.wikipedia.org/wiki/", "", 1)
        if title:
            article.append(title)
    logger.info("For query: %s Articles: %s" % (query, article))
    return article


def get_articles_from_wiki(query):
    article = []
    for w in wikipedia.search(query=query, results=limit):
        article.append(w)
    logger.info("For query: %s Articles: %s" % (query, article))
    return article


if __name__ == '__main__':
    logger.info('Start')

    logger.info('Reading queries')
    with open(queries, 'r') as my_file:
        raw_query = my_file.read()
        query_list = json.loads(raw_query)
    logger.info('Reading success')

    logger.info('Getting and dump seaerch result from google')
    t1 = datetime.now()
    dump_not_marked_data(query_list=query_list, search_sys="google")
    logger.info('Searching result got and dumped by %s' % (datetime.now() - t1))

    logger.info('Searchi and dump seaerch result from wiki')
    t1 = datetime.now()
    dump_not_marked_data(query_list=query_list, search_sys="wiki")
    logger.info('Searching result got and dumped by %s' % (datetime.now() - t1))
