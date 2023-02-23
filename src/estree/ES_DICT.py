
TYPE_DICT = {
    'Identifier': 0,
    'Literal': 1,
    'Program': 2,
    'ExpressionStatement': 3,
    'Directive': 4,
    'BlockStatement': 5,
    'EmptyStatement': 6,
    'DebuggerStatement': 7,
    'WithStatement': 8,
    'ReturnStatement': 9,
    'LabeledStatement': 10,
    'BreakStatement': 11,
    'ContinueStatement': 12,
    'IfStatement': 13,
    'SwitchStatement': 14,
    'SwitchCase': 15,
    'ThrowStatement': 16,
    'TryStatement': 17,
    'CatchClause': 18,
    'WhileStatement': 19,
    'DoWhileStatement': 20,
    'ForStatement': 21,
    'ForInStatement': 22,
    'FunctionDeclaration': 23,
    'VariableDeclaration': 24,
    'VariableDeclarator': 25,
    'ThisExpression': 26,
    'ArrayExpression': 27,
    'ObjectExpression': 28,
    'Property': 29,
    'FunctionExpression': 30,
    'UnaryExpression': 31,
    'UpdateExpression': 32,
    'BinaryExpression': 33,
    'AssignmentExpression': 34,
    'LogicalExpression': 35,
    'MemberExpression': 36,
    'ConditionalExpression': 37,
    'CallExpression': 38,
    'NewExpression': 39,
    'SequenceExpression': 40,
    'ForOfStatement': 41,
    'Super': 42,
    'SpreadElement': 43,
    'ArrowFunctionExpression': 44,
    'YieldExpression': 45,
    'TemplateLiteral': 46,
    'TaggedTemplateExpression': 47,
    'TemplateElement': 48,
    'AssignmentProperty': 49,
    'ObjectPattern': 50,
    'ArrayPattern': 51,
    'RestElement': 52,
    'AssignmentPattern': 53,
    'ClassBody': 54,
    'MethodDefinition': 55,
    'ClassDeclaration': 56,
    'ClassExpression': 57,
    'MetaProperty': 58,
    'ImportDeclaration': 59,
    'ImportSpecifier': 60,
    'ImportDefaultSpecifier': 61,
    'ImportNamespaceSpecifier': 62,
    'ExportNamedDeclaration': 63,
    'ExportSpecifier': 64,
    'AnonymousDefaultExportedFunctionDeclaration': 65,
    'AnonymousDefaultExportedClassDeclaration': 66,
    'ExportDefaultDeclaration': 67,
    'ExportAllDeclaration': 68,
    'AwaitExpression': 69,
    'ChainExpression': 70,
    'ImportExpression': 71,
    'PropertyDefinition': 72,
    'PrivateIdentifier': 73,
    'StaticBlock': 74,
}

ES6_TYPE = {
    'ForOfStatement',
    'Super',
    'SpreadElement',
    'ArrowFunctionExpression',
    'YieldExpression',
    'TemplateLiteral',
    'TaggedTemplateExpression',
    'TemplateElement',
    'AssignmentProperty',
    'ArrayPattern',
    'RestElement',
    'AssignmentPattern',
    'ClassBody',
    'MethodDefinition',
    'ClassDeclaration',
    'ClassExpression',
    'MetaProperty',
    'ImportDeclaration',
    'ImportSpecifier',
    'ImportDefaultSpecifier',
    'ImportNamespaceSpecifier',
    'ExportNamedDeclaration',
    'ExportSpecifier',
    'AnonymousDefaultExportedFunctionDeclaration',
    'ExportAllDeclaration',
}

ES6P_TYPE = {
    'ForOfStatement',
    'Super',
    'SpreadElement',
    'ArrowFunctionExpression',
    'YieldExpression',
    'TemplateLiteral',
    'TaggedTemplateExpression',
    'TemplateElement',
    'AssignmentProperty',
    'ObjectPattern',
    'ArrayPattern',
    'RestElement',
    'AssignmentPattern',
    'ClassBody',
    'MethodDefinition',
    'ClassDeclaration',
    'ClassExpression',
    'MetaProperty',
    'ImportDeclaration',
    'ImportSpecifier',
    'ImportDefaultSpecifier',
    'ImportNamespaceSpecifier',
    'ExportNamedDeclaration',
    'ExportSpecifier',
    'AnonymousDefaultExportedFunctionDeclaration',
    'AnonymousDefaultExportedClassDeclaration',
    'ExportDefaultDeclaration',
    'ExportAllDeclaration',
    'AwaitExpression',
    'ChainExpression',
    'ImportExpression',
    'PropertyDefinition',
    'PrivateIdentifier',
    'StaticBlock',
}

ES6P_RULES = {
    'ForOfStatement',
    'Super',
    'SpreadElement',
    'ArrowFunctionExpression',
    'YieldExpression',
    'TemplateLiteral',
    'TaggedTemplateExpression',
    'TemplateElement',
    'AssignmentProperty',
    'ObjectPattern',
    'ArrayPattern',
    'RestElement',
    'AssignmentPattern',
    'ClassBody',
    'MethodDefinition',
    'ClassDeclaration',
    'ClassExpression',
    'MetaProperty',
    'ImportDeclaration',
    'ImportSpecifier',
    'ImportDefaultSpecifier',
    'ImportNamespaceSpecifier',
    'ExportNamedDeclaration',
    'ExportSpecifier',
    'AnonymousDefaultExportedFunctionDeclaration',
    'AnonymousDefaultExportedClassDeclaration',
    'ExportDefaultDeclaration',
    'ExportAllDeclaration',
    'AwaitExpression',
    'ChainExpression',
    'ImportExpression',
    'PropertyDefinition',
    'PrivateIdentifier',
    'StaticBlock',
}

RESERVED_WORD = {
    'abstract', 'arguments', 'await', 'boolean',
    'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue',
    'debugger', 'default', 'delete', 'do',
    'double', 'else', 'enum', 'eval',
    'export', 'extends', 'false', 'final',
    'finally', 'float', 'for', 'function',
    'goto', 'if', 'implements', 'import',
    'in', 'instanceof', 'int', 'interface',
    'let', 'long', 'native', 'new',
    'null', 'package', 'private', 'protected',
    'public', 'return', 'short', 'static',
    'super', 'switch', 'synchronized', 'this',
    'throw', 'throws', 'transient', 'true',
    'try', 'typeof', 'var', 'void', 'undefined',
    'volatile', 'while', 'with', 'yield', None
}