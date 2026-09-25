import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_ow_syntax import SyntaxFailure, check


ROOT = Path(__file__).resolve().parents[1]


def rule(actions):
    return 'rule("한국어 日本語") { event { Ongoing - Global; } actions {' + actions + '} }'


class SyntaxTests(unittest.TestCase):
    def test_valid_expressions(self):
        check(rule('''
            "label with } and escaped \\" quotation" disabled Wait(1, Ignore Condition);
            // ignored } ;
            /* ignored " */
            Global.a[0] = True ? Array(1, -2)[0] : (3 + 4) * 5;
            If(True); Else If(False); Else; End;
            Icon String(Arrow: Up); Hero(Soldier: 76); Button(Ability 2);
        '''), True)

    def test_implicit_end(self):
        check(rule('If(True); Wait(1, Ignore Condition);'), True)

    def test_declarations_and_disabled_rule(self):
        check('variables { global: 0: a player: 0: a } subroutines { 0: run } disabled ' + rule(''))

    def test_bad_inputs(self):
        for source in [rule('Wait(1)'), rule('Wait(,1);'), rule('Wait(1,);'),
                       rule('Global.a = ;'), rule('Global.a = 1 + ;'),
                       rule('Global.a[0) = 1;'), rule('"unterminated'),
                       rule('/* unterminated'), rule('Wait(1);') + '}',
                       'rule("x") { actions {} }', 'rule("x") { event {} }',
                       'variables { global: 0: a 0: b }',
                       'variables { global: 0: a 1: a }',
                       'settings {}', '', rule('Wait(1) Wait(2);')]:
            with self.subTest(source=source), self.assertRaises(SyntaxFailure):
                check(source)

    def test_optional_control_lint(self):
        for action in ['End;', 'Else;', 'If(True); Else; Else If(True);']:
            with self.subTest(action=action), self.assertRaises(SyntaxFailure):
                check(rule(action), True)
        check(rule('End;'))  # default checks syntax, not control-flow semantics

    def test_error_location(self):
        with self.assertRaisesRegex(SyntaxFailure, r'^2:1:'):
            check('variables {\n@\n}')

    def test_cli_read_only_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.ow'
            original = ('\ufeff' + rule('Wait(1);')).encode('utf-8')
            path.write_bytes(original)
            command = [sys.executable, str(ROOT / 'scripts/check_ow_syntax.py')]
            result = subprocess.run(command + [directory], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_bytes(), original)
            path.write_text(rule('Wait(1)'), encoding='utf-8')
            self.assertEqual(subprocess.run(command + [str(path)], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run(command + [str(path) + '.missing'], capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
