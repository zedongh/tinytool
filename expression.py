from enum import Enum

class TokenType(Enum):
    ADD = 0
    MINUS = 1
    STAR = 2
    SLASH = 3
    LEFT_PAREN = 4
    RIGHT_PAREN = 5
    BANG = 6
    POWER = 7
    NUMBER = 8
    EOF = 9
    LEFT_BRACE = 10
    RIGHT_BRACE = 11
    LEFT_SQUARE = 12
    RIGHT_SQUARE = 13

class Assoc(Enum):
    LEFT = 0
    RIGHT = 1

class Scanner:

    def __init__(self, source):
        self._source = source
        self._start = 0
        self._current = 0
        # self._column = 1
        self._tokens = []

    def _advance(self):
        if self._isAtEnd():
            return '\0'
        else:
            ch = self._source[self._current]
            self._current += 1
            return ch

    def scanTokens(self):
        while not self._isAtEnd():
            self._start = self._current
            self._scanToken()
        self._tokens.append((TokenType.EOF, None))
        return self._tokens

    def _scanToken(self):
        ch = self._advance()
        if ch == '+':
            self._tokens.append((TokenType.ADD, None))
        elif ch == '-':
            self._tokens.append((TokenType.MINUS, None))
        elif ch == '*':
            self._tokens.append((TokenType.STAR, None))
        elif ch == '/':
            self._tokens.append((TokenType.SLASH, None))
        elif ch == '!':
            self._tokens.append((TokenType.BANG, None))
        elif ch == '(':
            self._tokens.append((TokenType.LEFT_PAREN, None))
        elif ch == '[':
            self._tokens.append((TokenType.LEFT_SQUARE, None))
        elif ch == '{':
            self._tokens.append((TokenType.LEFT_BRACE, None))
        elif ch == ')':
            self._tokens.append((TokenType.RIGHT_PAREN, None))
        elif ch == ']':
            self._tokens.append((TokenType.RIGHT_SQUARE, None))
        elif ch == '}':
            self._tokens.append((TokenType.RIGHT_BRACE, None))
        elif ch == '^':
            self._tokens.append((TokenType.POWER, None))
        elif ch.isdigit():
            while not self._isAtEnd() and self._peek().isdigit():
                self._advance()
            if self._peek() == '.' and self._peekNext().isdigit():
                self._advance() # consume '.'
                while self._peek().isdigit():
                    self._advance()
            num = float(self._source[self._start:self._current])
            if num == int(num):
                num = int(num)
            self._tokens.append((TokenType.NUMBER, num))
        elif ch not in ' \t\r':
            raise ValueError("Unknown Charater")

    def _peekNext(self):
        return '\0' if self._current + 1 >= len(self._source) else self._source[self._current + 1]

    def _isAtEnd(self):
        return self._current >= len(self._source)
    
    def _peek(self):
        return '\0' if self._isAtEnd() else self._source[self._current]

Unary = {
    TokenType.MINUS: 4,
    TokenType.ADD: 4,
    TokenType.BANG: 7
}

Binary = {
    TokenType.ADD: (Assoc.LEFT, 3),
    TokenType.MINUS: (Assoc.LEFT, 3),
    TokenType.STAR: (Assoc.LEFT, 5),
    TokenType.SLASH: (Assoc.LEFT, 5),
    TokenType.POWER: (Assoc.RIGHT, 6)
}

class Parser:

    def __init__(self, tokens):
        self._current = 0
        self._tokens = tokens
        pass

    def parse(self):
        ast = self._exp(0)
        if self._peek()[0] != TokenType.EOF:
            raise ValueError("Syntax Error")
        return ast

    def _exp(self, pred):
        exp = self._p()
        while self._peek()[0] in Binary and Binary[self._peek()[0]][1] >= pred:
            bin_tok = self._advance()
            op = bin_tok[0]
            assoc = Binary[op][0]
            q = Binary[op][1] + 1  if assoc == Assoc.LEFT else Binary[op][1]
            right = self._exp(q)
            exp = (op, exp, right)
        return exp

    def _p(self):
        if self._peek()[0] in Unary:
            tok = self._advance()
            pred = Unary[tok[0]]
            return (tok[0], self._exp(pred))
        elif self._peek()[0] == TokenType.LEFT_PAREN:
            self._advance()
            tree = self._exp(0)
            if self._peek()[0] == TokenType.RIGHT_PAREN:
                self._advance()
                return tree
            else:
                raise ValueError("Syntax Error: Lack ')' Token")
        elif self._peek()[0] == TokenType.LEFT_SQUARE:
            self._advance()
            tree = self._exp(0)
            if self._peek()[0] == TokenType.RIGHT_SQUARE:
                self._advance()
                return tree
            else:
                raise ValueError("Syntax Error: Lack ']' Token")
        elif self._peek()[0] == TokenType.LEFT_BRACE:
            self._advance()
            tree = self._exp(0)
            if self._peek()[0] == TokenType.RIGHT_BRACE:
                self._advance()
                return tree
            else:
                raise ValueError("Syntax Error: Lack '}' Token")
        elif self._peek()[0] == TokenType.NUMBER:
            num = self._advance()
            return num[1]
        else:
            raise ValueError()
        

    def _peek(self):
        return self._tokens[-1] if self._current >= len(self._tokens) else self._tokens[self._current]

    def _advance(self):
        if self._current >= len(self._tokens):
            return self._tokens[-1]
        else:
            tok = self._tokens[self._current]
            self._current += 1
            return tok

class Interpreter:

    def __init__(self, ast):
        self._ast = ast

    def interpret(self):
        # Tree Walker
        def tree_walker(tree):
            if type(tree) is not tuple:
                return tree
            elif tree[0] in Unary and len(tree) == 2:
                tb = {
                    TokenType.MINUS: - tree_walker(tree[1]),
                    TokenType.ADD: tree_walker(tree[1])
                }
                return tb[tree[0]]
            elif tree[0] in Binary:
                tb = {
                    TokenType.ADD: tree_walker(tree[1]) + tree_walker(tree[2]),
                    TokenType.MINUS: tree_walker(tree[1]) - tree_walker(tree[2]),
                    TokenType.STAR: tree_walker(tree[1]) * tree_walker(tree[2]),
                    TokenType.SLASH: tree_walker(tree[1]) / tree_walker(tree[2]),
                    TokenType.POWER: tree_walker(tree[1]) ** tree_walker(tree[2])
                }
                return tb[tree[0]]
        return tree_walker(ast)


if __name__ == "__main__":
    while True:
        source = input()
        scanner = Scanner(source)
        #try:
        tokens = scanner.scanTokens()
        print("Tokens:")
        [print(x) for x in tokens]
        parser = Parser(tokens)
        ast = parser.parse()
        print("AST:")
        print(ast)
        interpreter = Interpreter(ast)
        result = interpreter.interpret()
        print(f'result = {result}')
        #except ValueError:
        #    print("Invaild Syntax")
