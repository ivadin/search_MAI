import logging
import wikipediaapi

from datetime import datetime

logging.basicConfig(filename="sample.log", level=logging.INFO, filemode='w')

def getArticlesList(categorymembers, level=0, max_level=2):
	articlesList = []
	for c in categorymembers.values():
		if c.ns == wikipediaapi.Namespace.CATEGORY and level < max_level:
			articlesList += getArticlesList(c.categorymembers, level=level + 1, max_level=max_level)
		if c.ns == wikipediaapi.Namespace.MAIN:
			articlesList.append(c.title)
	return articlesList


if __name__ == "__main__":
    wiki_wiki = wikipediaapi.Wikipedia(
        language='ru',
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    cat = wiki_wiki.page("Категория:Спорт")

    logging.info("Downloading articles...")
    t1 = datetime.now()

    articles = getArticlesList(cat.categorymembers)

    article_counter = 0

    logging.info("Texts downloading...")
    for name in articles:
        article_counter += 1
        try:
            page = wiki_wiki.page(name)
            f = open("data/article-" + str(article_counter) + '.txt', "w+", encoding='utf8')
            text = page.text
            f.write(text)
            f.close()
        except Exception as exc:
            logging.info(exc)
            continue

    logging.info("Timet spending:" % str(datetime.now() - t1))
