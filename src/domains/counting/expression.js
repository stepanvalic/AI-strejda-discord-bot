function tokenize(input) {
  const tokens = [];
  const regex = /\s*(0x[0-9a-f]+|0b[01]+|0o[0-7]+|\d+|[()+\-*/])\s*/giy;
  let lastIndex = 0;

  while (lastIndex < input.length) {
    regex.lastIndex = lastIndex;
    const match = regex.exec(input);

    if (!match || match.index !== lastIndex) {
      throw new Error('Neplatný výraz.');
    }

    tokens.push(match[1]);
    lastIndex = regex.lastIndex;
  }

  return tokens;
}

function tokenToNumber(token) {
  if (token.startsWith('0x')) {
    return Number.parseInt(token, 16);
  }

  if (token.startsWith('0b')) {
    return Number.parseInt(token.slice(2), 2);
  }

  if (token.startsWith('0o')) {
    return Number.parseInt(token.slice(2), 8);
  }

  return Number.parseInt(token, 10);
}

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.index = 0;
  }

  parse() {
    const value = this.parseExpression();

    if (this.index < this.tokens.length) {
      throw new Error('Nečekaný token.');
    }

    if (!Number.isFinite(value) || !Number.isInteger(value)) {
      throw new Error('Counting podporuje jen celá čísla.');
    }

    return value;
  }

  parseExpression() {
    let value = this.parseTerm();

    while (this.peek() === '+' || this.peek() === '-') {
      const operator = this.consume();
      const right = this.parseTerm();
      value = operator === '+' ? value + right : value - right;
    }

    return value;
  }

  parseTerm() {
    let value = this.parseFactor();

    while (this.peek() === '*' || this.peek() === '/') {
      const operator = this.consume();
      const right = this.parseFactor();
      value = operator === '*' ? value * right : value / right;
    }

    return value;
  }

  parseFactor() {
    const token = this.peek();

    if (token === '+' || token === '-') {
      this.consume();
      const value = this.parseFactor();
      return token === '-' ? -value : value;
    }

    if (token === '(') {
      this.consume();
      const value = this.parseExpression();

      if (this.consume() !== ')') {
      throw new Error('Chybí závorka.');
      }

      return value;
    }

    if (!token) {
      throw new Error('Nečekaný konec výrazu.');
    }

    this.consume();
    return tokenToNumber(token);
  }

  peek() {
    return this.tokens[this.index];
  }

  consume() {
    return this.tokens[this.index++];
  }
}

export function parseCountingExpression(input) {
  const tokens = tokenize(input.trim());
  const parser = new Parser(tokens);
  return parser.parse();
}
