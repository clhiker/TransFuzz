import os
import re
import shutil
import subprocess
import time
import sys

from subprocess import PIPE
from filediff.diff import file_diff_compare
import func_timeout
from utils.err_info import node_err
from utils.multi_p import pool, RunCmd, read_stdout
from utils import load_json, keep_json, re_simply, rm_value_dup


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


class Diff_TEST:
    def __init__(self,
                 home_path,
                 bug_path,
                 bug_keep_path
                 ):
        self.home_path = home_path
        self.bug_path = bug_path
        self.bug_keep_path = bug_keep_path
        self.babel_config_path = '../babel/babel-es6.json'
        self.swc_config_path = os.path.abspath('conf/js/swc-es6.json')
        self.babel_ori_res_path = os.path.join(self.home_path, 'ori-babel.json')
        self.babel_res_path = os.path.join(self.home_path, 'babel.json')
        self.swc_ori_res_path = os.path.join(self.home_path, 'ori-swc.json')
        self.swc_res_path = os.path.join(self.home_path, 'swc.json')
        self.init_dir()
        self.temp_res_dict = {}

    def init_dir(self):
        if os.path.exists(self.home_path):
            shutil.rmtree(self.home_path)
        os.mkdir(self.home_path)

        self.to_path = os.path.join(self.home_path, 'to_path')
        if not os.path.exists(self.to_path):
            os.mkdir(self.to_path)
        self.babel_to_path = os.path.join(self.to_path, 'babel')
        if not os.path.exists(self.babel_to_path):
            os.mkdir(self.babel_to_path)
        self.swc_to_path = os.path.join(self.to_path, 'swc')
        if not os.path.exists(self.swc_to_path):
            os.mkdir(self.swc_to_path)

    # 检查语义错误
    def multi_check_semantics(self, trans, bug_list):
        if trans == 'babel':
            seed_path_list = [os.path.join(self.bug_keep_path, bug) for bug in bug_list]
            trans_path_list = [os.path.join(self.babel_to_path, js) for js in os.listdir(self.babel_to_path)]
            home_path_list = [seed_path_list, trans_path_list]
            res_path_list = [self.babel_ori_res_path, self.babel_res_path]

            for i in range(len(home_path_list)):
                print('begin run ' + trans)
                # 并发跑
                self.temp_res_dict.clear()
                pool.map(self.run_by_node, home_path_list[i])
                time.sleep(3)
                keep_json(res_path_list[i], self.temp_res_dict)

        elif trans == 'swc':
            seed_path_list = [os.path.join(self.bug_keep_path, bug) for bug in bug_list]
            trans_path_list = [os.path.join(self.swc_to_path, js) for js in os.listdir(self.swc_to_path)]
            home_path_list = [seed_path_list, trans_path_list]
            res_path_list = [self.swc_ori_res_path, self.swc_res_path]

            for i in range(len(home_path_list)):
                print('begin run ' + trans)
                # 并发跑
                self.temp_res_dict.clear()
                pool.map(self.run_by_node, home_path_list[i])
                time.sleep(3)
                keep_json(res_path_list[i], self.temp_res_dict)

    def run_by_node(self, js_path):
        cmd = ['node'] + [js_path]
        try:
            return_code, std_out = RunCmd(cmd, 3).Run()
        except:
            return
        try:
            # 防阻塞
            std_out = read_stdout(std_out)
        except func_timeout.exceptions.FunctionTimedOut:
            print('node run timeout' + js_path)
            return -1
        if return_code == 0:
            self.temp_res_dict[js_path[js_path.rfind('/') + 1:]] = std_out

    def multi_trans(self, trans, bugs):
        bug_path_list = [os.path.join(self.bug_keep_path, bug) for bug in bugs]
        trans = [trans for i in range(len(bugs))]
        pool.map(self.single_trans, zip(trans, bug_path_list))

    def single_trans(self, paras):
        trans, test_path = paras
        from_path = test_path
        name = test_path[test_path.rfind('/') + 1:]

        if trans == 'babel':
            babel_to_path = os.path.join(self.babel_to_path, name)
            cmd = ['../babel/node_modules/.bin/babel'] + \
                  ['--config-file', self.babel_config_path] + \
                  [from_path] + ['-o', babel_to_path]

        elif trans == 'swc':
            swc_to_path = os.path.join(self.swc_to_path, name)
            cmd = ['npx', 'swc'] + ['-s', 'inline'] + \
                  ['--config-file=' + self.swc_config_path] + \
                  [os.path.abspath(from_path)] + ['-o', os.path.abspath(swc_to_path)]

            if self.transpiler_js(cmd):
                while not os.path.exists(swc_to_path):  # 代码陷阱，在性能问题下对并发的补充
                    self.transpiler_js(cmd)
                    time.sleep(1)
            else:
                print(name + '转译失败')

    def transpiler_js(self, cmd):
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=30)
            if res.returncode != 0:
                return False
            else:
                return True
        except subprocess.TimeoutExpired as time_err:
            print(cmd[-1] + '转译超时')
            return False

    def simplify_result(self):
        res_path_list = {
            self.babel_ori_res_path: self.babel_res_path,  # 之后要添加上
            self.swc_ori_res_path: self.swc_res_path
        }
        for res_path in res_path_list.keys():
            ori_temp = dict()
            to_temp = dict()
            try:
                ori_dict = load_json(res_path)
                to_dict = load_json(res_path_list[res_path])
            except FileNotFoundError:
                continue
            for key in ori_dict.keys():
                ori_text = ori_dict[key]
                if re.search('function', ori_text, re.IGNORECASE):
                    continue
                if re.search('Object', ori_text, re.IGNORECASE):
                    continue
                if ori_text.lower().find('class') > 0:
                    continue
                ori_text = re_simply(ori_text)
                ori_temp.update({key: ori_text})

            ori_temp = rm_value_dup(ori_temp)  # 筛重
            ori_temp = dict(sorted(ori_temp.items(), key=lambda it: it[0]))  # 排序
            for ori_key in ori_temp:
                to_temp.update({ori_key: re_simply(to_dict[ori_key])})
            to_temp = dict(sorted(to_temp.items(), key=lambda it: it[0]))

            keep_json(res_path, ori_temp)
            keep_json(res_path_list[res_path], to_temp)

    def diff_print(self, diff_res_path):
        file_diff_compare(self.swc_ori_res_path,
                          self.swc_res_path,
                          diff_out=diff_res_path,
                          max_width=70,
                          numlines=0,
                          show_all=False,
                          no_browser=True)

    def run(self, diff_res_path):
        bug_dict = load_json(self.bug_path)
        try:
            babel_bugs = bug_dict['babel']['semantics']['diff_res']
            self.multi_trans('babel', babel_bugs)
            self.multi_check_semantics('babel', babel_bugs)
            self.simplify_result()
            self.diff_print(diff_res_path)
        except KeyError as err:
            print(err, end=' ')
            print('不存在')

        swc_bugs = bug_dict['swc']['semantics']['diff_res']
        self.multi_trans('swc', swc_bugs)
        self.multi_check_semantics('swc', swc_bugs)
        self.simplify_result()
        self.diff_print(diff_res_path)


if __name__ == '__main__':
    config_path = sys.argv[1]
    config_dict = load_json(config_path)
    temp_path = sys.argv[2]
    diff_res_path = sys.argv[3]
    diff_test = Diff_TEST(
        temp_path,
        config_dict['filter_bug_path'],
        config_dict['seeds_path']
    )
    diff_test.run(diff_res_path)
