import os
import subprocess
import threading
import time
from subprocess import PIPE
from func_timeout import func_set_timeout
from multiprocessing.pool import ThreadPool
from utils import load_json


config_dict = load_json('conf/Ts.json')
job_nums = config_dict['job_nums']

pool = ThreadPool()           # 线程占有率


@func_set_timeout(30)
def read_stdout(std_out):
    try:
        std_out = str(std_out.read(), 'utf-8')  # 由于文件管理会阻塞！需要超时管理
    except:
        std_out = 'decoding error'
    return std_out


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


class CHECK:
    def __init__(self):
        self.ok_seeds_list = []
        self.id = 0

    def serous_check(self, js_path):
        cmd_1 = ['npx', 'jshint', '-c', 'conf/js/jshint-es6.json'] + [js_path]
        cmd_2 = ['/root/.jsvu/v8'] + [js_path]
        # cmd_2 = ['/home/clhiker/.jsvu/v8'] + [js_path]
        try:
            res_1 = subprocess.run(cmd_1, stdout=PIPE, stderr=PIPE, timeout=30)
            return_code_2, _ = RunCmd(cmd_2, 30).Run()
            if res_1.returncode == 0 and return_code_2 == 0:
                self.ok_seeds_list.append((self.id, js_path))
                self.id += 1
                return True
            else:
                return False
        except subprocess.TimeoutExpired:
            return False

    def node_check(self, js_path):
        cmd = ['node'] + [js_path]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode == 0:
                self.ok_seeds_list.append((self.id, js_path))
                self.id += 1
                return True
            else:
                # print(res.stderr)
                return False
        except subprocess.TimeoutExpired:
            return False

    def multi_syntax_check(self, seeds_path):
        self.ok_seeds_list.clear()
        self.id = 0

        seeds_path_list = []
        for name in os.listdir(seeds_path):
            seeds_path_list.append(os.path.join(seeds_path, name))
        # pool.map(self.serous_check, seeds_path_list)
        # time.sleep(3)
        # os.system('pkill -f v8')
        pool.map(self.node_check, seeds_path_list)
        return self.ok_seeds_list
