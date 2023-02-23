import os
import random
import re


def deal_rule(spec):        # ret dict
    rules = spec[spec.find('{') + 1: spec.rfind('}')]
    rules = re.sub(r'\n', ' ', rules)
    rules = re.sub(r' +', '', rules)
    # rules = re.sub(r'\[', '', rules)
    # rules = re.sub(r']', '', rules)
    rules = rules[:-1]
    if len(rules) > 0:
        if '{' in rules:
            values = rules[rules.find('{') + 1: rules.rfind('}')-1]
            values = {i.split(':')[0]: i.split(':')[1].split('|') for i in values.split(';')}
            rules = rules.split(';')
            for item in rules:
                if '{' in item:
                    key = item[:item.find(':')]
                    break
            rules = ';'.join(rules)
            rules = re.sub(r'\{(.*?)\}', '', rules)
            rules = {i.split(':')[0]: i.split(':')[1].split('|') for i in rules.split(';')}
            rules[key] = values
        else:
            if '[' not in rules:
                rules = {i.split(':')[0]: i.split(':')[1].split('|') for i in rules.split(';')}
            else:
                temp = {}
                for line in rules.split(';'):
                    if '[' in line:
                        line = line.replace('[', '')
                        line = line.replace(']', '')
                        temp[line.split(':')[0]] = [line.split(':')[1].split('|')]
                    else:
                        temp[line.split(':')[0]] = line.split(':')[1].split('|')
                return temp
    else:
        rules = {}
    return rules


def deal_enum(spec):        # ret list
    rules = spec[spec.find('{') + 1: spec.find('}')]
    rules = re.sub(r'\n', ' ', rules)
    rules = re.sub(r' +', '', rules)
    rules = re.findall(r'"(.*?)"', rules, re.S)
    return rules


class RULE:
    def __init__(self, version, key, values, certain):
        self.version = version  # str
        self.key = key
        self.values = values
        self.certain = certain  # bool
        self.del_dou_qut()

    def get_ver(self):
        return self.version

    def get_key(self):
        return self.key

    def get_values(self):
        return self.values

    def get_certain(self):
        return self.certain

    def del_dou_qut(self):
        if isinstance(self.values, list):
            for i in range(len(self.values)):
                if isinstance(self.values[i], list):
                    continue
                self.values[i] = self.values[i].strip('"')
        elif isinstance(self.values, dict):
            for val in self.values.values():
                for i in range(len(val)):
                    val[i] = val[i].strip('"')


class Node:
    def __init__(self, type_name):
        self.type_name = type_name
        self.versions = set()
        self.rule_keys = []
        self.rules = []
        self.parents = set()
        self.unfold = False

    def get_rules(self, key):
        res = []
        for r in self.rules:
            if r.get_key() == key:
                res.append(r)
        return res

    def get_all_rules(self):
        return self.rules

    def add_vers(self, ver):
        self.versions.add(ver)

    def ext_rules(self, rules):
        self.rules.extend(rules)

    def app_rule(self, rule):
        self.rules.append(rule)

    def uni_parents(self, parent):  # par : []
        self.parents |= parent

    def get_parents(self):
        return self.parents

    def get_vers(self):
        return self.versions

    def get_unfold(self):
        return self.unfold

    def set_unfold(self, unfold):
        self.unfold = unfold

    def ext_rule_keys(self, rule_keys):
        self.rule_keys.extend(rule_keys)

    def app_rule_keys(self, rule_key):
        self.rule_keys.append(rule_key)

    def get_rules_keys(self):
        return self.rule_keys


