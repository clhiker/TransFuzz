from utils import find_nth
from ts_log import MyLog


def babel_err(std_err):
    try:
        stderr = std_err.split('\n')[0].split(':')
        if len(stderr) > 2:
            return stderr[0] + stderr[2]
        else:
            return stderr[0] + stderr[1]
    except:
        print('在读取babel报错的时候出现了一个错误.')
        return ''


def swc_err(std_err):
    std_err = std_err.split('\n')[1]
    std_err = std_err[find_nth(std_err, ' ', 3) + 1:]
    return std_err
    # try:
    #     std_err = std_err.split('\n')[1]
    #     std_err = std_err[find_nth(std_err, ' ', 3) + 1:]
    #     return std_err
    # except:
    #     print('在读取swc报错的时候出现了一个错误.')
    #     return ''


def jshint_err(std_err):
    try:
        info = std_err.split('\n')
    except AttributeError:
        print('在读取jshint报错的时候出现了一个错误.')
        info = []
    for error_info in info:
        if "(use 'esversion: " in error_info:
            return error_info[find_nth(error_info, ',', 2) + 2:
                              error_info.find("(use 'esversion: ")]
    return None


def node_err(std_err):
    v8_errs = ['EvalError', 'SyntaxError', 'RangeError', 'ReferenceError', 'TypeError', 'URIError']
    try:
        info = std_err.split('\n')
    except AttributeError:
        print('在读取node报错的时候出现了一个错误.')
        info = []
    for it in info:
        for err in v8_errs:
            if err in it:
                return it
    return None
