import logging
import datetime

class Colors:
  END = '\033[0m'
  ERROR = '\033[91m[ERROR] '    # 红
  DEBUG = '\033[92m[DEBUG] '    # 绿
  WARN = '\033[93m[WARN] '      # 黄
  INFO = '\033[94m[INFO] '      # 蓝


class MyLog:
    def __init__(self, log_path, data=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')):
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG
        )
        logging.info('\n\n')
        logging.info(data)

    def get_color(self, msg_type):
        if msg_type == 'ERROR':
            return Colors.ERROR
        elif msg_type == 'INFO':
            return Colors.INFO
        elif msg_type == 'WARN':
            return Colors.WARN
        elif msg_type == 'DEBUG':
            return Colors.DEBUG
        else:
            return Colors.END

    def print_msg(self, message, msg_type):
        if msg_type == 'ERROR':
            logging.error(message)
        elif msg_type == 'INFO':
            logging.info(message)
        elif msg_type == 'WARN':
            logging.warning(message)
        elif msg_type == 'DEBUG':
            logging.debug(message)
        things = ''.join([self.get_color(msg_type), message, Colors.END])
        print(things)


if __name__ == '__main__':
    my_log = MyLog("test.ts_log")
    my_log.print_msg('error', 'ERROR')
    my_log.print_msg('warn', 'WARN')
    my_log.print_msg('info', 'INFO')
    my_log.print_msg('debug', 'DEBUG')