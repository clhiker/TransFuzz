import os
import subprocess
import tqdm

from subprocess import PIPE
from ts_log import MyLog
from utils.multi_p import pool


my_log = MyLog('ts_log/eval_node.ts_log')


class EvalEs6:
    def __init__(self,
                 new_seeds_path):
        self.new_seeds_path = new_seeds_path
        self.js_path_list = []
        self.md_path_list = []
        self.ok_js_count = 0
        self.es6_list = []
        my_log.print_msg('evaluate ' + self.new_seeds_path, 'INFO')

    def get_path(self):
        for seed in os.listdir(self.new_seeds_path):
            self.js_path_list.append(os.path.abspath(os.path.join(self.new_seeds_path, seed)))

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

    def mutil_verify(self):
        pool.map(self.verify_ok_js_by_node, self.js_path_list)
        # pool = multiprocessing.Pool(processes=20)
        # for _ in tqdm.tqdm(pool.imap(self.verify_ok_js_by_node, self.js_path_list),
        #                    total=len(self.js_path_list)):
        #     pass

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

        cmd_1 = ['npx', 'jshint', '-c', 'conf/js/jshint-es5.json'] + [js_path]
        cmd_2 = ['node'] + [js_path]
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
                            else:
                                # print(res_2.stderr)
                                pass
                        except:
                            print('timeout error\t' + js_path)
                    break
        except:
            print('error\t' + js_path)

    def print_info(self):
        my_log.print_msg('There are seeds: ' + str(len(self.js_path_list)), 'DEBUG')
        my_log.print_msg('There are semantics corrected seeds: ' + str(self.ok_js_count), 'DEBUG')
        my_log.print_msg('rate of succeed is ' + str(self.ok_js_count / len(self.js_path_list)), 'DEBUG')

    def main(self):
        self.get_path()
        self.mutil_verify()
        # self.verify_v8()
        self.print_info()


if __name__ == '__main__':
    # es6_path = '../corpus/lite_es6/node/new_seeds'
    es6_path = '../corpus/es6plus/seeds'
    # es6_path = '../../corpus/CA-result/tmp-10k'
    # es6_path = '../../corpus/COM-result/gen-100k'
    # es6_path = '../../corpus/Mon-result/proc.0-100k'
    evaluate_es6 = EvalEs6(es6_path)
    evaluate_es6.main()