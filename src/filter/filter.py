import copy
import os

from utils import load_json, keep_json


class FilterTestCase:
    def __init__(self,
                 bug_keep_path,
                 bug_dict_path,
                 found_bug_path,
                 filter_bug_path,
                 ):
        self.bug_keep_path = bug_keep_path
        self.bug_dict_path = bug_dict_path
        self.found_bug_path = found_bug_path
        self.filter_dict_path = filter_bug_path
        self.bug_dict = {}
        self.found_bug = {}

    def load_data(self):
        self.bug_dict = load_json(self.bug_dict_path)
        self.found_bug = load_json(self.found_bug_path)
        if os.path.exists(self.filter_dict_path):
            os.remove(self.filter_dict_path)

    def filter(self):
        temp_bug_dict = copy.deepcopy(self.bug_dict)

        for trans in self.bug_dict.keys():
            for bug_type in self.bug_dict[trans].keys():
                if len(self.bug_dict[trans][bug_type]) > 0:
                    bugs = self.bug_dict[trans][bug_type].keys()
                    for bug in bugs:
                        if bug == 'diff_res':
                            for js in self.bug_dict[trans][bug_type][bug]:
                                js_path = os.path.join(self.bug_keep_path, js)
                                try:
                                    with open(js_path, 'r') as f:
                                        text = f.read()
                                except IOError:
                                    continue
                                for item in self.found_bug['special']:
                                    if item in text:
                                        temp_bug_dict[trans][bug_type][bug].remove(js)
                                        break
                        elif 'is defined multiple times' in bug or 'TypeError Duplicate declaration' in bug:
                            temp_bug_dict[trans][bug_type].pop(bug)
                        else:
                            for found_bug in self.found_bug[trans][bug_type]:
                                if found_bug in bug:
                                    try:
                                        temp_bug_dict[trans][bug_type].pop(bug)
                                    except KeyError as err:
                                        print(err)

        keep_json(self.filter_dict_path, temp_bug_dict)

    def main(self):
        print('------------------提取bug报告-----------------')
        self.load_data()
        print('------------------过滤已发现的bug--------------\n')
        self.filter()


if __name__ == '__main__':
    filter_test = FilterTestCase(
        '../corpus/es6plus-git/bug',
        'bug/bug.json',
        'bug/found-bug.json',
        'bug/filter-bug.json',
    )
    filter_test.main()