import os
import re
import shutil
import tqdm


class CpEs6:
    def __init__(self,
                 js_home_path,
                 ok_js_path):
        self.js_home_path = js_home_path
        self.md_path = os.path.join(self.js_home_path, 'md_path')
        self.js_path_list = []
        self.md_path_list = []
        self.ok_js_count = 0
        self.ok_js_path = ok_js_path
        self.es6_list = []

    # 得到JS 的文件列表
    def get_path(self):
        self.get_file_list(self.js_home_path, 'md', self.md_path_list)
        print('there are md ' + str(len(self.md_path_list)))
        self.extract_js_from_md()
        self.get_file_list(self.js_home_path, 'js', self.js_path_list)
        print('there are js ' + str(len(self.js_path_list)))

    def cp_js(self):
        for js in tqdm.tqdm(self.js_path_list):
            name = js[js.rfind('/')+1:]
            des = os.path.join(self.ok_js_path, name)
            try:
                shutil.copy(js, des)
            except:
                continue

    # 从readme 中提取JS
    def extract_js_from_md(self):
        count = 0
        for md in tqdm.tqdm(self.md_path_list):
            try:
                with open(md, 'r') as f:
                    js = f.read()
            except:
                js = ''
            try:
                md_text_list = re.findall(r'```javascript(.*?)```', js, re.S)
                md_text_list += re.findall(r'```js(.*?)```', js, re.S)
                md_text_list += re.findall(r'```JavaScript(.*?)```', js, re.S)
            except:
                md_text_list = []
            for i in range(len(md_text_list)):
                try:
                    js_text = md_text_list[i]
                    # js_path = md[:md.rfind('.')] + '_' + str(i) + '.js' 直接提取到当地
                    js_path = self.md_path + str(count) + '.js'
                    with open(js_path, 'w') as jf:
                        jf.write(js_text)
                    count += 1
                except:
                    pass

    def get_file_list(self, path, file_type, path_list):
        for item in os.listdir(path):
            file = os.path.join(path, item)
            if os.path.isdir(file):
                self.get_file_list(file, file_type, path_list)
            else:
                if file[file.rfind('.') + 1:] == file_type:
                    path_list.append(file)

    def main(self):
        self.get_path()
        self.cp_js()


if __name__ == '__main__':
    cp_es6 = CpEs6('/D/Corpus/es6+',
                   '/D/Corpus/es6pjs')
    cp_es6.main()