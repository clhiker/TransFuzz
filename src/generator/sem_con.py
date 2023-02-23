'''
语义约束，完全的语义约束是无法实现的，我们只能尽可能的约束语法提高正确率
'''
import copy
import json
import ujson
import subprocess
from subprocess import PIPE
from utils import load_json, keep_json


class CallExpression:
    def __init__(self, name):
        self.type = 'CallExpression'
        self.name = name
        self.nest_args = {}


class MemberExpression:
    def __init__(self, obj_name, prop_name):
        self.type = 'MemberExpression'
        self.obj_name = obj_name  # 可以是 ident, meb_exp, call_exp, 我们根据name来找，name唯一
        self.prop_name = prop_name


class SemanticConstraints:
    def __init__(self):
        # 根据不同版本的语法进行定制
        self.declarations = {
            'FunctionDeclaration': set(),
            'VariableDeclarator': set(),
            'ClassDeclaration': set(),
            'AssignmentExpression': set(),
        }
        self.all_ident = set()
        self.all_decl = set()

        self.express = {
            'CallExpression': {},  # name : {nest: args}
            'MemberExpression': {},
            'NewExpression': {},
            'MetaProperty': {}
        }
        self.temp_add_func = {}
        self.add_body = []
        self.super_class_name = set()
        self.tt_exp_func = set()
        self.iter_exp_name = set()
        self.await_exp = []
        self.async_num = 0

    # 找到所有声明
    def find_declared(self, node):
        if node:
            if 'type' in node.keys():
                if node['type'] in self.declarations.keys():
                    if node['type'] == 'AssignmentExpression':
                        if node['operator'] == '=':
                            if 'name' in node['left']:
                                self.declarations[node['type']].add(node['left']['name'])
                                self.all_decl.add(node['left']['name'])
                    else:
                        id_node = node['id']
                        if id_node['type'] == 'Identifier':
                            self.declarations[node['type']].add(id_node['name'])
                            self.all_decl.add(id_node['name'])
                        elif id_node['type'] == 'ArrayPattern':
                            for item in id_node['elements']:
                                name = self.find_ident(item)
                                if name:
                                    self.declarations[node['type']].add(name)
                                    self.all_decl.add(name)

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.find_declared(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.find_declared(item)

    # 找到所有的 identifier
    def find_ident(self, node):
        if node and 'type' in node.keys() and node['type'] == 'Identifier':
            return node['name']
        return None

    def solve_get_set(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'MethodDefinition':
                func_exp = node['value']
                if node['kind'] == 'get':
                    if 'params' in func_exp.keys():
                        func_exp['params'] = []
                elif node['kind'] == 'set':
                    if 'params' in func_exp.keys():
                        if len(func_exp['params']) != 1:  # 1个清晰的变量
                            func_exp['params'] = [{
                                "type": "Identifier",
                                "name": "v_1"
                            }]
            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_get_set(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_get_set(item)

    def solve_super_class(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'ClassDeclaration':
                extend = node['superClass']
                if extend:
                    try:
                        self.super_class_name.add(extend['name'])
                    except KeyError:
                        pass
            if 'type' in node.keys() and node['type'] == 'ClassExpression':
                extend = node['superClass']
                if extend:
                    try:
                        self.super_class_name.add(extend['name'])
                    except KeyError:
                        pass

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_super_class(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_super_class(item)

    def add_super_class(self):
        for sc_name in self.super_class_name:
            super_class = {
                "type": "ClassDeclaration",
                "id": {
                    "type": "Identifier",
                    "name": sc_name
                },
                "superClass": None,
                "body": {
                    "type": "ClassBody",
                    "body": []
                }
            }
            self.add_body.append(super_class)
            self.declarations['ClassDeclaration'].add(sc_name)
            self.all_decl.add(sc_name)

    def solve_tt_exp(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'TaggedTemplateExpression':
                tag = node['tag']
                if tag:
                    try:
                        self.tt_exp_func.add(tag['name'])
                    except KeyError:
                        pass
            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_tt_exp(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_tt_exp(item)

    def add_tag_func(self):
        for tt_name in self.tt_exp_func:
            tt_func = {
                "type": "FunctionDeclaration",
                "id": {
                    "type": "Identifier",
                    "name": tt_name
                },
                "expression": False,
                "generator": False,
                "async": False,
                "params": [],
                "body": {
                    "type": "BlockStatement",
                    "body": []
                }
            }
            self.add_body.append(tt_func)
            self.declarations['FunctionDeclaration'].add(tt_name)
            self.all_decl.add(tt_name)

    def solve_iter_exp(self, node):
        if node:
            if 'type' in node.keys():
                if node['type'] == 'ForOfStatement':
                    right = node['right']
                    if right:
                        try:
                            self.iter_exp_name.add(right['name'])
                        except KeyError:
                            pass
                elif node['type'] == 'SpreadElement':
                    args = node['argument']
                    if args:
                        try:
                            self.iter_exp_name.add(args['name'])
                        except KeyError:
                            pass

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_iter_exp(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_iter_exp(item)

    def add_iter_array(self):
        for iter_name in self.iter_exp_name:
            iter_exp = {
                "type": "VariableDeclaration",
                "declarations": [
                    {
                        "type": "VariableDeclarator",
                        "id": {
                            "type": "Identifier",
                            "name": iter_name
                        },
                        "init": {
                            "type": "ArrayExpression",
                            "elements": []
                        }
                    }
                ],
                "kind": "var"
            }
            self.add_body.append(iter_exp)
            self.declarations['VariableDeclarator'].add(iter_name)
            self.all_decl.add(iter_name)

    def solve_await_exp(self, root, id, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'ForOfStatement':
                if node['await'] is True:
                    root[id] = self.add_async_func(node)
                    self.async_num += 1
                    node = root[id]['body']['body'][0]

            # if AwaitExpression : 向上溯源，到将declarations 类型的停止，然后替换为 async 函数

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_await_exp(node, key, node[key])
                elif isinstance(node[key], list):
                    for i in range(len(node[key])):
                        try:
                            self.solve_await_exp(node[key], i, node[key][i])
                        except IndexError:
                            pass

    def add_async_func(self, node):
        temp_node = copy.deepcopy(node)
        return {
            "type": "FunctionDeclaration",
            "id": {
                "type": "Identifier",
                "name": "f_" + str(self.async_num)
            },
            "expression": False,
            "generator": False,
            "async": True,
            "params": [],
            "body": {
                "type": "BlockStatement",
                "body": [
                    temp_node
                ]
            }
        }

    def solve_super_func(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'ClassDeclaration':
                super_list = []
                self.get_super_func(node, 0, node, super_list)
                if len(super_list) > 0:
                    if node['superClass'] is None:     # 没有父类，直接删除掉super调用
                        for item in super_list:
                            root, index, temp_node = item
                            try:
                                root.pop(index)
                            except IndexError:
                                pass
                    else:
                        const_exp = self.build_constructor()
                        for item in super_list:
                            root, index, temp_node = item
                            try:
                                root.pop(index)
                            except IndexError:
                                pass
                            const_exp['value']['body']['body'].append(temp_node)
                        node['body']['body'].insert(0, const_exp)

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_super_func(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_super_func(item)

    def get_super_func(self, root, id, node, super_list):
        if node:
            if 'type' in node.keys() and node['type'] == 'ExpressionStatement':
                exp_node = node['expression']
                if 'type' in exp_node.keys() and exp_node['type'] == 'CallExpression':
                    try:
                        if exp_node['callee']['type'] == 'Super':
                            super_list.append((root, id, node))
                    except:
                        pass

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.get_super_func(node, key, node[key], super_list)
                elif isinstance(node[key], list):
                    for i in range(len(node[key])):
                        try:
                            self.get_super_func(node[key], i, node[key][i], super_list)
                        except IndexError:
                            pass

    def solve_trash_paras(self, node):
        if node:
            if 'type' in node.keys():
                if node['type'] == 'FunctionDeclaration':
                    params = node['params']
                    params_set = set()
                    for ident in params[:]:
                        try:
                            if ident['name'] in params_set:
                                params.remove(ident)
                            else:
                                params_set.add(ident['name'])
                        except KeyError:
                            pass

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.solve_trash_paras(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.solve_trash_paras(item)

    def build_constructor(self):
        const_exp = {
            "type": "MethodDefinition",
            "static": False,
            "computed": False,
            "key": {
              "type": "Identifier",
              "name": "constructor"
            },
            "kind": "constructor",
            "value": {
              "type": "FunctionExpression",
              "id": None,
              "expression": False,
              "generator": False,
              "async": False,
              "params": [],
              "body": {
                "type": "BlockStatement",
                "body": []
              }
            }
        }
        return const_exp

    def solve_yield_exp(self, node):
        # 如果包裹在函数中，给函数添加生成式，否则删除掉
        pass

    # 关闭expression 标签
    def close_exp(self, node):
        if node:
            if 'type' in node.keys() and node['type'] == 'ArrowFunctionExpression':
                node['expression'] = False

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.close_exp(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.close_exp(item)

    # 找到复杂表达式和函数调用
    def find_exp(self, node):
        if node:
            if 'type' in node.keys():
                if node['type'] == 'CallExpression':
                    args_len = len(node['arguments'])
                    name = self.get_callee_name(node['callee'])
                    if name:
                        if name not in self.express['CallExpression'].keys():
                            self.express['CallExpression'][name] = [args_len]
                        else:
                            self.express['CallExpression'][name].append(args_len)

                elif node['type'] == 'MemberExpression':
                    prop_name, computed = self.get_prop_name(node['property'])
                    obj_name = self.get_obj_name(node['object'])
                    if obj_name and prop_name:
                        self.express['MemberExpression'][prop_name] = obj_name
                    # node['computed'] = computed
                    node['computed'] = False

                elif node['type'] == 'MetaProperty':
                    prop_name = self.get_prop_name(node['property'])
                    obj_name = self.get_obj_name(node['meta'])
                    if obj_name and prop_name:
                        self.express['MetaProperty'][prop_name] = obj_name

                elif node['type'] == 'NewExpression':
                    cons_name = self.get_construct_name(node['callee'])
                    cons_len = len(node['arguments'])
                    if cons_name:
                        self.express['NewExpression'][cons_name] = cons_len

            for key in node.keys():
                if isinstance(node[key], dict):
                    self.find_exp(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.find_exp(item)

    def get_construct_name(self, node):
        if node['type'] == 'Identifier':
            return node['name']
        else:
            return None

    def get_callee_name(self, node):
        """
        callee 继承了express，所以所有express 都是有可能作为name 的, 还要返回递归深度
        """
        if node['type'] == 'Identifier':
            return node['name']
        elif node['type'] == 'MemberExpression':
            return self.get_callee_name(node['property'])
        elif node['type'] == 'CallExpression':
            return self.get_callee_name(node['callee'])
        else:
            return None

    def get_obj_name(self, node):
        if node['type'] == 'Identifier':
            return node['name']
        elif node['type'] == 'MemberExpression':
            return self.get_obj_name(node['property'])
        elif node['type'] == 'CallExpression':
            return self.get_obj_name(node['callee'])
        elif node['type'] == 'ThisExpression':
            return None
        else:
            # print(node['type'])
            pass

    def get_prop_name(self, node):
        if node['type'] == 'Identifier':
            return node['name'], False
        # elif node['type'] == 'Literal':
        #     return node['value'], True
        return None, True

    # 找到所有 name
    def find_name(self, node):
        if node:
            if 'name' in node.keys():
                if node['name']:
                    self.all_ident.add(node['name'])
            for key in node.keys():
                if isinstance(node[key], dict):
                    self.find_name(node[key])
                elif isinstance(node[key], list):
                    for item in node[key]:
                        self.find_name(item)

    # 添加函数声明和对象声明
    def add_exp(self):
        for exp in self.express.keys():
            if exp == 'CallExpression':
                for func_name in self.express[exp].keys():
                    func_dec = self.add_function(func_name, self.express[exp][func_name], 0)
                    self.temp_add_func[func_name] = func_dec
                    self.all_decl.add(func_name)

            elif exp == 'MemberExpression':
                for prop_name in self.express[exp].keys():
                    obj_exp = self.add_obj_exp(self.express[exp][prop_name], prop_name)
                    if obj_exp:
                        self.add_body.append(obj_exp)
                    self.all_decl.add(self.express[exp][prop_name])

            elif exp == 'MetaProperty':
                for prop_name in self.express[exp].keys():
                    obj_exp = self.add_obj_exp(self.express[exp][prop_name], prop_name)
                    if obj_exp:
                        self.add_body.append(obj_exp)
                    self.all_decl.add(self.express[exp][prop_name])

            elif exp == 'NewExpression':
                for cons_name in self.express[exp].keys():
                    cons_exp = self.add_cons_exp(cons_name, self.express[exp][cons_name])
                    if cons_exp:
                        self.add_body.append(cons_exp)
                    self.all_decl.add(cons_name)

        for value in self.temp_add_func.values():
            self.add_body.append(value)

    def add_function(self, func_name, args_len_list, index):  # 从外层到内层
        paras = []
        if index == 0:
            if args_len_list[index] > 0:
                for id_name in range(args_len_list[index]):
                    paras.append({
                        'type': 'Identifier',
                        'name': 'v_' + str(id_name)
                    })
            return {
                'type': 'FunctionDeclaration',
                'id': {
                    'type': 'Identifier',
                    'name': func_name,
                },
                'params': paras,
                "body": {
                    "type": "BlockStatement",
                    "body": [
                        {
                            "type": "ReturnStatement",
                            "argument": None if len(args_len_list) == 1 else self.add_function(func_name, args_len_list,
                                                                                               index + 1)
                        }
                    ],
                }
            }
        elif index == len(args_len_list) - 1:
            if args_len_list[index] > 0:
                for id_name in range(args_len_list[index]):
                    paras.append({
                        'type': 'Identifier',
                        'name': 'v_' + str(id_name)
                    })
            return {
                'type': 'FunctionDeclaration',
                'id': None,
                'params': paras,
                "body": {
                    "type": "BlockStatement",
                    "body": [
                        {
                            "type": "ReturnStatement",
                            "argument": None
                        }
                    ],
                }
            }
        else:
            for id_name in range(args_len_list[index]):
                paras.append({
                    'type': 'Identifier',
                    'name': 'v_' + str(id_name)
                })
            return {
                'type': 'FunctionDeclaration',
                'id': None,
                'params': paras,
                "body": {
                    "type": "BlockStatement",
                    "body": [
                        {
                            "type": "ReturnStatement",
                            "argument": self.add_function(func_name, args_len_list, index + 1)
                        }
                    ],
                }
            }

    def add_obj_exp(self, obj_name, prop_name):
        properties = [
            {
                "type": "Property",
                "method": False,
                "shorthand": True,
                "computed": False,
                "key": {
                    "type": "Identifier",
                    "name": prop_name
                },
                "kind": "init",
                "value": {
                    "type": "Identifier",
                    "name": prop_name
                }
            }
        ]
        if obj_name not in self.temp_add_func.keys():
            obj_decl = {
                "type": "ExpressionStatement",
                "expression": {
                    "type": "AssignmentExpression",
                    "operator": "=",
                    "left": {
                        "type": "Identifier",
                        "name": obj_name
                    },
                    "right": {
                        "type": "ObjectExpression",
                        "properties": properties
                    }
                }
            }
            return obj_decl
        else:
            node = self.temp_add_func[obj_name]['body']['body'][0]
            while node['argument']:
                try:
                    node = node['argument']['body']['body'][0]
                except KeyError as key_error:
                    return None
            node['argument'] = {
                'type': 'ObjectExpression',
                'properties': properties
            }
            return None

    def add_cons_exp(self, cons_name, cons_len):
        paras = []
        if cons_len > 0:
            for id_name in range(cons_len):
                paras.append({
                    'type': 'Identifier',
                    'name': 'v_' + str(id_name)
                })
        return {
            "type": "FunctionDeclaration",
            "id": {
                "type": "Identifier",
                "name": cons_name
            },
            "expression": False,
            "generator": False,
            "async": False,
            "params": paras,
            "body": {
                "type": "BlockStatement",
                "body": []
            }
        }

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

    def add_ident(self):
        self.all_ident = self.all_ident - self.all_decl
        temp_id = []
        for ident in self.all_ident:
            temp_id.append(self.add_var(ident))
        self.add_body = temp_id + self.add_body

    def add_constraints(self, ast):
        # 解决get 和 set 问题
        self.solve_get_set(ast)
        # 关闭expression 标签
        self.close_exp(ast)

        self.solve_super_class(ast)
        self.solve_tt_exp(ast)
        self.solve_iter_exp(ast)
        self.solve_await_exp(ast, 0, ast)

        # 解决函数参数重复的问题
        self.solve_trash_paras(ast)

        # 解决在超类中调用super函数的情况
        self.solve_super_func(ast)

        # 5. 添加 父类 声明
        self.add_super_class()
        self.add_tag_func()
        self.add_iter_array()

        # 解决yield 表达式, 要放在生成函数的后面
        self.solve_yield_exp(ast)

        # 1. 找到所有函数调用和复杂表达式调用
        self.find_exp(ast)
        # 2. 找到所有变量调用
        self.find_name(ast)
        # 3. 找到所有函数，对象，变量 声明
        self.find_declared(ast)
        # 4. 添加 函数，对象 声明
        self.add_exp()
        # 5. 添加 变量 声明
        self.add_ident()

        return self.add_body


if __name__ == '__main__':
    # cmd = ['node', 'utils/js/acorn_parse.js'] + ['resolve_err/poc.js'] + ['resolve_err/poc.json'] + ['parse']
    # res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
    # if res.returncode == 0:
    ast = load_json('resolve_err/poc.json')
    sem_con = SemanticConstraints()
    add_body = sem_con.add_constraints(ast)
    program = {'type': 'Program', 'body': add_body, "sourceType": "module"}
    program['body'].extend(ast['body'])
    keep_json('resolve_err/poc_new.json', program)
    cmd = ['node', 'utils/js/es_gen.js'] + ['resolve_err/poc_new.json'] + ['resolve_err/poc_new.js']
    res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, timeout=10)
    print(res.stdout)
