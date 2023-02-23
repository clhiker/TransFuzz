import json
import os
import shutil
import subprocess
import tqdm
import time
import sys
import gc
from subprocess import PIPE

from ts_log import MyLog
from utils import load_json
from estree.ES_DICT import RESERVED_WORD
from utils.multi_p import pool

sys.setrecursionlimit(3000)  # 默认的递归深度只有 1000，我们增加递归深度到 3000

my_log = MyLog("ts_log/process.log")


class GrammarPreprocess:
    def __init__(self,
                 seeds_path,
                 seeds_ast_path,
                 dataset_path
                 ):
        self.seeds_path = os.path.abspath(seeds_path)
        self.seeds_ast_path = os.path.abspath(seeds_ast_path)
        self.dataset_path = os.path.abspath(dataset_path)
        self.simplified_ast_json_path = os.path.join(dataset_path, 'node-simple-ast.json')
        self.terminal_path = os.path.join(dataset_path, 'node-terminal.json')
        self.ori_sim_ast_json = os.path.join(dataset_path, 'ori-sim-ast.json')
        self.simplified_ast_dict = {}
        self.seeds_list = []
        self.seeds_ast_list = []
        self.simplified_ast_set = set()
        self.terminal_dict = {}
        self.ori_sim_ast = {}

    def clear(self):
        self.seeds_list.clear()
        self.seeds_ast_list.clear()
        self.simplified_ast_dict.clear()
        self.terminal_dict.clear()
        self.ori_sim_ast.clear()
        # if os.path.exists(self.seeds_ast_path):
        #     shutil.rmtree(self.seeds_ast_path)
        gc.collect()

    def parse_ast_path(self):
        self.get_seeds()
        my_log.print_msg('共载入' + str(len(self.seeds_list)) + ' 种子', 'DEBUG')
        self.get_ast_path_list()
        my_log.print_msg('开始转换成语法树', 'INFO')
        self.multi_ast_frag()

    def get_seeds(self, ):
        for item in os.listdir(self.seeds_path):
            file = os.path.join(self.seeds_path, item)
            self.seeds_list.append(file)

    # 提前获得ast 路径列表
    def get_ast_path_list(self):
        for file in self.seeds_list:
            name = file[file.rfind('/') + 1: file.rfind('.')]
            self.seeds_ast_list.append(
                os.path.join(self.seeds_ast_path, name + '.json')
            )

    def multi_ast_frag(self):
        if os.path.exists(self.seeds_ast_path):
            shutil.rmtree(self.seeds_ast_path)
        os.mkdir(self.seeds_ast_path)

        begin_time = time.time()
        pool.map(self.get_ast_frag, zip(self.seeds_list, self.seeds_ast_list))
        my_log.print_msg('parse ast run：' + str(time.time() - begin_time) + 's', 'DEBUG')

    def get_ast_frag(self, paras):
        cmd = ['node', 'utils/js/acorn_parse.js'] + [paras[0]] + [paras[1]] + ['parse']
        # res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode != 0:
                print(res.stdout)
                print(res.stderr)
        except subprocess.TimeoutExpired:
            print('error\t' + str(cmd))

    def keep_simplified_path(self):
        if not os.path.exists(self.dataset_path):
            os.mkdir(self.dataset_path)

        begin_time = time.time()
        count = 0
        for ast in tqdm.tqdm(os.listdir(self.seeds_ast_path)):
            self.keep_path(ast, count)
            count += 1

        my_log.print_msg('keep path run：' + str(time.time() - begin_time) + 's', 'DEBUG')
        my_log.print_msg('一共保存了 ' + str(len(self.simplified_ast_set)) + '个AST片段', 'DEBUG')
        i = 0
        for sim_ast in self.simplified_ast_set:
            self.simplified_ast_dict[i] = sim_ast
            i += 1
        self.simplified_ast_set.clear()

        my_log.print_msg('如果你的数据集比较大，这将会花费几分钟', 'INFO')
        with open(self.simplified_ast_json_path, 'w') as jf:
            jf.write(json.dumps(self.simplified_ast_dict, indent=1))
        with open(self.ori_sim_ast_json, 'w') as jf:
            jf.write(json.dumps(self.ori_sim_ast, indent=1))

    def keep_path(self, ast, count):
        path = os.path.join(self.seeds_ast_path, ast)
        ast_json = load_json(path)
        self.simple_ast(ast_json)

        # 原始种子简化头
        self.ori_sim_ast[count] = ast_json

        for body in ast_json['body']:
            self.simplified_ast_set.add(json.dumps(body))
            self.keep_path_rec(body)

    def keep_path_rec(self, body):
        for key in body.keys():
            if isinstance(body[key], list):
                for it in body[key]:
                    if it is not None:
                        if 'type' in it.keys():
                            self.simplified_ast_set.add(json.dumps(it))
                        self.keep_path_rec(it)
            elif isinstance(body[key], dict):
                if 'type' in body[key].keys():
                    self.simplified_ast_set.add(json.dumps(body[key]))
                    self.keep_path_rec(body[key])
            else:
                pass

    # 简化：删掉所有终结符的数据，但是保留终结符的标志
    # 保留下非终结符
    def simple_ast(self, node):
        temp_node = node.copy()
        for key in temp_node:
            if isinstance(node[key], list):
                if len(node[key]) > 0:
                    for it in node[key]:
                        if it is not None:
                            self.simple_ast(it)
                else:
                    pass
            elif isinstance(node[key], dict):
                self.simple_ast(node[key])
            elif key == 'type':
                pass
            # elif key in {'body', 'params', 'expressions', 'element', 'arguments', 'properties', 'elements'}:
            #     pass
            else:
                node[key] = None

    def single_keep_terminal(self):
        begin_time = time.time()
        for ast in tqdm.tqdm(os.listdir(self.seeds_ast_path)):
            self.keep_terminal(ast)
        my_log.print_msg('keep path run：' + str(time.time() - begin_time) + 's', 'DEBUG')
        for key in self.terminal_dict.keys():
            for it in self.terminal_dict[key]:
                self.terminal_dict[key][it] = list(self.terminal_dict[key][it])
        with open(self.terminal_path, 'w') as jf:
            jf.write(json.dumps(self.terminal_dict, indent=1))

    def keep_terminal(self, ast):
        path = os.path.join(self.seeds_ast_path, ast)
        ast_json = load_json(path)
        for body in ast_json['body']:
            self.loc_ast(body)

    # 保存格式进行修改，{terminal：{type1:set(), type2:set()}}
    def loc_ast(self, node):
        terminal_key = ''
        for key in node.keys():
            if key == 'type':
                terminal_key = node[key]
        for key in node.keys():
            if isinstance(node[key], list):
                for it in node[key]:
                    if it is not None:
                        self.loc_ast(it)

            elif isinstance(node[key], dict):
                self.loc_ast(node[key])
            else:
                if key not in {'sourceType', 'type'}:
                    # 'body', 'params', 'expressions', 'element', 'arguments', 'properties', 'elements'}:        # 列表
                    if terminal_key in ['Identifier', 'Literal']:
                        if node[key] not in RESERVED_WORD:  # 标识符不应该包含保留字
                            self.add_terminal_dict(key, terminal_key, node)
                    else:
                        self.add_terminal_dict(key, terminal_key, node)

    def add_terminal_dict(self, key, terminal_key, node):
        if node[key] == 'undefined':
            print(terminal_key)
        if key not in self.terminal_dict:
            self.terminal_dict[key] = {}
            self.terminal_dict[key][terminal_key] = {node[key]}
        else:
            if terminal_key not in self.terminal_dict[key].keys():
                self.terminal_dict[key][terminal_key] = {node[key]}
            else:
                self.terminal_dict[key][terminal_key].add(node[key])

    def print_info(self):
        print(self.terminal_dict)

    def main(self):
        my_log.print_msg('------------------将代码解析为AST-------------------\n', 'INFO')
        self.parse_ast_path()
        my_log.print_msg('------------------保存简化后的非终结符子树------------\n', 'INFO')
        self.keep_simplified_path()
        my_log.print_msg('------------------保存终结符叶子节点-----------------\n', 'INFO')
        self.single_keep_terminal()
        my_log.print_msg('------------------清理内存空间(如果需要连续运行）------\n', 'INFO')
        self.clear()


if __name__ == '__main__':
    # 完整数据集
    grammar_pre = GrammarPreprocess(
        '../corpus/es6lit/seeds',
        '../corpus/es6lit/ast',
        '../corpus/es6lit/dataset',
    )
    grammar_pre.main()
