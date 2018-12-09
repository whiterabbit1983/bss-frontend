import ast
from functools import reduce


class OneLiner:
    def __init__(self, res):
        self._res = res

    def __call__(self, node, **kwargs):
        return self._res


class Translator:
    def __init__(self):
        self._env = {}
        self.defs = {}

    visit_None = OneLiner('null')
    visit_Add = visit_UAdd = OneLiner('+')
    visit_Sub = visit_USub = OneLiner('-')
    visit_Mult = OneLiner('*')
    visit_Div = OneLiner('/')
    visit_Lt = OneLiner('<')
    visit_LtE = OneLiner('<=')
    visit_Gt = OneLiner('>')
    visit_GtE = OneLiner('>=')
    visit_Eq = OneLiner('==')
    visit_NotEq = OneLiner('!=')
    visit_Not = OneLiner('not')

    def _map_visit(self, lst, **kwargs):
        return list(map(lambda x: self.visit(x), lst))

    def visit_Module(self, node):
        def _reduce_func(a, v):
            res = self.visit(v)
            return a + [res] if res else a
        return reduce(_reduce_func, node.body, [])

    # TODO: implement loops
    # def visit_For(self, node, **kwargs):
    #     raise NotImplementedError('For is not implemented yet')

    # def visit_While(self, node, **kwargs):
    #     raise NotImplementedError('While is not implemented yet')

    def visit_Str(self, node, **kwargs):
        return ['v', node.s]

    def visit_arguments(self, node, **kwargs):
        return self._map_visit(node.args, **kwargs)

    def visit_arg(self, node, **kwargs):
        return node.arg

    def visit_FunctionDef(self, node, **kwargs):
        self.defs[node.name] = {
            'args': self.visit(node.args, **kwargs),
            'e': self._map_visit(node.body, **kwargs)
        }

    def visit_BinOp(self, node, **kwargs):
        return [self.visit(node.op), self.visit(node.left), self.visit(node.right)]

    def visit_UnaryOp(self, node, **kwargs):
        return self._map_visit([node.op, node.operand], **kwargs)

    def visit_Compare(self, node, **kwargs):
        def _reduce_func(a, v):
            a[-1][-1]
            return a + [[self.visit(v[0]), a[-1][-1], self.visit(v[1])]]

        exprs = zip(node.ops, node.comparators)
        res = reduce(_reduce_func, exprs, [self.visit(node.left)])
        if len(res) > 2:
            res[0] = 'and'
        else:
            res = res[-1]
        return res

    def visit_If(self, node, **kwargs):
        return [
            'if', 
            self.visit(node.test), 
            [self.visit(expr) for expr in node.body],
            [self.visit(expr) for expr in node.orelse]
        ]

    def visit_Return(self, node, **kwargs):
        if node.value is None:
            return 'null'
        return self.visit(node.value, **kwargs)

    def visit_Expr(self, node, **kwargs):
        return self.visit(node.value, **kwargs)

    def visit_Name(self, node, **kwargs):
        if isinstance(node.ctx, ast.Load) and node.id in self._env:
            return self.visit(self._env[node.id])
        return node.id

    def visit_Num(self, node, **kwargs):
        return ['v', node.n]

    def visit_Call(self, node, **kwargs):
        args = [self.visit(a) for a in node.args]
        if isinstance(node.func, ast.Name):
            return [node.func.id] + args
        else:
            return self.visit(node, **kwargs) + args

    def visit_Tuple(self, node, **kwargs):
        return ['tuple'] + [self.visit(elt, **kwargs) for elt in node.elts]

    def visit_List(self, node, **kwargs):
        return ['list'] + [self.visit(elt, **kwargs) for elt in node.elts]

    def visit_Assign(self, node, **kwargs):
        lvalue = node.targets[0]
        if isinstance(lvalue, ast.Tuple):
            raise NotImplementedError('Multiple assignment is not implemented yet')
        elif isinstance(lvalue, ast.Name):
            self._env[lvalue.id] = node.value
        return 'nop'

    def visit(self, node, **kwargs):
        meth = getattr(self, f'visit_{node.__class__.__name__}', None)
        if meth:
            return meth(node, **kwargs)
        raise NotImplementedError(f'{node.__class__.__name__} is not implemented yet')


def compile(expression):
    translator = Translator()
    return {'e': translator.visit(ast.parse(expression)), 'g': translator.defs}


if __name__ == '__main__':
    # test
    print(compile('if 1 > x < 2: return 2'))
