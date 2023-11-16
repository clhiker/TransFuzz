
# TransFuzz
Source code of [Detecting JavaScript Transpiler bugs with Grammar-guided Mutation](https://ieeexplore.ieee.org/abstract/document/10123443).

## Environment
Tested on Ubuntu 20.04 with following environment.
- python v3.6.13
- npm v8.19.1
- n v9.0.0

## General Setup
For nodejs and npm and nodejs.
```shell
sudo apt install npm -y
sudo npm install -g n
sudo n latest                
```

For npm dependency
```shell
cd TransFuzz
sudo npm -i
```

For python dependency
```shell
cd TransFuzz
pip3 install -r requirement.txt
```

## Tips

### configuration
Please refer conf/README.md for writing the configuration file. 

### preprocess
```shell
cd src
python3 preprocess/pro_data.py <conf ABSPATH>
```
After this step, you can get subtree dataset and leaf dataset in dataset dir.

### fuzz
```shell
python3 main.py <conf ABSPATH>
```

### reduce
```shell
python3 reduce/JSReduce.py <conf ABSPATH> <reduced bug path> <reduced testcase path>
```
