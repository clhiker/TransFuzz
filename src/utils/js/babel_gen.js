const babel = require('@babel/core');
const generator = require("@babel/generator").default;
const path = require("path");
const fs = require("fs");

function genJs(ast_path, des) {
    try {
        let text = fs.readFileSync(ast_path, 'utf-8');
        let ast = JSON.parse(text);
        let code = generator(ast).code;
        // console.log(code);
        fs.writeFileSync(des, code);
    }catch (err) {
        console.log(err);
    }
}

if (process.argv.length === 4) {
    const src = path.resolve(process.argv[2]);
    const des = path.resolve(process.argv[3]);
    genJs(src, des);
    dir = true;
} else {
    dir = false;
}

// genJs(path.resolve('/D/N2ttFuzz-v2/corpus/lite_es6/node/new_ast/0.json'), '');