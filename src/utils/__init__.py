import json
import re
import sys
import ujson


def keep_json(json_path, json_dict):
    try:
        with open(json_path, 'w') as hf:
            hf.write(json.dumps(json_dict, indent=1))
    except IOError:
        print('存储' + json_path + '出错')


def load_json(json_path):
    with open(json_path, 'r') as f:
        try:
            json_data = ujson.load(f)
        except ValueError as ve:
            dec = json.JSONDecoder()
            f.seek(0, 0)
            json_data = f.read()
            json_data = dec.decode(json_data)
    return json_data


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


class TailRecurseException(BaseException):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def tail_call_optimized(g):
    """
    This function decorates a function with tail call
    optimization. It does this by throwing an exception
    if it is it's own grandparent, and catching such
    exceptions to fake the tail call optimization.

    This function fails if the decorated
    function recurses in a non-tail context.
    """
    def func(*args, **kwargs):
        f = sys._getframe()
        # sys._getframe(): 当前调用栈
        # f_back: 栈顶元素 next outer frame object
        # f_back.f_back: 栈顶第二元素
        # f_code: code object being executed in this frame
        if f.f_back and f.f_back.f_back and f.f_back.f_back.f_code == f.f_code:
            raise TailRecurseException(args, kwargs)
        else:
            while 1:
                try:
                    return g(*args, **kwargs)
                except TailRecurseException as e:
                    args = e.args
                    kwargs = e.kwargs
    func.__doc__ = g.__doc__
    return func


def re_simply(text):
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s', ' ', text)
    text = re.sub(r'\\t', ' ', text)
    text = re.sub(r' +', '', text)
    return text


rm_dup = lambda z: dict([(x, y) for y, x in z.items()])


def rm_value_dup(_dict):
    return rm_dup(rm_dup(_dict))
