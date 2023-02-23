import subprocess
import os
import time
from subprocess import PIPE
from utils.err_info import babel_err, swc_err
from utils.multi_p import pool


class Trans_FUZZ:
    def __init__(self,
                 to_path,
                 bug_dict,
                 bug_name_set,
                 invalid_bugs
                 ):
        self.to_path = to_path
        self.bug_dict = bug_dict
        self.bug_name_set = bug_name_set
        self.invalid_bugs = invalid_bugs

        self.babel_config_path = 'conf/js/babel-es6.json'
        self.swc_config_path = os.path.abspath('conf/js/swc-es6.json')
        if not os.path.exists(self.to_path):
            os.mkdir(self.to_path)
        self.babel_trans_path = os.path.join(self.to_path, 'babel')
        self.swc_trans_path = os.path.join(self.to_path, 'swc')

        self.babel_seeds_list = []
        self.swc_seeds_list = []

    def multi_trans(self, ok_seeds_list):
        pool.map(self.single_trans, ok_seeds_list)

        # 配置转译器
    def single_trans(self, id_path):
        id, test_path = id_path
        from_path = test_path
        name = test_path[test_path.rfind('/') + 1:]

        babel_to_path = os.path.join(self.babel_trans_path, name)
        cmd = ['npx', 'babel'] + \
              ['--config-file', './' + self.babel_config_path] + \
              [from_path] + ['-o', babel_to_path]
        if self.transpiler_js(cmd, 'babel'):
            self.babel_seeds_list.append((id, babel_to_path))
            while not os.path.exists(babel_to_path):      # 代码陷阱，在性能问题下对并发的补充
                self.transpiler_js(cmd, 'babel')
                time.sleep(1)
        else:
            self.babel_seeds_list.append((id, None))

        swc_to_path = os.path.join(self.swc_trans_path, name)
        cmd = ['npx', 'swc'] + ['-s', 'inline'] + \
              ['--config-file=' + self.swc_config_path] + \
              [os.path.abspath(from_path)] + ['-o', os.path.abspath(swc_to_path)]

        if self.transpiler_js(cmd, 'swc'):
            self.swc_seeds_list.append((id, swc_to_path))
            while not os.path.exists(swc_to_path):      # 代码陷阱，在性能问题下对并发的补充
                self.transpiler_js(cmd, 'swc')
                time.sleep(1)
        else:
            self.swc_seeds_list.append((id, None))

    def transpiler_js(self, cmd, trans):
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=30)
            if res.returncode != 0:
                js_name = cmd[-3][cmd[-3].rfind('/') + 1:]
                # bug1:转译器报错
                if trans == 'babel':
                    stderr = babel_err(res.stderr.decode('utf-8'))
                elif trans == 'swc':
                    stderr = swc_err(res.stderr.decode('utf-8'))

                for invalid in self.invalid_bugs[trans]['ori']:
                    if stderr and invalid in stderr:
                        return False
                if stderr not in self.bug_dict[trans]['ori']:
                    self.bug_dict[trans]['ori'][stderr] = [js_name]
                else:
                    self.bug_dict[trans]['ori'][stderr].append(js_name)
                self.bug_name_set.add(js_name)
                return False
            else:
                return True

        except subprocess.TimeoutExpired:
            js_name = cmd[-3][cmd[-3].rfind('/') + 1:]
            if 'timeout' not in self.bug_dict[trans]['ori']:
                self.bug_dict[trans]['ori']['timeout'] = [js_name]
            else:
                self.bug_dict[trans]['ori']['timeout'].append(js_name)

            print('time out transpiler' + js_name)
            self.bug_name_set.add(js_name)
            return False

    def run(self, ok_seeds_list):
        self.babel_seeds_list.clear()
        self.swc_seeds_list.clear()
        self.multi_trans(ok_seeds_list)
        return self.babel_seeds_list, self.swc_seeds_list
