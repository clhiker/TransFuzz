import os
import re
import shutil
import subprocess
import threading
import time
import tqdm
import logging

from subprocess import PIPE

import sys

from utils.multi_p import pool

logging.basicConfig(filename='ts_log/cp_js.ts_log', level=logging.DEBUG)


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
        # self.get_file_list(self.js_home_path, 'md', self.md_path_list)
        # logging.info('there are md ' + str(len(self.md_path_list)))
        # self.extract_js_from_md()
        self.get_file_list(self.js_home_path, 'js', self.js_path_list)
        print('there are js ' + str(len(self.js_path_list)))

    # 从readme 中提取JS
    def extract_js_from_md(self):
        count = 0
        for md in tqdm.tqdm(self.md_path_list):
            try:
                with open(md, 'r') as f:
                    js = f.read()
            except IOError:
                js = ''
            try:
                md_text_list = re.findall(r'```javascript(.*?)```', js, re.S)
                md_text_list += re.findall(r'```js(.*?)```', js, re.S)
                md_text_list += re.findall(r'```JavaScript(.*?)```', js, re.S)
            except:
                md_text_list = []
            for i in range(len(md_text_list)):
                try:
                    js_text = md_text_list[i]
                    # js_path = md[:md.rfind('.')] + '_' + str(i) + '.js' 直接提取到当地
                    js_path = self.md_path + str(count) + '.js'
                    with open(js_path, 'w') as jf:
                        jf.write(js_text)
                    count += 1
                except:
                    pass

    # 将JS文件移动到指定文件夹
    def multi_cp_js(self):
        begin_time = time.time()
        pool.map(self.cp_es6plus_js, self.js_path_list)
        print('find es6 use：' + str(time.time() - begin_time) + 's')

    # 两遍筛查后复制 es6+
    def cp_es6plus_js(self, js_path):
        cmd_1 = ['npx', 'jshint', '-c', 'conf/js/jshint-es5.json'] + [js_path]
        cmd_2 = ['npx', 'jshint', '-c', 'conf/js/jshint-es6.json'] + [js_path]
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

    # 筛查es6 代码
    def cp_es6_js(self, js_path):
        cmd_1 = ['npx', 'jshint', '-c', os.path.abspath('config/jshint-es5.json')] + [js_path]
        try:
            res_1 = subprocess.run(cmd_1, stdout=PIPE, stderr=PIPE, timeout=10)
            if "use 'esversion: 6'" in res_1.stdout.decode('utf-8'):
                self.es6_list.append(js_path)
        except:
            print('error\t' + js_path)

    # 法2：用v8 提取正确语法代码
    def cp_by_v8(self):
        print('v8 check and cp')
        for js in tqdm.tqdm(self.js_path_list):
            cmd = ['/root/.jsvu/v8', js]
            return_code, std_out = RunCmd(cmd, 3).Run()
            if return_code == 0:
                new_path = os.path.join(self.ok_js_path, str(self.ok_js_count) + '.js')
                self.ok_js_count += 1
                try:
                    shutil.copy(js, new_path)
                except:
                    print('copy error ' + js)

    def cp_jsx(self):
        for jsx in tqdm.tqdm(self.js_path_list):
            new_path = os.path.join(self.ok_js_path, str(self.ok_js_count) + '.jsx')
            try:
                shutil.copy(jsx, new_path)
                self.ok_js_count += 1
            except:
                print('copy error ' + jsx)

    def get_file_list(self, path, file_type, path_list):
        for item in os.listdir(path):
            file = os.path.join(path, item)
            if os.path.isdir(file):
                self.get_file_list(file, file_type, path_list)
            else:
                if file[file.rfind('.') + 1:] == file_type:
                    path_list.append(file)

    def multi_check_jsx(self):
        begin_time = time.time()
        pool.map(self.check_jsx, os.listdir(self.ok_js_path))
        print('check jsx use：' + str(time.time() - begin_time) + 's')
        print(self.ok_js_count)
        print(len(self.ok_js_path))

    def single_check_jsx(self):
        count = 0
        for jsx in tqdm.tqdm(os.listdir(self.ok_js_path)):
            path = os.path.join(self.ok_js_path, jsx)
            cmd = ['npx', 'eslint', '-c', '.eslintrc.js', path]
            try:
                res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
                if res.returncode == 0:
                    count += 1
                else:
                    print(res.stderr.decode('utf-8'))
                    print(res.stdout.decode('utf-8'))
            except:
                print('error\t' + path)
        print(count)

    def check_jsx(self, jsx):
        path = os.path.join(self.ok_js_path, jsx)
        cmd = ['npx', 'eslint', '-c', '.eslintrc.js', path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode == 0:
                self.ok_js_count += 1
                try:
                    shutil.copy(path, '/D/Corpus/jsx-cor-total/'+jsx)
                except:
                    print('copy error' + jsx)
        except:
            print('error\t' + path)

    def print_info(self):
        logging.info(len(self.js_path_list))
        logging.info(self.ok_js_count)
        print(len(self.js_path_list))
        print(self.ok_js_count)

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
        # self.print_info()


if __name__ == '__main__':
    # cp_es6 = CpEs6('../../corpus/es6plus/ori',
    #                '../../corpus/es6plus/v8-checked')
    # cp_es6 = CpEs6('/D/Corpus/jsx-topic',
    #                '/D/Corpus/jsx-topic-total', '')
    # cp_es6 = CpEs6('../../corpus/lite_es6/ori_lit_es6',
    #                '../../corpus/lite_es6/seeds')
    cp_es6 = CpEs6('../../corpus/es6pjs',
                   '../../corpus/jsh-checked')
    cp_es6.main()