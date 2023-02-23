import os

seeds_path = '../corpus/es6lit/seeds'
text_path = '../corpus/es6lit/new-dataset/data.txt'
if os.path.exists(text_path):
    os.remove(text_path)
count = 0
with open(text_path, 'a+') as tf:
    for js in os.listdir(seeds_path):
        js_path = os.path.join(seeds_path, js)
        try:
            with open(js_path, 'r') as jf:
                text = jf.read()
                tf.write('\n' + js + '测试用例\n')
                tf.write(text)
        except:
            count += 1
print(count)