class ExtraEstree:
    def __init__(self):
        self.es_home_path = 'estree/SPEC/'
        self.es_spec = ['es5', 'es2015', 'es2016', 'es2017', 'es2018', 'es2019', 'es2020', 'es2021', 'es2022']
        self.no_terminal_key = {'sourceType', 'type', 'raw',
                                'body', 'params', 'expressions', 'element', 'arguments',
                                'properties', 'elements'}
        self.grammar = {}
        self.par_sons = {}

        self.extra()
        self.unfold_grammar()
        self.deal_inherit()
        pass

    def extra(self):
        for es in self.es_spec:
            spec_list = []
            es_path = os.path.join(self.es_home_path, es + '.md')
            with open(es_path, 'r') as f:
                text = f.read()

            if es == 'es5':
                es = 'es2011'

            temp_list = re.findall(r'```js\n(.*?)```', text, re.S)
            temp_list.extend(re.findall(r'```jsrex\n(.*?)```', text, re.S))
            for item in temp_list:
                if '\n\n' in item:
                    spec_list.extend(item.split('\n\n'))
                else:
                    spec_list.append(item)

            for spec in spec_list:
                type_info = re.sub(r',', '', spec[:spec.find('{')])
                type_list = type_info.split(' ')[:-1]
                if 'enum' in spec:
                    if 'extend' in spec:
                        type_name = type_list[type_list.index('enum') + 1]
                        node = self.grammar[type_name]
                        node.add_vers(es)
                        rules = deal_enum(spec)
                        r = list(set(rules) - set(node.get_all_rules()[0].get_values()))
                        node.app_rule(RULE(es, None, r, self.jg_cert(r)))
                        continue
                    else:
                        type_name = type_list[type_list.index('enum') + 1]
                        node = Node(type_name)
                        node.add_vers(es)
                        rules = deal_enum(spec)
                        one_rule = RULE(es, None, rules, True)
                        node.app_rule(one_rule)
                        self.grammar[type_name] = node
                        continue
                if 'extend' in spec:
                    # # print(spec)
                    type_name = type_list[type_list.index('interface') + 1]
                    node = self.grammar[type_name]
                    ori_keys = node.get_rules_keys()
                    rules = deal_rule(spec)
                    node.add_vers(es)
                    for key in rules.keys():
                        if key in ori_keys:
                            for rs in node.get_rules(key):
                                if isinstance(rules[key], list):
                                    if isinstance(rules[key][0], list):
                                        r = [list(set(rules[key][0]) - set(rs.get_values()[0]))]
                                    else:
                                        r = list(set(rules[key]) - set(rs.get_values()))
                                    node.app_rule(RULE(es, key, r, self.jg_cert(r)))
                        else:
                            node.app_rule(RULE(es, key, rules[key], self.jg_cert(rules[key])))
                    node.ext_rule_keys(rules.keys())
                    continue

                type_name = type_list[type_list.index('interface') + 1]
                node = Node(type_name)
                node.add_vers(es)
                if '<:' in type_list:
                    inherit = set(type_list[type_list.index('<:') + 1:])
                    node.uni_parents(inherit)
                rules = deal_rule(spec)
                node.ext_rule_keys(rules.keys())
                for key in rules.keys():
                    one_rule = RULE(es, key, rules[key], self.jg_cert(rules[key]))
                    node.app_rule(one_rule)
                self.grammar[type_name] = node

    def deal_inherit(self):
        for type_name in self.grammar:
            if len(self.grammar[type_name].get_parents()) > 0:
                for item in self.grammar[type_name].get_parents():
                    if item not in self.par_sons:
                        self.par_sons[item] = {type_name}
                    else:
                        self.par_sons[item].add(type_name)

    def unfold_grammar(self):
        for node in self.grammar.values():
            if len(node.get_parents()) == 0:
                node.set_unfold(True)
        for node in self.grammar.values():
            if not node.get_unfold():
                self.unfold_node(node)

        for node in self.grammar.values():
            temp_pars = node.get_parents().copy()
            for parent in temp_pars:
                node.uni_parents(self.unfold_parents(parent))

    def unfold_node(self, node):
        for parent in node.get_parents():
            if not self.grammar[parent].get_unfold():
                self.unfold_node(self.grammar[parent])

        node_rule_keys = node.get_rules_keys()
        for parent in node.get_parents():
            rule_keys = self.grammar[parent].get_rules_keys()
            for r_k in rule_keys:
                if r_k not in node_rule_keys:
                    node.app_rule_keys(r_k)
                    node.ext_rules(self.grammar[parent].get_rules(r_k))
        node.set_unfold(True)

    def unfold_parents(self, node_name):
        if len(self.grammar[node_name].get_parents()) > 0:
            node = self.grammar[node_name]
            for par_name in node.get_parents():
                self.unfold_parents(par_name)
            return node.get_parents()
        else:
            return set()

    def jg_cert(self, rule_l):
        if len(rule_l) > 0 and isinstance(rule_l, list):
            if isinstance(rule_l[0], list):
                return False
            elif '"' in ''.join(rule_l):
                return True
            else:
                return False
        return False

    def get_grammar(self):
        return self.grammar

    def get_par_sons(self):
        return self.par_sons

    def list_get_new_types(self, p_type, key, es):
        rules = self.grammar[p_type].get_rules(key)
        s_type = []
        for rule in rules:
            s_type.extend(rule.get_values()[0])
        return self.choose_es_son(s_type, es)

    def dict_get_new_types(self, p_type, key, es):
        rules = self.grammar[p_type].get_rules(key)
        s_type = []
        for rule in rules:
            s_type.extend(rule.get_values())
        return self.choose_es_son(s_type, es)

    def choose_es_son(self, s_type, es):
        s_type = s_type[random.randint(0, len(s_type) - 1)]
        if s_type == 'null':
            return None
        if s_type in self.par_sons.keys():
            sat_node = []
            for item in self.par_sons[s_type]:
                for ver in self.grammar[item].get_vers():
                    if ver >= es:
                        sat_node.append(item)
            if len(sat_node) > 0:
                return sat_node  # return str_list: type_name
            else:
                unsat_node = []
                for item in self.par_sons[s_type]:
                    unsat_node.append(item)
                return unsat_node
        else:
            for ver in self.grammar[s_type].get_vers():
                if ver >= es:
                    return [s_type]
            return None

    def find_null_type(self, p_type, key):
        rules = self.grammar[p_type].get_rules(key)
        s_type = []
        for rule in rules:
            s_type.extend(rule.get_values())
        if 'null' in s_type:
            return True
        return False

    # def get_de_null_type(self, p_type, key):
    #
    #     rules = self.grammar[p_type].get_rules(key)
    #     s_type = []
    #     for rule in rules:
    #         s_type.extend(rule.get_values())
    #     s_type = s_type[random.randint(0, len(s_type) - 1)]
    #     if isinstance(s_type, list):
    #         s_type = s_type[random.randint(0, len(s_type) - 1)]
    #     return s_type


if __name__ == '__main__':
    extra_estree = ExtraEstree()
    # # print(extra_estree.get_new_types('ExportNamedDeclaration', 'declaration', 'es2015'))