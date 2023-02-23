import random
from estree.ES_Grammar import ExtraEstree
from utils import tail_call_optimized


class VisitAST:
    def __init__(self):
        self.count = 0
        self.choose_len = 0
        self.max_rec = 3000  # 注意递归深度,挪到配置文件
        self.choose_node = {}
        self.es5_poses = set()
        self.terminals = {}  # 数据集
        self.estree = ExtraEstree()

    def total_no_terminal(self, node):
        self.count = 0
        self.total_func(node)
        return self.count

    # @tail_call_optimized
    def total_func(self, node):
        if node:
            if 'type' in node.keys():
                self.count += 1
                if self.count > self.max_rec:
                    self.count = -1
                    return -1
            for key in node.keys():
                if isinstance(node[key], list):
                    for item in node[key]:
                        if self.total_func(item) < 0:
                            return -1
                elif isinstance(node[key], dict):
                    if self.total_func(node[key]) < 0:
                        return -1
        return 1

    def get_es5_poses(self, node):
        self.count = 0
        self.es5_poses.clear()
        self.total_es5(node)
        return self.es5_poses

    def total_es5(self, node):
        if node:
            if 'type' in node.keys():
                if self.estree.grammar[node['type']].get_vers() == {'es2011'}:
                    self.es5_poses.add(self.count)
                self.count += 1
                if self.count > self.max_rec:
                    self.count = -1
                    return -1
            for key in node.keys():
                if isinstance(node[key], list):
                    for item in node[key]:
                        if self.total_es5(item) < 0:
                            return -1
                elif isinstance(node[key], dict):
                    if self.total_es5(node[key]) < 0:
                        return -1
        return 1

    def choose_sub(self, node, random_len):
        self.choose_len = random_len
        self.count = 0
        self.choose_func('', [0], node)
        return self.choose_node

    # @tail_call_optimized
    def choose_func(self, parent_node, key_info, node):
        if node:
            if 'type' in node.keys():
                self.count += 1
                if self.count == self.choose_len:  # 应该作为父节点
                    self.choose_node = parent_node, key_info, node
                    return 1

            for key in node.keys():
                if isinstance(node[key], list):
                    for i in range(len(node[key])):
                        if self.choose_func(node, [key, i], node[key][i]) > 0:
                            return 1

                elif isinstance(node[key], dict):
                    if self.choose_func(node, [key], node[key]) > 0:
                        return 1
        return -1

    def set_terminals(self, terminals):
        self.terminals = terminals

    def add_leaves(self, subtree):
        self.count = 0
        try:
            if self.rec_add_leaf(subtree):
                return self.count
            else:
                return -1
        except RecursionError:
            return -1

    # 增加一个语法指导
    def rec_add_leaf(self, node):
        if isinstance(node, list):
            for it in node:
                if it is not None:
                    if not self.rec_add_leaf(it):
                        return False
        elif isinstance(node, dict):
            terminal_type = ''
            for key in node.keys():
                if key == 'type':
                    terminal_type = node[key]  # 找到终结符的上层非终结符节点
                    self.count += 1
                    if self.count > 3000:  # 限制递归深度
                        return False
            for key in node.keys():
                if node[key] is None:
                    if key not in self.estree.no_terminal_key:  # 剔除非终结符的key，多为列表的key
                        try:
                            rules = self.estree.grammar[terminal_type].get_rules(key)
                            grammar_leaf = False
                            for rule in rules:
                                if rule.get_ver() != 'es2011' and rule.get_certain():  # 先判断语法条件，如果是确定性终结符，直接按照语法分配
                                    node[key] = rule.get_values()[
                                        random.randint(0, len(rule.get_values()) - 1)]
                                    grammar_leaf = True
                        except KeyError:
                            grammar_leaf = False

                        if not grammar_leaf:
                            try:  # 如果是不确定性终结符，随机选取
                                node[key] = self.terminals[key][terminal_type][
                                    random.randint(0, len(self.terminals[key][terminal_type]) - 1)]  # 修改这里
                            except KeyError:
                                continue
                if not self.rec_add_leaf(node[key]):
                    return False
        return True

    def add_raw(self, node):
        if isinstance(node, list):
            for it in node:
                if it is not None:
                    self.add_raw(it)

        elif isinstance(node, dict):
            for key in node.keys():
                if key == 'raw':
                    if 'cooked' in node:
                        node[key] = node['cooked']
                    else:
                        node[key] = node['value']
                self.add_raw(node[key])

    def total_context(self, node):
        pass

    def add_context_leaves(self):
        pass


if __name__ == '__main__':
    from utils import load_json

    # ../corpus/es6lit/ast/10401.json
    # ../corpus/es6lit/ast/14140.json
    # ../corpus/es6lit/ast/11385.json
    for path in ['../corpus/es6lit/ast/10401.json',
                 '../corpus/es6lit/ast/14140.json',
                 '../corpus/es6lit/ast/11385.json']:
        seed = load_json(path)
        visit_ast = VisitAST()
        visit_ast.get_es5_poses(seed)
