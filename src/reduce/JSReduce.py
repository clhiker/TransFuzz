import os.path
import shutil
import subprocess
import func_timeout
import sys
from subprocess import PIPE

from utils.multi_p import RunCmd, read_stdout
from utils import load_json, keep_json
from utils.err_info import babel_err, swc_err, jshint_err


class JSReduce:
    def __init__(self,
                 filter_bug_path,
                 bug_home_path,
                 seeds_path
                 ):
        self.filter_bug_path = filter_bug_path
        self.bug_home_path = bug_home_path
        self.seeds_path = seeds_path
        self.filter_bug = load_json(self.filter_bug_path)
        self.babel_config_path = 'conf/js/babel-es6.json'
        self.swc_config_path = 'conf/js/swc-es6.json'
        self.jshint_es5_config_path = 'conf/js/jshint-es5.json'

    def reduce(self):
        for trans in self.filter_bug.keys():
            bug_trans_path = os.path.join(self.bug_home_path, trans)  # ../bug/XXX
            if os.path.exists(bug_trans_path):
                shutil.rmtree(bug_trans_path)
            os.mkdir(bug_trans_path)
            for bug_type in self.filter_bug[trans].keys():
                print('开始缩减' + trans + ' ' + bug_type + '类型的bug')
                for bug in self.filter_bug[trans][bug_type].keys():
                    js_list = self.filter_bug[trans][bug_type][bug]             # 测试用例名字列表
                    for js in js_list:
                        ori_js_path = os.path.join(self.seeds_path, js)         # 原始测试用例位置
                        temp_ast_path = os.path.join(self.bug_home_path, 'temp.json')
                        try:
                            des_ast = self.parse_js(ori_js_path, temp_ast_path)
                        except FileNotFoundError:
                            print('初始解析发生错误')
                            continue
                        i = len(des_ast['body']) - 1
                        while i >= 0:
                            temp_ast = des_ast['body'][i]
                            des_ast['body'].pop(i)
                            temp_code_path = os.path.join(self.bug_home_path, 'temp.js')
                            temp_trans_path = os.path.join(self.bug_home_path, 'temp-trans.js')
                            if self.gen_js(des_ast, temp_ast_path, temp_code_path):     # 生成临时缩减后JS
                                if bug_type == 'ori':
                                    if self.trans_check(trans, temp_code_path, bug):
                                        pass
                                    else:
                                        des_ast['body'].insert(i, temp_ast)
                                elif bug_type == 'syntax':
                                    if self.trans_js(trans, temp_code_path, temp_trans_path).returncode == 0:
                                        if self.lint_check(temp_trans_path, bug):
                                            pass
                                        else:
                                            des_ast['body'].insert(i, temp_ast)
                                    else:
                                        des_ast['body'].insert(i, temp_ast)
                                elif bug_type == 'semantics':
                                    if self.trans_js(trans, temp_code_path, temp_trans_path).returncode == 0:
                                        if bug == 'diff_res':
                                            if self.diff_node_check(trans, temp_code_path, temp_trans_path):
                                                pass
                                            else:
                                                des_ast['body'].insert(i, temp_ast)
                                        else:
                                            if self.err_node_check(trans, temp_code_path, temp_trans_path, bug):
                                                pass
                                            else:
                                                des_ast['body'].insert(i, temp_ast)
                                    else:
                                        des_ast['body'].insert(i, temp_ast)
                            else:
                                des_ast['body'].insert(i, temp_ast)
                            i -= 1
                        self.gen_js(des_ast, temp_ast_path, os.path.join(bug_trans_path, js))

    def trans_check(self, trans, from_path, bug):
        res = self.trans_js(trans, from_path, None)
        if trans == 'babel':
            if res.returncode != 0:
                stderr = babel_err(res.stderr.decode('utf-8'))
                if stderr == bug:
                    return 1
        elif trans == 'swc':
            if res.returncode != 0:
                stderr = swc_err(res.stderr.decode('utf-8'))
                if stderr == bug:
                    return 1
        return 0

    def lint_check(self, js, bug):
        cmd = ['npx', 'jshint', '-c', self.jshint_es5_config_path] + [js]
        res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        if res.returncode != 0:
            error_info = jshint_err(res.stdout.decode('utf-8'))
            if error_info == bug:
                return 1
        return 0

    def err_node_check(self, trans, temp_ori_path, temp_trans_path, bug):
        res = self.trans_js(trans, temp_ori_path, temp_trans_path)
        if res.returncode == 0:
            cmd_1 = ['node'] + [temp_ori_path]
            cmd_2 = ['node'] + [temp_trans_path]
            return_code_1, std_out_1 = RunCmd(cmd_1, 3).Run()
            return_code_2, std_out_2 = RunCmd(cmd_2, 3).Run()
            if return_code_1 == 0:
                if return_code_2 != 0:
                    if std_out_2 == bug:
                        return 1
            return 0

    def diff_node_check(self, trans, temp_ori_path, temp_trans_path):
        res = self.trans_js(trans, temp_ori_path, temp_trans_path)
        if res.returncode == 0:
            cmd_1 = ['node'] + [temp_ori_path]
            cmd_2 = ['node'] + [temp_trans_path]
            return_code_1, std_out_1 = RunCmd(cmd_1, 3).Run()
            return_code_2, std_out_2 = RunCmd(cmd_2, 3).Run()
            if return_code_1 == 0 and return_code_2 == 0:
                try:
                    std_out_1 = read_stdout(std_out_1)
                    std_out_2 = read_stdout(std_out_2)
                    if std_out_1 == std_out_2:
                        return 1
                except func_timeout.exceptions.FunctionTimedOut:
                    return 0
        return 0

    def trans_js(self, trans, from_path, to_path):
        if to_path:
            to_path = ['-o', to_path]
        else:
            to_path = []
        if trans == 'babel':
            cmd = ['npx', 'babel'] + \
                  ['--config-file', './' + self.babel_config_path] + \
                  [from_path] + to_path
        elif trans == 'swc':
            cmd = ['npx', 'swc'] + ['-s', 'inline'] + \
                  ['--config-file=' + self.swc_config_path] + \
                  [from_path] + to_path

        res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        return res

    def parse_js(self, ori, des):
        cmd = ['node', 'utils/js/acorn_parse.js'] + [ori] + [des] + ['parse']
        subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        return load_json(des)

    def gen_js(self, ori_ast, ori_path, des_path):
        keep_json(ori_path, ori_ast)
        cmd = ['node', 'utils/js/es_gen.js'] + [ori_path] + [des_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode == 0:
                if "Error" not in res.stdout.decode('utf-8'):
                    return 1
            return 0
        except TimeoutError:
            print('time out error\t' + str(cmd))
            return 0

    def main(self):
        if not os.path.exists(self.bug_home_path):
            os.mkdir(self.bug_home_path)
        self.reduce()


if __name__ == '__main__':
    config_path = sys.argv[1]
    config_dict = load_json(config_path)
    reduce_bug_path = sys.argv[2]
    reduce_testcase_path = sys.argv[3]
    js_reduce = JSReduce(
        reduce_bug_path,
        reduce_testcase_path,
        config_dict['bug_keep_path']
    )
    js_reduce.main()
