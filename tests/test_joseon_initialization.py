"""Static checks for original-compatible initialization waits."""

from pathlib import Path
import re
import unittest

from scripts.check_ow_syntax import Parser


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'Joseon_deluxe.ow').read_text(encoding='utf-8')
REFERENCE = (ROOT / 'kr_deluxe.ow').read_text(encoding='utf-8')


def rule(source, name):
    start = source.index(f'rule("{name}")')
    end = source.find('\nrule(', start + 1)
    return source[start:end if end != -1 else len(source)]


def wait_boundaries(block):
    start = 0
    field = None
    result = []
    for token in Parser(block).tokens:
        if token.kind != 'symbol' or token.value != ';':
            continue
        statement = block[start:token.offset + 1]
        start = token.offset + 1
        assignment = re.search(r'Global\.([A-Z_]+)(?:\[\d+\])?\s*=', statement)
        if assignment:
            field = assignment[1]
        if statement.strip().startswith('Wait('):
            result.append((field, statement.strip()))
    return result


class JoseonInitializationTests(unittest.TestCase):
    def test_table_waits_match_corresponding_original_editions(self):
        for edition, reference in (('N3', 'GC'), ('CAFE', 'CAFE')):
            for part in (1, 2):
                with self.subTest(edition=edition, part=part):
                    actual = wait_boundaries(rule(SOURCE, f'Global subroutine: Deluxe {edition} init{part}'))
                    expected = wait_boundaries(rule(REFERENCE, f'Global subroutine: Deluxe {reference} init{part}'))
                    # The port already moved its numeric lookup before metadata.
                    if part == 1:
                        expected = [('ITEM_SCORE' if field == 'MIXING_RECIPE' else field, wait)
                                    for field, wait in expected]
                    self.assertEqual(actual, expected)

    def test_mixing_loop_retains_original_counter_and_no_extra_wait(self):
        block = rule(SOURCE, 'Global subroutine: Deluxe dispatcher dataInit')
        self.assertIn('For Global Variable(checkingIndex, False, Count Of(Global.RAW_MIX), True);', block)
        self.assertNotIn('Wait(', block)
        self.assertNotIn('dataInitIndex', SOURCE)
        self.assertEqual(block.count('Modify Global Variable At Index(MIXING_'), 4)

    def test_stock_and_customer_loops_match_original(self):
        for edition, reference in (('N3', 'GC'), ('CAFE', 'CAFE')):
            actual = rule(SOURCE, f'Global subroutine: Deluxe {edition} init3')
            expected = rule(REFERENCE, f'Global subroutine: Deluxe {reference} init3')
            start = 'For Global Variable(RAW_RESULT, False, Count Of(Global.DELUXE_DATA[2]), True);'
            stop = 'Global.DELUXE_DATA[2] = Global.RAW_MIX;'
            self.assertEqual(actual[actual.index(start):actual.index(stop)],
                             expected[expected.index(start):expected.index(stop)])
        name = 'Global subroutine: Deluxe common customer init'
        self.assertEqual(rule(SOURCE, name), rule(REFERENCE, name))

    def test_readiness_and_tutorial_menu_lock_are_preserved(self):
        setup = rule(SOURCE, 'Global: Setting')
        self.assertLess(setup.index('Call Subroutine(dataInit);'), setup.index('Global.stageTime ='))
        self.assertEqual(len(re.findall(r'Global\.stageTime\s*=', SOURCE)), 1)
        menu = rule(SOURCE, 'Global subroutine: Menu init')
        self.assertIn('Global.totalScore[False] = Global.stage == 0 ? 0 :', menu)


if __name__ == '__main__':
    unittest.main()
