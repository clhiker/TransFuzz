import os
import subprocess
import threading
import time
from subprocess import PIPE
import tqdm

from utils.multi_p import pool


class RunCmd(threading.Thread):
    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        self.p = subprocess.Popen(self.cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        self.p.wait()

    def Run(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()  # use self.p.kill() if process needs a kill -9
            self.p.kill()
            self.join()
            return self.p.returncode, self.p.stdout
        return self.p.returncode, self.p.stdout


class EvalEs6:
    def __init__(self,
                 new_seeds_path):
        self.new_seeds_path = new_seeds_path
        self.js_path_list = []
        self.md_path_list = []
        self.ok_js_count = 0
        self.es6_list = []

    # 得到JS 的文件列表
    def get_path(self):
        for seed in os.listdir(self.new_seeds_path):
            self.js_path_list.append(os.path.abspath(os.path.join(self.new_seeds_path, seed)))

    # 两遍筛查后评估 es6+
    def eval_es6(self):
        for js_path in tqdm.tqdm(self.js_path_list):
            cmd_1 = ['jshint', '-c', os.path.abspath('conf/js/jshint-es5.json')] + [js_path]
            cmd_2 = ['jshint', '-c', os.path.abspath('conf/js/jshint-es6.json')] + [js_path]
            es6_attention = ["use 'esversion: 6'", "use 'esversion: 7'",
                             "use 'esversion: 8'", "use 'esversion: 9'", "use 'esversion: 10'"]
            try:
                res_1 = subprocess.run(cmd_1, stdout=PIPE, stderr=PIPE, timeout=10)
                if res_1.returncode != 0:
                    for attention in es6_attention:
                        if attention in res_1.stdout.decode('utf-8'):
                            try:
                                res_2 = subprocess.run(cmd_2, stdout=PIPE, stderr=PIPE, timeout=10)
                                if res_2.returncode == 0:
                                    self.ok_js_count += 1
                            except:
                                print('error\t' + js_path)
                        break
            except:
                print('error\t' + js_path)

    # 验证代码 by jshint
    def mutil_verify(self):
        begin_time = time.time()
        pool.map(self.verify_ok_js_by_node, self.js_path_list)
        print('verify by node run：' + str(time.time() - begin_time) + 's')

    def verify_ok_by_eslint(self, js_path):
        cmd = ['npx', 'eslint', '-c', 'conf/js/.eslintrc.js', js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode == 0:
                self.ok_js_count += 1
            else:
                # print(res.stdout.decode('utf-8'))
                pass
        except subprocess.TimeoutExpired:
            print('error\t' + js_path)

    def verify_v8(self):
        for js_path in tqdm.tqdm(self.js_path_list):
            self.verify_ok_js_by_v8(js_path)

    def verify_ok_js_by_jshint(self, js_path):
        cmd = ['npx', 'jshint', '-c', 'conf/js/jshint-es6.json'] + [js_path]
        res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        try:
            if res.returncode != 0:
                print(res.stdout)
            else:
                self.ok_js_count += 1
        except:
            print('error\t' + str(cmd))

    # 验证代码 by babel
    def verify_ok_js_by_babel(self, js_path):
        cmd = ['npx', 'babel'] + [js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode != 0:
                print(res.stdout)
                print(res.stderr)
            else:
                self.ok_js_count += 1
        except:
            print('error\t' + str(cmd))

    def verify_ok_js_by_v8(self, js_path):
        cmd = ['/home/clhiker/.jsvu/v8'] + [js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode == 0:
                self.ok_js_count += 1
        except:
            print('error\t' + str(cmd))

    def verify_ok_js_by_node(self, js_path):
        cmd = ['node'] + [js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=3)
            if res.returncode == 0:
                self.ok_js_count += 1
            else:
                print(res.stderr)
                pass
        except subprocess.TimeoutExpired:
            print('error\t' + str(cmd))

    def print_info(self):
        print(len(self.js_path_list))
        print(self.ok_js_count)
        print(self.ok_js_count / len(self.js_path_list))

    def main(self):
        self.get_path()
        self.mutil_verify()
        # self.verify_v8()
        self.print_info()


if __name__ == '__main__':
    es6_path = '../corpus/es6plus/new_seeds'
    # es6_path = '../corpus/lite_es6/node/new_seeds'
    # es6_path = '../../corpus/gpt2/gen-js'
    # es6_path = '/home/clhiker/CodeAlchemist/result/tmp'
    evaluate_es6 = EvalEs6(es6_path)
    evaluate_es6.main()


'''
gpt-2
verify by jshint run：217.91649055480957s
14122
11807
0.8360713779917859

verify by babel run：277.4115455150604s
14122
11399
0.8071802860784592

14122
2006
0.1420478685738564

verify by node run：38.9480082988739s
8904
504
0.05660377358490566
'''