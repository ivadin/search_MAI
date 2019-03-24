import json
from datetime import datetime

import wikipedia
from googlesearch import search as google_search
from urllib.parse import unquote
import numpy as np

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


def read_query_and_get_raw_search_res():
    """
    получение 2х json-ов c 10-ю результатами на каждый запрос. оценки marks
    ставить вручную
    :return:
    """
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


def count_p(query, n):
    """
    Рассчет метрики P@n для запроса Q
    :param query:
    :param n:
    :return:
    """
    x = (np.array(query["marks"][0:n]) > 2)
    return sum(x) / n


def count_dcg(query, n):
    """
    Рассчет метрики DCG@n для запроса Q
    :param query:
    :param n:
    :return:
    """
    x = np.array(np.array(query["marks"][0:n]))
    y = np.log2(np.arange(2, n + 2))
    return sum(x / y)


def count_ndcg(query, n):
    """
    Рассчет метрики NDCG@n для запроса Q
    :param query:
    :param n:
    :return:
    """
    idcg = 5 * n
    return count_dcg(query, n) / idcg


def count_err(query, n):
    """
    Рассчет метрики ERR@n для запроса Q
    :param query:
    :param n:
    :return:
    """
    max_grade = max(query["marks"][0:n])
    grades = (np.power(2, np.array(query["marks"][0:n])) - 1) / np.power(2, max_grade)
    error = 0
    p = 1
    r = 1

    for grade in grades:
        error += p * grade / r
        p = p * (1 - grade)
        r += 1

    return error


def count_avg_metrix(search, p1_avg, p3_avg, p5_avg, dcg1_avg, dcg3_avg, dcg5_avg,
                     ndcg1_avg, ndcg3_avg, ndcg5_avg, err1_avg, err3_avg, err5_avg):
    return {
        "search_sys": search,
        "P@1": np.mean(p1_avg),
        "P@3": np.mean(p3_avg),
        "P@5": np.mean(p5_avg),
        "DCG@1": np.mean(dcg1_avg),
        "DCG@3": np.mean(dcg3_avg),
        "DCG@5": np.mean(dcg5_avg),
        "NDCG@1": np.mean(ndcg1_avg),
        "NDCG@3": np.mean(ndcg3_avg),
        "NDCG@5": np.mean(ndcg5_avg),
        "ERR@1": np.mean(err1_avg),
        "ERR@3": np.mean(err3_avg),
        "ERR@5": np.mean(err5_avg),
    }


