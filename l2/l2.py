import nltk
import string
from nltk.corpus import stopwords
from collections import Counter
from os import walk
import json
import re
from itertools import chain
from nltk.tokenize import ToktokTokenizer
from datetime import datetime

PUNCTUATION = string.punctuation + '—«»'
WORD = re.compile(r'\w+')


def get_articles_name():
    mypath = '../data/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    files_name = ["~/stud/search/data/" + x for x in f]

    return files_name


def tokenize_me(file_text):
    # для 1000  0:00:03.916178
    # для 15000 0:00:59.223518
    tokens = nltk.word_tokenize(file_text, 'russian')
    tokens = Counter((i.lower() for i in tokens if (i not in PUNCTUATION and len(i))))
    return tokens

def tokenize_me_1(file_text):
    # для 1000  0:00:00.770187
    # для 15000 0:00:10.593748
    words = WORD.findall(file_text)
    return Counter((word.lower() for word in words if len(word)))

def tokenize_me_2(file_text):
    # для 1000  0:00:02.934344
    # для 15000 0:00:41.782110
    toktok = ToktokTokenizer()
    tokenized_corpus = (toktok.tokenize(sent) for sent in nltk.sent_tokenize(file_text))

    return Counter((token.lower() for token in chain(*tokenized_corpus) if token not in PUNCTUATION and len(token)))

# Копирование 1000  элементов - 0:00:00.08
# Копирование 15000 элементов - 0:00:01.14

if __name__ == "__main__":
    articles = get_articles_name()

    t = datetime.now()
    for article in articles:
        article_num = article[27:]
        with open('../data/article-' + article_num, 'r') as source:
            text = source.read()
            # with open("../data-tokens-tmp/token-" + article_num, 'w') as fp:
            #     fp.write(text)
            # tokens = tokenize_me(text)
            tokens = tokenize_me_1(text)
            # tokens = tokenize_me_2(text)
            with open("../data-tokens-tmp/token-" + article_num, 'w') as fp:
                json.dump(tokens, fp, sort_keys=True,
                        ensure_ascii=False, indent=4, separators=(',', ': '))
    print(datetime.now()-t)