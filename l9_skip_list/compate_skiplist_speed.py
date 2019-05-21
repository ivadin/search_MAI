import random
from functools import reduce
from datetime import datetime

MAX_VALUE = 100000
LIST_CH = [x * random.choice([1, 2, 3]) for x in range(MAX_VALUE)]


def gen_list(list_len):
    return random.choices(LIST_CH, k=list_len)


def get_simple_compare(list_temp_res, next_list):
    return set([x for x in list_temp_res if x in next_list])


def get_set_compare(set_temp_res, next_set):
    return set(set_temp_res) & set(next_set)


def work(first_list_docid, second_list_docid):
    res = []
    first_id = 0
    second_id = 0
    while first_id < len(first_list_docid):
        while second_id < len(second_list_docid):

            if first_id >= len(first_list_docid) or second_id >= len(second_list_docid):
                return res

            if first_list_docid[first_id] < second_list_docid[second_id]:
                first_id += 1
                if first_id == len(first_list_docid):
                    return res

            elif first_list_docid[first_id] == second_list_docid[second_id]:
                res.append(first_list_docid[first_id])
                first_id += 1
                second_id += 1
                if first_id == len(first_list_docid) or second_id == len(second_list_docid):
                    return res

            else:
                second_id += 1
                if second_id == len(second_list_docid):
                    return res
    return res


if __name__ == '__main__':
    list_count = 5
    res_for_search = [sorted(set(gen_list(MAX_VALUE))) for _ in range(list_count)]

    t1 = datetime.now()
    print(len(reduce(lambda a, x: work(a, x), res_for_search)))
    print(f"Simple compare: {datetime.now() - t1}")

    t1 = datetime.now()
    print(len(reduce(lambda a, x: get_simple_compare(a, x), res_for_search)))
    print(f"Simple compare: {datetime.now() - t1}")

    t1 = datetime.now()
    print(len(reduce(lambda a, x: get_set_compare(a, x), res_for_search)))
    print(f"Simple compare: {datetime.now() - t1}")
