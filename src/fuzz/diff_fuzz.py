import re
import subprocess

from subprocess import PIPE
from utils.err_info import node_err
from utils.multi_p import pool


def simplify_result(text):
    try:
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s', ' ', text)
        text = re.sub(r'\\t', ' ', text)
        text = re.sub(r' +', '', text)
    except TypeError:
        print(text)
    return text


def run_by_node(js_path):
    cmd = ['node'] + [js_path]
    try:
        res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        if res.returncode == 0:
            return 0, res.stdout.decode('utf-8')
        else:
            return -1, res.stderr.decode('utf-8')

    except subprocess.TimeoutExpired:
        return -15, None


class Diff_FUZZ:
    def __init__(self,
                 bug_dict,
                 bug_name_set,
                 invalid_bugs
                 ):
        self.bug_dict = bug_dict
        self.bug_name_set = bug_name_set
        self.invalid_bugs = invalid_bugs

    def read_bug(self, return_code, ori_out, std_out, js_name, trans):
        if return_code == 0:
            ori_out = simplify_result(ori_out)
            std_out = simplify_result(std_out)
            if ori_out != std_out:
                if 'diff_res' not in self.bug_dict[trans]['semantics']:
                    self.bug_dict[trans]['semantics']['diff_res'] = [js_name]
                else:
                    self.bug_dict[trans]['semantics']['diff_res'].append(js_name)
                self.bug_name_set.add(js_name)

        elif return_code == 15:
            err_info = 'timeout'
            if err_info not in self.bug_dict[trans]['semantics']:
                self.bug_dict[trans]['semantics'][err_info] = [js_name]
            else:
                self.bug_dict[trans]['semantics'][err_info].append(js_name)
            self.bug_name_set.add(js_name)

        else:
            err_info = node_err(std_out)

            for invalid in self.invalid_bugs[trans]['semantics']:
                if err_info and invalid in err_info:
                    return False
            if err_info not in self.bug_dict[trans]['semantics']:
                self.bug_dict[trans]['semantics'][err_info] = [js_name]
            else:
                self.bug_dict[trans]['semantics'][err_info].append(js_name)
            self.bug_name_set.add(js_name)

    def single_diff(self, paras):
        js_path, babel_to_path, swc_to_path = paras
        js_name = js_path[js_path.rfind('/') + 1:]
        ori_code, ori_out = run_by_node(js_path)
        if babel_to_path:
            babel_code, babel_out = run_by_node(babel_to_path)
            self.read_bug(babel_code, ori_out, babel_out, js_name, 'babel')

        if swc_to_path:
            swc_code, swc_out = run_by_node(swc_to_path)
            self.read_bug(swc_code, ori_out, swc_out, js_name, 'swc')

    def multi_diff(self, ok_seeds_path, babel_path_list, swc_path_list):
        temp = {}
        paras = []
        for item in ok_seeds_path:
            id, ok_seeds = item
            temp[id] = [ok_seeds]
        for item in babel_path_list:
            id, babel_path = item
            temp[id].append(babel_path)
        for item in swc_path_list:
            id, swc_path = item
            temp[id].append(swc_path)
        for values in temp.values():
            paras.append(tuple(values))

        pool.map(self.single_diff, paras)

    def run(self, ok_seeds_path, babel_path_list, swc_path_list):
        self.multi_diff(ok_seeds_path, babel_path_list, swc_path_list)
