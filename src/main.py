import os
import shutil
import time
import sys
from filter.filter import FilterTestCase
from utils import load_json
from generator.gra_gen import GrammarGen
from fuzz.ts_fuzz import TS_FUZZ
from ts_log import MyLog


def main():
    config_path = sys.argv[1]
    config_dict = load_json(config_path)
    fuzz_time = config_dict['fuzz_time']
    temp_seeds_path = config_dict['new_seeds_path']
    my_log = MyLog(config_dict['log_path'])
    grammar_gen = GrammarGen(
        my_log,
        config_dict['seeds_ast_path'],
        config_dict['dataset_path'],
        config_dict['new_ast_path'],
        config_dict['new_seeds_path'],
        config_dict['loop_nums'],
        config_dict['mutate_nums'],
        config_dict['leaves_nums']
    )
    grammar_gen.init_data()
    ts_fuzz = TS_FUZZ(
        my_log,
        config_dict['new_seeds_path'],
        config_dict['to_path'],
        config_dict['bug_dict_path'],
        config_dict['bug_keep_path'],
        config_dict['invalid_bug_path']
    )

    bug_filter = FilterTestCase(config_dict['bug_keep_path'],
                                config_dict['bug_dict_path'],
                                config_dict['found_bug_path'],
                                config_dict['filter_bug_path']
                                )

    start_time = time.time()
    now = time.time()
    turn = 1
    # while now - start_time < fuzz_time * 3600:
    while turn < 100:
        my_log.print_msg('generate No.' + str(turn) + ' data', 'INFO')
        if os.path.exists(temp_seeds_path):
            shutil.rmtree(temp_seeds_path)
            os.mkdir(temp_seeds_path)
            time.sleep(1)
        grammar_gen.main(turn)
        ts_fuzz.fuzz(turn)
        now = time.time()
        my_log.print_msg('now using time ' + str(int(now-start_time)) + 's\n', 'INFO')
        turn += 1
        bug_filter.main()


if __name__ == '__main__':
    main()

