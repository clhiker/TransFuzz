import subprocess
from subprocess import PIPE
from utils.err_info import jshint_err
from utils.multi_p import pool


class Lint_FUZZ:
    def __init__(self,
                 bug_dict,
                 bug_name_set,
                 invalid_bugs
                 ):
        self.bug_dict = bug_dict
        self.bug_name_set = bug_name_set
        self.invalid_bugs = invalid_bugs
        self.jshint_es5_config_path = 'conf/js/jshint-es5.json'

    def check_by_lint(self, paras):
        js_path, trans = paras
        cmd = ['npx', 'jshint', '-c', self.jshint_es5_config_path] + [js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode != 0:
                error_info = jshint_err(res.stdout.decode('utf-8'))
                if error_info:
                    js = js_path[js_path.rfind('/') + 1:]

                    for invalid in self.invalid_bugs[trans]['syntax']:
                        if invalid in error_info:
                            return False
                    if error_info not in self.bug_dict[trans]['syntax']:
                        self.bug_dict[trans]['syntax'][error_info] = [js]
                    else:
                        self.bug_dict[trans]['syntax'][error_info].append(js)

                    self.bug_name_set.add(js)

        except subprocess.TimeoutExpired:
            print('timeout error lint\t' + js_path)

    def multi_lint(self, babel_path_list, swc_path_list):

        babel_paras = [(babel_path[1], 'babel') for babel_path in babel_path_list if babel_path[1]]
        pool.map(self.check_by_lint, babel_paras)

        swc_paras = [(swc_path[1], 'swc') for swc_path in swc_path_list if swc_path[1]]
        pool.map(self.check_by_lint, swc_paras)

    def run(self, babel_path_list, swc_path_list):
        self.multi_lint(babel_path_list, swc_path_list)