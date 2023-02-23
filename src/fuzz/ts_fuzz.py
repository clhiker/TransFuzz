import os
import shutil
import time

from utils.multi_p import CHECK
from fuzz.trans_fuzz import Trans_FUZZ
from fuzz.lint_fuzz import Lint_FUZZ
from fuzz.diff_fuzz import Diff_FUZZ
from utils import keep_json, load_json

check = CHECK()


class TS_FUZZ:
    def __init__(self,
                 my_log,
                 seeds_path,
                 to_path,
                 bug_dict_path,
                 bug_keep_path,
                 invalid_bug_path):
        self.my_log = my_log
        self.bug_dict = {
            'babel': {
                'ori': {},
                'syntax': {},
                'semantics': {}
            }, 'swc': {
                'ori': {},
                'syntax': {},
                'semantics': {}
            }
        }
        self.bug_name_set = set()
        self.seeds_path = seeds_path
        self.to_path = to_path
        self.bug_dict_path = bug_dict_path
        self.bug_keep_path = bug_keep_path
        self.invalid_bugs = load_json(invalid_bug_path)

        self.trans_fuzz = Trans_FUZZ(
            self.to_path,
            self.bug_dict,
            self.bug_name_set,
            self.invalid_bugs
        )
        self.lint_fuzz = Lint_FUZZ(
            self.bug_dict,
            self.bug_name_set,
            self.invalid_bugs
        )
        self.diff_fuzz = Diff_FUZZ(
            self.bug_dict,
            self.bug_name_set,
            self.invalid_bugs
        )
        # 实验数据
        self.seed_nums = 0
        self.ok_seed_nums = 0
        self.init_dir()

    def init_dir(self):
        self.my_log.print_msg('清空bug池', 'INFO')
        if os.path.exists(self.bug_keep_path):
            shutil.rmtree(self.bug_keep_path)
            os.mkdir(self.bug_keep_path)
    
    def keep_bug_dict(self):
        keep_json(self.bug_dict_path, self.bug_dict)
    
    def keep_bug(self):
        if not os.path.exists(self.bug_keep_path):
            os.mkdir(self.bug_keep_path)
        for js in self.bug_name_set:
            js_path = os.path.join(self.seeds_path, js)
            bug_path = os.path.join(self.bug_keep_path, js)
            try:
                shutil.copy(js_path, bug_path)
            except FileNotFoundError:
                pass
        self.bug_name_set.clear()
    
    def clear_trans_file(self):
        babel_home_path = os.path.join(self.to_path, 'babel')
        swc_home_path = os.path.join(self.to_path, 'swc')
        if os.path.exists(babel_home_path):
            shutil.rmtree(babel_home_path)
            os.mkdir(babel_home_path)
        if os.path.exists(swc_home_path):
            shutil.rmtree(swc_home_path)
            os.mkdir(swc_home_path)
        if os.path.exists(self.seeds_path):
            shutil.rmtree(self.seeds_path)
            os.mkdir(self.seeds_path)
        time.sleep(1)

    def fuzz(self, turn):
        self.my_log.print_msg('选择第' + str(turn) + '批数据进行测试', 'INFO')
                
        if os.path.exists(self.seeds_path):
            self.seed_nums += len(os.listdir(self.seeds_path))
            self.my_log.print_msg('开始筛选出语法语义正确的程序', 'INFO')
            ok_seeds_list = check.multi_syntax_check(self.seeds_path)
            self.ok_seed_nums += len(ok_seeds_list)
            self.my_log.print_msg('有' + str(len(ok_seeds_list)) + '个种子通过了检查', 'DEBUG')

            self.my_log.print_msg('开始检查转译过程中的错误', 'INFO')
            babel_path_list, swc_path_list = self.trans_fuzz.run(ok_seeds_list)

            self.my_log.print_msg('开始检查转译结果中的语法错误', 'INFO')
            self.lint_fuzz.run(babel_path_list, swc_path_list)

            self.my_log.print_msg('开始检查转译结果中的语义错误', 'INFO')
            self.diff_fuzz.run(ok_seeds_list, babel_path_list, swc_path_list)

            self.my_log.print_msg('当前测试过的种子数量为' + str(self.ok_seed_nums), 'DEBUG')
            self.my_log.print_msg('当前的累计正确率为' + str(self.ok_seed_nums / self.seed_nums), 'DEBUG')
            self.my_log.print_msg('目前发现了bug情况为: ', 'INFO')
            self.my_log.print_msg(
                'babel: ori: ' + str(len(self.bug_dict['babel']['ori'])) + '\n' +
                'babel: syntax: ' + str(len(self.bug_dict['babel']['syntax'])) + '\n' +
                'babel: semantics: ' + str(len(self.bug_dict['babel']['semantics'])) + '\n' +
                'swc: ori: ' + str(len(self.bug_dict['swc']['ori'])) + '\n' +
                'swc: syntax: ' + str(len(self.bug_dict['swc']['syntax'])) + '\n' +
                'swc: semantics: ' + str(len(self.bug_dict['swc']['semantics'])),
                'DEBUG'
            )
            self.my_log.print_msg('更新bug 报告', 'INFO')
            self.keep_bug_dict()
            self.keep_bug()

            self.clear_trans_file()


if __name__ == '__main__':
    from ts_log import MyLog
    fuzz_log = MyLog('ts_log/fuzz.log')
    seeds_path = '../corpus/es6plus/new_seeds'
    to_path = '../corpus/es6plus/to_path'
    bug_dict_path = 'bug/bug.json'
    bug_keep_path = '../corpus/es6plus/bug'
    ts_fuzz = TS_FUZZ(
        fuzz_log,
        seeds_path,
        to_path,
        bug_dict_path,
        bug_keep_path
    )
    ts_fuzz.fuzz(1)