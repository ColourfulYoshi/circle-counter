import ast
import operator


class Evaluator(ast.NodeVisitor):
    def __init__(self, variables, functions):
        self.vars = variables
        self.funcs = functions

        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.FloorDiv: operator.floordiv
        }

    def set_vars(self, variables):
        self.vars = variables

    def set_funcs(self, functions):
        self.funcs = functions

    def eval(self, expression):
        try:
            tree = ast.parse(expression, mode="eval")
            return self.visit(tree.body)
        except Exception as e:
            return str(e)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self.operators[type(node.op)](left, right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        return self.operators[type(node.op)](operand)

    def visit_Num(self, node):
        return node.n

    def visit_Constant(self, node):
        return node.value

    def visit_Name(self, node):
        if node.id in self.vars:
            return self.vars[node.id]
        return f"variable \"{node.id}\" is not defined"

    def visit_Call(self, node):
        func_name = node.func.id
        if func_name in self.funcs:
            args = [self.visit(arg) for arg in node.args]
            return self.funcs[func_name](*args)
        return f"operation \"{func_name}\" is not defined"

BASE_FORMULA = "round(t * ((p ** 2) / (a ** 2)))"
