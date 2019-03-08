import nltk
import string
from nltk.corpus import stopwords
from collections import Counter
from os import walk
import json
from datetime import datetime


def get_articles_name():
    mypath = '../data/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    files_name = ["~/stud/search/data/" + x for x in f]

    return files_name


def tokenize_me(file_text):
    tokens = nltk.word_tokenize(file_text)

    tokens = [i.lower() for i in tokens if ( i not in string.punctuation )]

    stop_words = stopwords.words('russian')
    ext_stop_words = ['—']
    stop_words.extend(ext_stop_words)
    tokens = Counter([i.replace("«", "").replace("»", "")
        for i in tokens if (i not in stop_words and len(i.replace("«", "").replace("»", "")))])
    return tokens


if __name__ == "__main__":
    articles = get_articles_name()

    t = datetime.now()
    for article in articles:
        article_num = article[27:]
        article_num = "1.txt"
        with open('../data/article-' + article_num, 'r') as source:
            text = source.read()
            with open("../data-tokens/token-" + article_num, 'w') as fp:
                json.dump(tokens, fp, sort_keys=True,
                        ensure_ascii=False, indent=4, separators=(',', ': '))
    print(datetime.now()-t)