import copy
import gc
import hashlib
import json
import os
import shutil
import subprocess
import random
from subprocess import PIPE
import time
import sys

import tqdm

from utils.multi_p import pool

from generator.sem_con import SemanticConstraints
from generator.syn_con import SyntaxConstraints
from utils import load_json, keep_json
from generator.visit_ast import VisitAST
from estree.ES_Grammar import ExtraEstree

sys.setrecursionlimit(10000)  # 默认的递归深度只有 1000，我们增加递归深度到 系统允许上限


class GrammarGen:
    def __init__(self,
                 my_log,
                 seeds_ast_path,
                 dataset_path,
                 new_ast_path,
                 new_seeds_path,
                 loop_nums,
                 mutate_nums,
                 leaves_nums
                 ):
        self.my_log = my_log
        self.simple_ast_path = os.path.join(dataset_path, 'es6p-sub.json')
        self.terminal_path = os.path.join(dataset_path, 'node-terminal.json')
        self.new_ast_path = new_ast_path
        self.new_seeds_path = new_seeds_path
        self.simple_ast = {}
        self.ast_set = set()  # 记录独特非终结符的集合
        self.ast_dict = {}
        self.random_ast_header = []
        self.mutated_ast = []
        self.estree = ExtraEstree()
        self.visit_ast = VisitAST()

        # 原始AST 种子池
        self.ast_seeds = []
        for js in os.listdir(seeds_ast_path):
            seed = os.path.join(seeds_ast_path, js)
            self.ast_seeds.append(seed)

        # 变异参数
        self.loop_nums = loop_nums
        self.mutate_nums = mutate_nums
        self.leaves_nums = leaves_nums

        # 调试变量
        self.error_info = set()
        self.not_exist_node = set()
        self.add_node = set()
        self.success_node = set()
        self.choose_seeds = set()

    def load_ast(self):
        self.simple_ast = load_json(self.simple_ast_path)
        for key in self.simple_ast.keys():
            try:
                self.simple_ast[key] = eval(self.simple_ast[key])
            except:
                continue
        self.my_log.print_msg('一共有' + str(len(self.simple_ast)) + ' 个AST片段', 'DEBUG')

    def load_leaves(self):
        self.terminals = load_json(self.terminal_path)
        self.my_log.print_msg('一共有' + str(len(self.terminals)) + ' 种非终结符上层映射', 'DEBUG')

    def keep_ast_in_dict(self):  # 将子树按照非终结符分类进字典中
        for value in self.simple_ast.values():
            key = value[-1]
            if not isinstance(value[-2], dict):
                continue
            type_name = value[-2]['type']
            if key not in self.ast_dict.keys():
                self.ast_dict[key] = {}
                self.ast_dict[key][type_name] = [value]
            else:
                if type_name not in self.ast_dict[key].keys():
                    self.ast_dict[key][type_name] = [value]
                else:
                    self.ast_dict[key][type_name].append(value)

    def choose_header(self):
        self.random_ast_header.clear()
        random_asts = random.sample(self.ast_seeds, self.mutate_nums)  # 选取随机种子
        for path in tqdm.tqdm(random_asts):
            self.random_ast_header.append(load_json(path))

    def test_ori(self):
        self.random_ast_header.clear()
        random_asts = random.sample(self.ast_seeds, self.mutate_nums)  # 选取随机种子
        for path in tqdm.tqdm(random_asts):
            self.random_ast_header.append(path)  # 这一句是为了配合下面的test_ori 函数的，调试代码行

        print('清理之前的数据')
        if os.path.exists(self.new_ast_path):
            shutil.rmtree(self.new_ast_path)
        os.mkdir(self.new_ast_path)
        if os.path.exists(self.new_seeds_path):
            shutil.rmtree(self.new_seeds_path)
        os.mkdir(self.new_seeds_path)
        time.sleep(1)

        # 转换一下
        print('生成新的AST')
        for ast_path in self.random_ast_header:
            ast = load_json(ast_path)
            new_ast_path = os.path.join(self.new_ast_path, ast_path[ast_path.rfind('/') + 1:])
            keep_json(new_ast_path, ast)

        print('开始转换')
        ast_path_list = self.random_ast_header
        js_path_list = []
        for ast in self.random_ast_header:
            ast = ast[ast.rfind('/') + 1:]
            name = ast[:ast.rfind('.')]
            js_path = os.path.join(self.new_seeds_path, name + '.js')
            js_path_list.append(js_path)
        pool.map(self.trans2js, zip(ast_path_list, js_path_list))

    # 由于包含单例类VisitAST， 所以是单线程的
    def mutate_ast(self, turn):
        if os.path.exists(self.new_ast_path):
            shutil.rmtree(self.new_ast_path)
            time.sleep(1)
        os.mkdir(self.new_ast_path)

        for seed in tqdm.tqdm(self.random_ast_header):
            loop = 0
            while loop < self.loop_nums:  # 迭代循环
                es5pos = self.visit_ast.get_es5_poses(seed)
                if not es5pos:
                    continue
                times = 0
                choose_info = ()
                while times < 5 and len(es5pos) > 0:  # 通过循环增加找到合适种子的正确率
                    times += 1
                    random_pos = random.choice(tuple(es5pos))
                    es5pos.remove(random_pos)
                    if random_pos < 2 or random_pos > 3000:
                        continue
                    choose_info = self.visit_ast.choose_sub(seed, random_pos)  # ret = 父节点, 定位父节点的pos
                    if len(choose_info) != 0:
                        break
                    es5pos.add(random_pos)              # 没找到还放回去
                if len(choose_info) == 0:  # 10次还没找到，很罕见，就返回 / 考虑后面抛弃这个AST 种子
                    break
                parent_node, key_info, old_node = choose_info
                self.change_subtree(seed, parent_node, key_info, old_node)
                self.mutate_leaf(seed)
                loop += 1

        self.my_log.print_msg('一共变异生成了' + str(len(self.mutated_ast)) + ' 个AST片段', 'DEBUG')
        self.my_log.print_msg('每次变异上轮变异后种子,添加随机种子头到种子池', 'WARN')
        self.random_ast_header.clear()

        tree_count = 0
        for new_ast in self.mutated_ast:
            try:
                with open(os.path.join(self.new_ast_path,
                                       str(turn) + '-' + str(tree_count) + '.json'), 'w') as jf:
                    jf.write(json.dumps(new_ast, indent=1))
                tree_count += 1
            except ValueError:
                pass

    # 添加非终结符
    def add_subtree(self, choose_node, seed):
        p_type, node, key = choose_node
        attempt = 0
        while attempt < 10:
            attempt += 1
            if node[key] is None:
                sim_types = self.estree.dict_get_new_types(p_type, key, 'es2015')  # 字典情况
            elif len(node[key]) == 0:
                sim_types = self.estree.list_get_new_types(p_type, key, 'es2015')  # 列表情况
            else:
                continue
            if not sim_types:
                # print('没有选取到合适的非终结符')
                continue
            new_type = sim_types[random.randint(0, len(sim_types) - 1)]
            if new_type not in self.ast_dict or new_type == 'Super':
                # print('字典中没有合适的非终结符')
                continue
            random_subtree = self.ast_dict[new_type][random.randint(0, len(self.ast_dict[new_type]) - 1)]
            if node[key] is None:
                node[key] = random_subtree
                self.mutated_ast.append((seed, node[key]))  # 我们存储修改的种子和修改的子树
            elif len(node[key]) == 0:
                node[key] = [random_subtree]
                self.mutated_ast.append((seed, node[key][0]))  # 我们存储修改的种子和修改的子树
            return True
        return False

    # 删除非终结符
    def del_subtree(self, choose_node, seed):
        p_type, node, key = choose_node
        attempt = 0
        while attempt < 10:
            attempt += 1
            if not node[key] or len(node[key]) == 0:       # 已经是空(None|[]|{})就没办法删除了
                # print('空')
                continue
            if isinstance(node[key], list):     # 如果是列表则随机删除一个元素
                # print('随机删除列表元素')
                node[key].pop(random.randint(0, len(node[key])-1))
                self.mutated_ast.append(seed)
                return True
            elif isinstance(node[key], dict):     # 如果是字典就查看语法判断是否可以是空字典
                if self.estree.find_null_type(p_type, key):     # 当前节点可以是空
                    # print('将字典替换为空')
                    node[key] = None
                    self.mutated_ast.append(seed)
                    return True
                else:
                    continue
        return False

    # 修改非终结符
    def change_subtree(self, seed, parent_node, key_info, old_node):
        p_type = parent_node['type']
        key = key_info[0]
        attempt = 0
        while attempt < 10:
            attempt += 1
            if len(key_info) > 1:
                sim_types = self.estree.list_get_new_types(p_type, key, 'es2015')  # 字典情况
            else:
                sim_types = self.estree.dict_get_new_types(p_type, key, 'es2015')  # 字典情况
            if not sim_types:
                continue
            if key in self.ast_dict.keys():
                choose_types = list(set(sim_types) & set(self.ast_dict[key]))
                if len(choose_types) > 0:
                    new_type = choose_types[random.randint(0, len(choose_types) - 1)]
                    if new_type == 'Super':
                        continue
                    # chose_sub = self.ast_dict[new_type][random.randint(0, len(self.ast_dict[new_type]) - 1)]
                    chose_sub = self.ast_dict[key][new_type][random.randint(0, len(self.ast_dict[key][new_type]) - 1)]

                    random_subtree = chose_sub[-2]
                    if len(key_info) > 1:       # list
                        parent_node[key_info[0]][key_info[1]] = random_subtree
                    else:                       # dict
                        parent_node[key] = random_subtree
                    # 添加语义约束

                    syn_con = SyntaxConstraints()
                    # 保留原始的声明
                    old_decl = syn_con.keep_old_decl(old_node)
                    if len(chose_sub) > 1:
                        old_decl.extend(chose_sub[0:-2])
                    seed['body'] = old_decl + seed['body']

                    syn_con.correct_program(seed)
                    self.mutated_ast.append(seed)
                    return True

        return False

    def mutate_leaf(self, seed):
        self.visit_ast.set_terminals(self.terminals)
        node_nums = self.visit_ast.add_leaves(seed)
        if node_nums > 0:  # 越复杂越难正确生成，假设只取递归深度超过1000的测试用例
            self.visit_ast.add_raw(seed)

    def multi_trans2js(self):
        if os.path.exists(self.new_seeds_path):
            shutil.rmtree(self.new_seeds_path)
        os.mkdir(self.new_seeds_path)

        ast_path_list = []
        js_path_list = []
        for ast in os.listdir(self.new_ast_path):
            name = ast[:ast.rfind('.')]
            ast_path = os.path.join(self.new_ast_path, ast)
            js_path = os.path.join(self.new_seeds_path, name + '.js')
            ast_path_list.append(ast_path)
            js_path_list.append(js_path)

        begin_time = time.time()
        pool.map(self.trans2js, zip(ast_path_list, js_path_list))
        print('gen js run：' + str(time.time() - begin_time) + 's')

    def trans2js(self, paras):
        cmd = ['node', 'utils/js/es_gen.js'] + [paras[0]] + [paras[1]]
        # cmd = ['node', 'utils/js/babel_gen.js'] + [paras[0]] + [paras[1]]
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if len(res.stdout) > 0:
                std_out = res.stdout.decode('utf-8').split('\n')
                self.error_info.add(std_out[0])
                # print(std_out[0])
        except:
            print('error\t' + str(cmd))
            pass

    def evaluate(self):
        if len(os.listdir(self.new_seeds_path)) == 0:
            self.my_log.print_msg('没有生成任何成功的测试用例', 'ERROR')
        else:
            self.my_log.print_msg('一共成功生成了' + str(len(os.listdir(self.new_seeds_path))) + '个新的JS程序', 'DEBUG')
            self.my_log.print_msg('the success rate of mutate is ' +
                                  str(len(os.listdir(self.new_seeds_path)) / len(os.listdir(self.new_ast_path))),
                                  'DEBUG')
            # print(self.error_info)

    def init_data(self):
        self.my_log.print_msg('-------------加载语法树--------------', 'INFO')
        self.load_ast()
        self.load_leaves()
        self.my_log.print_msg('-------------将AST保存进字典---------', 'INFO')
        self.keep_ast_in_dict()

    def clear_data(self):
        self.mutated_ast.clear()
        gc.collect()

    def hash_total(self):
        hash_set = set()
        for ast in self.ast_set:
            hash_set.add(hash(ast))

    def main(self, turn):
        self.my_log.print_msg('-------------选择随机种子头-----------', 'INFO')
        self.choose_header()

        self.my_log.print_msg('-------------变异语法树--------------', 'INFO')
        self.mutate_ast(turn)

        self.my_log.print_msg('-------------转换成JS----------------', 'INFO')
        self.multi_trans2js()

        self.my_log.print_msg('-------------转换率结果评估-----------', 'INFO')
        self.evaluate()

        self.my_log.print_msg('-------------清理生成结果-------------', 'INFO')
        self.clear_data()


if __name__ == '__main__':
    from ts_log import MyLog
    from utils.multi_p import CHECK

    check = CHECK()
    gen_log = MyLog('ts_log/gen.log')
    gen_seed_path = '../corpus/es6lit/new_seeds'
    # 完整数据集
    grammar_gen = GrammarGen(
        gen_log,
        '../corpus/es6lit/ast',
        '../corpus/es6lit/new-dataset',
        '../corpus/es6lit/new_ast',
        gen_seed_path,
        1,
        1000,
        1
    )
    grammar_gen.init_data()
    for i in range(1, 2):
        grammar_gen.main(i)
        print('\n开始筛选出语法语义正确的程序\n')
        ok_seeds_list = check.multi_syntax_check(gen_seed_path)
        print('\n有' + str(len(ok_seeds_list)) + '个种子通过了检查\n')
