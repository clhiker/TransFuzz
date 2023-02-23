const acorn = require('acorn');
const walk =  require('acorn-walk');
const path = require("path");
const fs = require("fs");


function del_loc(ast){
    delete ast["start"];
    delete ast["end"];
    for (let key in ast){
        if (ast[key] !== null && ast[key] !== undefined && typeof(ast[key]) === 'object') {
            del_loc(ast[key]);
        }
    }
}

function a_parse(js_path, des){
    try {
        let text = fs.readFileSync(js_path, 'utf-8');
        let code = acorn.parse(text, {
            locations: false,
            ranges:false,
            sourceType: "script",
            ecmaVersion: "latest"
        });
        // walk.full(code, path => {
        //     if (path.type === 'MemberExpression'){
        //         path.computed = false;
        //     }
        // });
        del_loc(code);
        let ast = JSON.stringify(code, null, 2);
        // console.log(ast);
        fs.writeFileSync(des, ast);
    }catch (err) {
        console.log(err);
    }
}

function a_parse2rename(js_path, des) {
    try {
        let text = fs.readFileSync(js_path, 'utf-8');
        let code = acorn.parse(text, {
            locations: false,
            ecmaVersion: "latest"
        });
        let v = new Map();
        let f = new Map();
        let v_count = 0;
        let f_count = 0;
        walk.full(code, path => {
            if (path.type === 'VariableDeclaration'){
                let declarations = path.declarations;
                for(let decl of declarations){
                    let new_v = 'v' + v_count.toString();
                    v.set(decl.id.name, new_v);
                    decl.id.name = new_v;
                    v_count ++;
                }
            }
            if (path.type === 'FunctionDeclaration'){
                let new_f = 'f' + f_count.toString();
                f.set(path.id.name, new_f);
                path.id.name = new_f;
                f_count ++;
            }
            if (path.type === 'Identifier'){
                if(v.has(path.name)){
                    path.name = v.get(path.name);
                }
                if(f.has(path.name)){
                    path.name = f.get(path.name);
                }
            }
        });
        del_loc(code);
        let ast = JSON.stringify(code, null, 2);
        // console.ts_log(ast);
        fs.writeFileSync(des, ast);
    }catch (err) {
        console.log(err);
    }
}

if (process.argv.length === 5) {
    const src = path.resolve(process.argv[2]);
    const des = path.resolve(process.argv[3]);
    const option = process.argv[4];
    if (option === 'rename'){
        a_parse2rename(src, des);
    }else if (option === 'parse'){
        a_parse(src, des);
    }
    dir = true;
} else {
    dir = false;
}

// a_parse(path.resolve('/home/clhiker/TsFuzz-bench/corpus/lit/seeds/1.js'), '');