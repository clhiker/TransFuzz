import os
import shutil
import subprocess
import time
from subprocess import PIPE
import tqdm
import sys

from utils.multi_p import pool



class CpEs6:
    def __init__(self,
                 js_home_path,
                 ok_js_path):
        self.js_home_path = js_home_path
        self.md_path = os.path.join(self.js_home_path, 'md_path')
        self.js_path_list = []
        self.md_path_list = []
        self.ok_js_count = 0
        self.ok_js_path = ok_js_path
        self.es6_list = []

    # 得到JS 的文件列表
    def get_path(self):
        self.get_file_list(self.js_home_path, 'js', self.js_path_list)
        print('there are js ' + str(len(self.js_path_list)))

    # 将JS文件移动到指定文件夹
    def multi_cp_js(self):
        if os.path.exists(self.ok_js_path):
            shutil.rmtree(self.ok_js_path)
        os.mkdir(self.ok_js_path)

        begin_time = time.time()
        pool.map(self.cp_es6plus_js, self.js_path_list)
        print('find es6 use：' + str(time.time() - begin_time) + 's')

    # 两遍筛查后复制 es6+
    def cp_es6plus_js(self, js_path):
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
                                new_path = os.path.join(self.ok_js_path, str(self.ok_js_count) + '.js')
                                self.ok_js_count += 1
                                try:
                                    shutil.copy(js_path, new_path)
                                except:
                                    print('copy error ' + js_path)
                        except:
                            print('error\t' + js_path)
                    break
        except:
            print('error\t' + js_path)

    def get_file_list(self, path, file_type, path_list):
        for item in os.listdir(path):
            file = os.path.join(path, item)
            if os.path.isdir(file):
                self.get_file_list(file, file_type, path_list)
            else:
                if file[file.rfind('.') + 1:] == file_type:
                    path_list.append(file)

    def print_info(self):
        print('there js ori are ' + str(len(self.js_path_list)))
        print('there checked js are ' + str(self.ok_js_count))

    # 验证代码 by jshint
    def verify_ok_js_by_jshint(self):
        count = 0
        for item in tqdm.tqdm(os.listdir(self.ok_js_path)):
            js_path = os.path.join(self.ok_js_path, item)
            cmd = ['npx', 'jshint', '-c', 'conf/js/jshint-es6.json'] + [js_path]
            try:
                res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
                if res.returncode != 0:
                    print(res.stderr)
                else:
                    count += 1
            except:
                print('error\t')
                print(cmd)
        print(count)
        print(len(os.listdir(self.ok_js_path)))

    # 验证代码 by babel
    def verify_ok_js_by_babel(self):
        count = 0
        for item in tqdm.tqdm(os.listdir(self.ok_js_path)):
            js_path = os.path.join(self.ok_js_path, item)
            cmd = ['babel'] + [js_path]
            try:
                res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
                if res.returncode != 0:
                    print(res.stdout)
                    print(res.stderr)
                else:
                    count += 1
            except:
                print('error\t')
                print(cmd)
        print(count)
        print(len(os.listdir(self.ok_js_path)))

    def main(self):
        self.get_path()
        self.multi_cp_js()
        # self.cp_by_v8()
        self.print_info()
        # self.verify_ok_js_by_jshint()


if __name__ == '__main__':
    cp_es6 = CpEs6('../../corpus/es6pjs',
                   '../../corpus/node-checked')
    # cp_es6 = CpEs6('/home/clhiker/corpus/COM-result/gen-10k',
    #                '/home/clhiker/corpus/COM-result/10k-result/node-checked')
    # cp_es6 = CpEs6('/home/clhiker/corpus/Mon-result/proc.0-100k',
    #                '/home/clhiker/corpus/Mon-result/100k-result/node-checked')
    cp_es6.main()