import math
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


def gen_skip_list(input_list):
    n = len(input_list)
    step = int(n/int(math.sqrt(n)))
    return input_list[::step]


def get_ans_with_skip_list(first_list, second_list):
    skip_index1 = 0
    skip_index2 = 0

    # скип-листы
    skip1 = gen_skip_list(first_list)
    skip2 = gen_skip_list(second_list)

    # step_for_first_list - переменная показывает, на сколько нужно нужно переместить итератор в списке, если
    # произошел ОДИН прыжок по индексу
    n1 = len(first_list)
    step_for_first_list1 = int(n1/int(math.sqrt(n1)))
    n2 = len(second_list)
    step_for_first_list2 = int(n1/int(math.sqrt(n2)))

    first = 0
    second = 0
    answer = list()
    while True:

        if first >= len(first_list) or second >= len(second_list):
            return answer

        first_elem = first_list[first]
        second_elem = second_list[second]
        step = 1

        if first_elem == second_elem:
            answer.append(first_elem)

            first += 1
            second += 1

            if skip_index1 < len(skip1) and first_elem == skip1[skip_index1]:
                skip_index1 += 1
            if skip_index2 < len(skip2) and second_elem == skip2[skip_index2]:
                skip_index2 += 1

        elif first_elem < second_elem:

            if skip_index1 < len(skip1) and skip1[skip_index1] == first_elem:
                if skip_index1 + step < len(skip1) and skip1[skip_index1 + step] < second_elem:
                    # пытаемтся двигаться в скип-листе
                    while skip1[skip_index1 + step] < second_elem:
                        step += 1
                    first += step * step_for_first_list1
                first += step
                skip_index1 += step
            else:
                first += step
        else:

            if skip_index2 < len(skip2) and skip2[skip_index2] == second_elem:
                if skip_index2 + step < len(skip2) and skip2[skip_index2 + step] < first_elem:
                    # пытаемтся двигаться в скип-листе
                    while skip2[skip_index2 + step] < first_elem:
                        step += 1
                    second += step * step_for_first_list2
                second += step
                skip_index2 += step
            else:
                second += step

    # return answer


if __name__ == '__main__':
    list_count = 2
    res_for_search = [sorted(set(gen_list(MAX_VALUE))) for _ in range(list_count)]

    t1 = datetime.now()
    print(len(reduce(lambda a, x: work(a, x), res_for_search)))
    print(f"Work compare: {datetime.now() - t1}")

    t1 = datetime.now()
    print(len(reduce(lambda a, x: get_simple_compare(a, x), res_for_search)))
    print(f"Simple compare: {datetime.now() - t1}")

    t1 = datetime.now()
    print(len(reduce(lambda a, x: get_set_compare(a, x), res_for_search)))
    print(f"Python sets compare: {datetime.now() - t1}")

    t1 = datetime.now()
    print(len(reduce(lambda a, x: get_ans_with_skip_list(a, x), res_for_search)))
    print(f"Skip list compare: {datetime.now() - t1}")
