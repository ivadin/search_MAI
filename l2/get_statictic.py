import json
from os import walk

def get_tokens_name():
    mypath = '../data-tokens/'
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    files_name = ["../data-tokens/" + x for x in f]

    return files_name

if __name__ == "__main__":
    tokens = get_tokens_name()

    my_set = set()
    for token in tokens:
        with open(token, 'r') as data:
            json_dict = json.load(data)
            my_set = my_set | set(json_dict)
    tokens_counts = len(my_set)
    print("Tokens count: ",  tokens_counts)

    all_tokens_len = 0
    for elem in my_set:
        all_tokens_len += len(elem)
    print("Average: ", all_tokens_len // tokens_counts)
