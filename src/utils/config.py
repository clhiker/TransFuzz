import json
import os


def read(file_name, mode='rb', encoding=None):
    with open(file_name, mode, encoding=encoding) as f:
        return f.read()


class Config:
    def __init__(self, conf_path):
        conf = self.load_conf(conf_path)
        self.seeds_path = conf['seeds_path']
        self.seeds_ast_path = conf['seeds_ast_path']
        self.corpus_path = conf['corpus_path']

    def load_conf(self, conf_path):
        conf = read(conf_path, 'r')
        dec = json.JSONDecoder()
        conf = dec.decode(conf)
        return conf
