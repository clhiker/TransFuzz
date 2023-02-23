import os
import shutil
import subprocess
import time

from subprocess import PIPE
from ts_log.log_info import MyLog
from estree import ES_DICT
from utils import load_json
from utils.multi_p import pool
my_log = MyLog('ts_log/eval_cvg.ts_log')


class EvalDepth:
    def __init__(self,
                 gen_js_path
                 ):
        self.temp_id = ''
        self.node_nums = 0
        self.gen_js_path = gen_js_path
        self.temp_ast_path = '../temp_ast'
        self.one_ast_list = []
        self.sub_ast_set = set()
        self.every_sub_ast_list = []
        self.every_avg_list = []
        self.type_dict = ES_DICT.TYPE_DICT
        self.es6_type = [self.type_dict[i] for i in ES_DICT.ES6_TYPE]
        self.es6p_type = [self.type_dict[i] for i in ES_DICT.ES6P_TYPE]
        my_log.print_msg('evaluate ' + self.gen_js_path, 'INFO')

    def keep_lit_ast(self, ast):
        for body in ast['body']:
            self.visit_ast(body)
            self.sub_ast_set.add(self.temp_id[:-1])
            self.every_sub_ast_list.append(self.temp_id[:-1])
            self.temp_id = ''
            self.keep_lit_ast_rec(body)

    def keep_lit_ast_rec(self, body):
        for key in body.keys():
            if isinstance(body[key], list):
                for it in body[key]:
                    if it is not None and 'type' in it.keys():
                        self.visit_ast(it)
                        self.sub_ast_set.add(self.temp_id[:-1])
                        self.temp_id = ''
                        self.keep_lit_ast_rec(it)
            elif isinstance(body[key], dict):
                if 'type' in body[key].keys():
                    self.visit_ast(body[key])
                    self.sub_ast_set.add(self.temp_id[:-1])
                    self.temp_id = ''
                    self.keep_lit_ast_rec(body[key])

    def visit_ast(self, node):
        if node:
            if 'type' in node.keys():
                self.temp_id += str(self.type_dict[node['type']]) + '-'
            for key in node.keys():
                if isinstance(node[key], list):
                    for it in node[key]:
                        if it is not None and 'type' in it.keys():
                            self.visit_ast(it)
                elif isinstance(node[key], dict):
                    if 'type' in node[key].keys():
                        self.visit_ast(node[key])

    def parse_ast(self):
        if os.path.exists(self.temp_ast_path):
            shutil.rmtree(self.temp_ast_path)
        os.mkdir(self.temp_ast_path)
        js_path_list = [os.path.join(self.gen_js_path, js) for js in os.listdir(self.gen_js_path)]
        ast_path_list = [os.path.join(self.temp_ast_path, js[:js.rfind('.')]+'.json')
                         for js in os.listdir(self.gen_js_path)]
        begin_time = time.time()
        pool.map(self.get_ast_frag, zip(js_path_list, ast_path_list))
        print('parse ast run：' + str(time.time() - begin_time) + 's')

    def get_ast_frag(self, paras):
        cmd = ['node', 'utils/js/acorn_parse.js'] + [paras[0]] + [paras[1]] + ['parse']
        try:
            res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
            if res.returncode != 0:
                print(res.stdout)
                print(res.stderr)
        except:
            print('error\t' + str(cmd))

    def total_sub_tree(self):
        # for js in os.listdir(self.gen_js_path):
        #     js_path = os.path.join(self.gen_js_path, js)
        #     with open(js_path, 'r') as f:
        #         code = f.read()
        #         try:
        #             ast = toDict(esprima.parse(code))
        #             self.keep_lit_ast(ast)
        #         except:
        #             print(js_path)
        for item in os.listdir(self.temp_ast_path):
            ast_path = os.path.join(self.temp_ast_path, item)
            ast = load_json(ast_path)
            try:
                self.keep_lit_ast(ast)
            except:
                print(ast_path)
        # shutil.rmtree(self.temp_ast_path)

    def eval_avg_sub(self):
        for sub_ast in self.every_sub_ast_list:
            count = 0
            sub_ast_list = sub_ast.split('-')
            for node in self.es6p_type:
                if str(node) in sub_ast_list:
                    count += 1
            self.every_avg_list.append(count / len(self.es6p_type))
        my_log.print_msg('average ' + str(sum(self.every_avg_list) / len(self.every_avg_list)), 'DEBUG')

    def eval_all_sub(self):
        count = 0
        for sub_ast in self.sub_ast_set:
            if int(sub_ast.split('-')[0]) in self.es6p_type:
                count += 1
        my_log.print_msg('There subtrees of es6p  ' + str(count), 'DEBUG')
        my_log.print_msg('There are no repeated subtrees ' + str(len(self.sub_ast_set)), 'DEBUG')
        my_log.print_msg('total ' + str(count / len(self.sub_ast_set)), 'DEBUG')

    def main(self):
        my_log.print_msg('There are seeds: ' + str(len(os.listdir(self.gen_js_path))), 'DEBUG')
        # self.parse_ast()
        self.total_sub_tree()
        self.eval_all_sub()
        self.eval_avg_sub()


if __name__ == '__main__':
    # eval_depth = EvalDepth('../corpus/es6plus/node/1k-ori')
    eval_depth = EvalDepth('../corpus/lite_es6/node/new_seeds')
    # eval_depth = EvalDepth('../corpus/es6plus/node/new_seeds')
    # eval_depth = EvalDepth('/home/clhiker/corpus/CA-result/100k-result/node-checked')
    # eval_depth = EvalDepth('/home/clhiker/corpus/COM-result/1k-result/node-checked')
    # eval_depth = EvalDepth('/home/clhiker/corpus/Mon-result/10k-result/node-checked')
    eval_depth.main()
