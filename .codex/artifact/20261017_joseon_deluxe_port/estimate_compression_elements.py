"""Read-only expression-cost estimate, not an in-game Workshop measurement.

Model: https://github.com/Zezombye/overpy/wiki/Element-saving-techniques
Only compares the four numeric/string data rules; no hero-literal adjustments
are needed in those rules. Unchanged runtime rules are outside this estimate.
"""

import subprocess
import sys

from read_tables import ROOT, Expr, rule

sys.path.insert(0, str(ROOT))
from scripts.check_ow_syntax import Parser


def cost(node):
    kind = node[0]
    if kind == 'literal':
        return 2 if type(node[1]) in (int, float) else 1
    if kind == 'name':
        return 2 if node[1].startswith('Global.') else 1
    if kind == 'call':
        name, args = node[1:]
        base = 2 if name in ('Array', 'Evaluate Once') or name.startswith('Workshop Setting') else 1
        result = base + sum(cost(arg) for arg in args)
        if name == 'Custom String':
            result += max(0, 4 - len(args))
        return result
    if kind == 'index':
        return 1 + cost(node[1]) + cost(node[2])
    if kind == 'binary':
        return 1 + cost(node[2]) + cost(node[3])
    if kind == 'ternary':
        return 1 + sum(cost(arg) for arg in node[1:])
    raise ValueError(kind)


def expression(text):
    parser = Expr(text)
    result = parser.parse()
    assert parser.i == len(parser.tokens)
    return result


def rule_cost(block):
    body = block.split('\n\tactions\n\t{\n', 1)[1].rsplit('\n\t}', 1)[0]
    tokens = Parser(body).tokens
    start, result = 0, 1
    for token in tokens:
        if token.kind != 'symbol' or token.value != ';':
            continue
        statement = body[start:token.offset].strip()
        start = token.offset + 1
        if statement.startswith('Global.') and '=' in statement:
            left, right = statement.split('=', 1)
            target = expression(left.strip())
            result += cost(expression(right.strip()))
            if target[0] == 'index':
                result += cost(target[2]) - 1
        else:
            node = expression(statement)
            result += 1 + sum(cost(arg) - 1 for arg in node[2]) if node[0] == 'call' else 1
    return result


if __name__ == '__main__':
    baseline = subprocess.check_output(
        ['git', 'show', '2716010:Joseon_deluxe.ow'], cwd=ROOT, text=True)
    current = (ROOT / 'Joseon_deluxe.ow').read_text()
    saved = 0
    for edition in ('N3', 'CAFE'):
        for part in (1, 2):
            title = f'Global subroutine: Deluxe {edition} init{part}'
            before = rule_cost(rule(baseline, title))
            after = rule_cost(rule(current, title))
            saved += before - after
            print(title, before, after, 'saved', before - after)
    print('ESTIMATED_SAVED_ELEMENTS', saved)
    print('PROJECTED_FROM_USER_REPORTED_33715', 33715 - saved)
