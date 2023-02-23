const escodegen = require('escodegen');
const path = require("path");
const fs = require("fs");

function genJs(ast_path, des) {
    try {
        let text = fs.readFileSync(ast_path, 'utf-8');
        let ast = JSON.parse(text);
        let code = escodegen.generate(ast);
        // console.ts_log(code);
        fs.writeFileSync(des, code);
    }catch (err) {
        console.log(err);
    }
}

if (process.argv.length === 4) {
    const src = path.resolve(process.argv[2]);
    const des = path.resolve(process.argv[3]);
    genJs(src, des)
    dir = true;
} else {
    dir = false;
}

// genJs(path.resolve('/D/N2ttFuzz-v2/corpus/lite_es6/es/new_ast/0.json'), '')