if __name__ == '__main__':
    logger.info('Start')

    metrix = []

    p1g_avg = []
    p1w_avg = []

    p3g_avg = []
    p3w_avg = []

    p5g_avg = []
    p5w_avg = []

    dcg1g_avg = []
    dcg1w_avg = []

    dcg3g_avg = []
    dcg3w_avg = []

    dcg5g_avg = []
    dcg5w_avg = []

    ndcg1g_avg = []
    ndcg1w_avg = []

    ndcg3g_avg = []
    ndcg3w_avg = []

    ndcg5g_avg = []
    ndcg5w_avg = []

    err1g_avg = []
    err1w_avg = []

    err3g_avg = []
    err3w_avg = []

    err5g_avg = []
    err5w_avg = []

    with open(google_mark_data_file, 'r') as gmdf:
        with open(wikipedia_mark_data_file, 'r') as wmdf:
            gmdf_list = json.load(gmdf)
            wmdf_list = json.load(wmdf)

            counted_metrix_for_queries = {}

            for q1, q2 in zip(gmdf_list, wmdf_list):
                if q1["query"] == q2["query"]:
                    counted_metrix_for_queries["query"] = q1["query"]
                    # P
                    p1g = count_p(q1, 1)
                    p1g_avg.append(p1g)
                    p1w = count_p(q2, 1)
                    p1w_avg.append(p1w)

                    p3g = count_p(q1, 3)
                    p3g_avg.append(p3g)
                    p3w = count_p(q2, 3)
                    p3w_avg.append(p3w)

                    p5g = count_p(q1, 5)
                    p5g_avg.append(p5g)
                    p5w = count_p(q2, 5)
                    p5w_avg.append(p5w)

                    counted_metrix_for_queries["P_google"] = [p1g, p3g, p5g]
                    counted_metrix_for_queries["P_wiki"] = [p1w, p3w, p5w]
                    # DCG
                    dcg1g = count_dcg(q1, 1)
                    dcg1g_avg.append(dcg1g)
                    dcg1w = count_dcg(q2, 1)
                    dcg1w_avg.append(dcg1w)

                    dcg3g = count_dcg(q1, 3)
                    dcg3g_avg.append(dcg3g)
                    dcg3w = count_dcg(q2, 3)
                    dcg3w_avg.append(dcg3w)

                    dcg5g = count_dcg(q1, 5)
                    dcg5g_avg.append(dcg5g)
                    dcg5w = count_dcg(q2, 5)
                    dcg5w_avg.append(dcg5w)

                    counted_metrix_for_queries["DCG_google"] = [dcg1g, dcg3g, dcg5g]
                    counted_metrix_for_queries["DCG_wiki"] = [dcg1w, dcg3w, dcg5w]
                    # NDCG
                    ndcg1g = count_ndcg(q1, 1)
                    ndcg1g_avg.append(ndcg1g)
                    ndcg1w = count_ndcg(q2, 1)
                    ndcg1w_avg.append(ndcg1w)

                    ndcg3g = count_ndcg(q1, 3)
                    ndcg3g_avg.append(ndcg3g)
                    ndcg3w = count_ndcg(q2, 3)
                    ndcg3w_avg.append(ndcg3w)

                    ndcg5g = count_ndcg(q1, 5)
                    ndcg5g_avg.append(ndcg5g)
                    ndcg5w = count_ndcg(q2, 5)
                    ndcg5w_avg.append(ndcg5w)

                    counted_metrix_for_queries["NDCG_google"] = [ndcg1g, ndcg3g, ndcg5g]
                    counted_metrix_for_queries["NDCG_wiki"] = [ndcg1w, ndcg3w, ndcg5w]
                    # ERR
                    err1g = count_ndcg(q1, 1)
                    err1g_avg.append(err1g)
                    err1w = count_ndcg(q2, 1)
                    err1w_avg.append(err1w)

                    err3g = count_ndcg(q1, 3)
                    err3g_avg.append(err3g)
                    err3w = count_ndcg(q2, 3)
                    err3w_avg.append(err3w)

                    err5g = count_ndcg(q1, 5)
                    err5g_avg.append(err5g)
                    err5w = count_ndcg(q2, 5)
                    err5w_avg.append(err5w)

                    counted_metrix_for_queries["ERR_google"] = [err1g, err3g, err5g]
                    counted_metrix_for_queries["ERR_wiki"] = [err1w, err3w, err5w]

                    metrix.append(counted_metrix_for_queries)

    counted_metrix = "counted_metrix.json"
    metrix.append(count_avg_metrix(
        "qoogle",
        p1g_avg,
        p3g_avg,
        p3g_avg,
        dcg1g_avg,
        dcg3g_avg,
        dcg5g_avg,
        ndcg1g_avg,
        ndcg3g_avg,
        ndcg5g_avg,
        err1g_avg,
        err3g_avg,
        err5g_avg,
    ))
    metrix.append(count_avg_metrix(
        "wiki",
        p1w_avg,
        p3w_avg,
        p3w_avg,
        dcg1w_avg,
        dcg3w_avg,
        dcg5w_avg,
        ndcg1w_avg,
        ndcg3w_avg,
        ndcg5w_avg,
        err1w_avg,
        err3w_avg,
        err5w_avg,
    ))
    with open(counted_metrix, 'w') as cm:
        json.dump(metrix, cm, ensure_ascii=False, indent=4, separators=(',', ': '))

    logger.info("Success")

