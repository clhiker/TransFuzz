import json
import os
import shutil
import subprocess
import tqdm
import time
import sys
import gc
from subprocess import PIPE
from estree.ES_DICT import RESERVED_WORD

from ts_log import MyLog
from utils import load_json
from estree.ES_DICT import ES6P_TYPE
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
        self.es6p_sub_path = os.path.join(dataset_path, 'es6p-sub.json')
        self.terminal_path = os.path.join(dataset_path, 'node-terminal.json')
        self.seeds_list = []
        self.seeds_ast_list = []
        self.es6p_sub_set = set()
        self.es6p_sub_dict = dict()
        self.decl_set = {
            'FunctionDeclaration',
            'VariableDeclaration',
            'ClassDeclaration',
            'AssignmentExpression',
        }
        self.terminal_dict = {}

    def clear_ram(self):
        self.seeds_list.clear()
        self.seeds_ast_list.clear()
        self.es6p_sub_set.clear()
        self.terminal_dict.clear()
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

    # 保存子树的主函数
    def keep_es6p_subtrees(self):
        if not os.path.exists(self.dataset_path):
            os.mkdir(self.dataset_path)

        for ast_name in tqdm.tqdm(os.listdir(self.seeds_ast_path)):
            self.keep_path(ast_name)
        my_log.print_msg('一共保存了 ' + str(len(self.es6p_sub_set)) + '个AST片段', 'DEBUG')

        i = 0
        for sub_ast in self.es6p_sub_set:
            self.es6p_sub_dict[i] = sub_ast
            i += 1

        my_log.print_msg('将es6plus 的AST子树保存到本地', 'INFO')
        with open(self.es6p_sub_path, 'w') as jf:
            jf.write(json.dumps(self.es6p_sub_dict, indent=1))

    # 保存子树的钩子
    def keep_path(self, ast_name):
        ast_path = os.path.join(self.seeds_ast_path, ast_name)
        ast_dict = load_json(ast_path)
        all_decl = self.collect_var_info(ast_dict)
        self.keep_path_rec('', ast_dict, all_decl)

    # 保存子树的递归
    def keep_path_rec(self, key, node, all_decl):
        if node:
            if 'type' in node.keys() and node['type'] in ES6P_TYPE:
                front_decl = self.find_front_decl(all_decl, node)  # 约束声明
                new_front = []
                for decl in front_decl:  # 删除和子树重复的声明
                    if decl not in str(node):
                        new_front.append(eval(decl))

                new_front.append(node)  # 选择的子树
                new_front.append(key)
                self.es6p_sub_set.add(str(new_front))

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.keep_path_rec(key, node[key], all_decl)
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.keep_path_rec(key, item, all_decl)

    # 子树约束的钩子
    def find_front_decl(self, all_decl, subtree):
        front_decl = set()
        self.rec_find_front(all_decl, subtree, front_decl)
        unique_decl = front_decl.copy()
        front_decl = list(front_decl)
        for front in front_decl:
            temp_decl = set()
            self.rec_find_front(all_decl, eval(front), temp_decl)
            for temp in temp_decl:
                if temp not in unique_decl:
                    unique_decl.add(temp)
                    front_decl.append(temp)

        return list(unique_decl)

    # 子树约束的递归
    def rec_find_front(self, all_decl, subtree, front_decl):
        if subtree:
            if 'type' in subtree.keys() and isinstance(subtree['type'], str):
                if subtree['type'] not in self.decl_set:
                    id_name = self.find_ident(subtree)
                    try:
                        front_decl.add(str(all_decl[id_name]))
                    except KeyError:
                        pass

            for key in subtree.keys():
                if isinstance(subtree[key], dict):
                    self.rec_find_front(all_decl, subtree[key], front_decl)
                elif isinstance(subtree[key], list):
                    for item in subtree[key]:
                        self.rec_find_front(all_decl, item, front_decl)

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

    def collect_var_info(self, node):
        all_decl = {}
        self.find_all_decl(all_decl, node)
        # print(all_decl)
        return all_decl

    def find_all_decl(self, all_decl, node):
        if node:
            if isinstance(node, dict):
                if 'type' in node.keys():
                    if node['type'] == 'FunctionDeclaration' or \
                            node['type'] == 'FunctionExpression' or \
                            node['type'] == 'ArrowFunctionExpression':
                        params = node['params']
                        for para in params:
                            if para['type'] == 'Identifier':
                                name = self.find_ident(para)
                                all_decl[name] = self.add_var(name)

                            elif para['type'] == 'RestElement':
                                name = self.find_ident(para)
                                all_decl[name] = self.add_arr(name)

                            elif para['type'] == 'AssignmentPattern':
                                left_name = self.find_ident(para['left'])
                                right_lit = self.find_Literal(para['right'])
                                if left_name and right_lit:
                                    all_decl[left_name] = self.add_ass_pat(left_name, right_lit)

                    if node['type'] in self.decl_set:
                        if node['type'] == 'AssignmentExpression':
                            if node['operator'] == '=':
                                if 'name' in node['left']:
                                    all_decl[node['left']['name']] = node
                        else:
                            if node['type'] == 'VariableDeclaration':
                                var_dec = node['declarations']
                                for var in var_dec:
                                    id_node = var['id']
                                    if id_node['type'] == 'Identifier':
                                        all_decl[id_node['name']] = node
                                    elif id_node['type'] == 'ArrayPattern':
                                        for item in id_node['elements']:
                                            name = self.find_ident(item)
                                            if name:
                                                all_decl[name] = node
                            else:
                                id_node = node['id']
                                if id_node['type'] == 'Identifier':
                                    all_decl[id_node['name']] = node
                                elif id_node['type'] == 'ArrayPattern':
                                    for item in id_node['elements']:
                                        name = self.find_ident(item)
                                        if name:
                                            all_decl[name] = node

                for key in node.keys():
                    self.find_all_decl(all_decl, node[key])
            elif isinstance(node, list):
                for item in node:
                    self.find_all_decl(all_decl, item)

    # 找到所有的 identifier
    def find_ident(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'Identifier':
                return node['name']
            for key in node.keys():
                if isinstance(node[key], list):
                    for item in node[key]:
                        res = self.find_ident(item)
                        if res:
                            return res

                elif isinstance(node[key], dict):
                    res = self.find_ident(node[key])
                    if res:
                        return res
        return None

    def find_Literal(self, node):
        if node and 'type' in node.keys() and node['type'] == 'Literal':
            return node['value'], node['raw']
        return None

    def add_var(self, name):
        return {"type": "VariableDeclaration",
                "declarations": [
                    {
                        "type": "VariableDeclarator",
                        "id": {
                            "type": "Identifier",
                            "name": name
                        },
                        "init": None
                    }
                ],
                "kind": "var"}

    def add_arr(self, name):
        return {
            "type": "VariableDeclaration",
            "declarations": [
                {
                    "type": "VariableDeclarator",
                    "id": {
                        "type": "Identifier",
                        "name": name
                    },
                    "init": {
                        "type": "ArrayExpression",
                        "elements": []
                    }
                }
            ],
            "kind": "var"
        }

    def add_ass_pat(self, left_name, right_lit):
        return {
            "type": "VariableDeclaration",
            "declarations": [
                {
                    "type": "VariableDeclarator",
                    "id": {
                        "type": "Identifier",
                        "name": left_name
                    },
                    "init": {
                        "type": "Literal",
                        "value": right_lit[0],
                        "raw": right_lit[1]
                    }
                }
            ],
            "kind": "var"
        }

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

    def main(self):
        my_log.print_msg('------------------将代码解析为AST-------------------\n', 'INFO')
        self.parse_ast_path()
        my_log.print_msg('------------------保存简化后的非终结符子树------------\n', 'INFO')
        self.keep_es6p_subtrees()
        my_log.print_msg('------------------保存终结符叶子节点-----------------\n', 'INFO')
        self.single_keep_terminal()
        my_log.print_msg('------------------清理内存空间(如果需要连续运行）------\n', 'INFO')
        self.clear_ram()


if __name__ == '__main__':
    config_path = sys.argv[1]
    config_dict = load_json(config_path)
    grammar_pre = GrammarPreprocess(
        config_dict['seeds_path'],
        config_dict['seeds_ast_path'],
        config_dict['dataset_path'],
    )
    grammar_pre.main()
