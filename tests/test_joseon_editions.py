"""Static edition-selection regression checks; not an in-game test."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'Joseon_deluxe.ow').read_text(encoding='utf-8')


def rule(name):
    start = SOURCE.index(f'rule("{name}")')
    end = SOURCE.find('\nrule(', start + 1)
    return SOURCE[start:end if end != -1 else len(SOURCE)]


class JoseonEditionTests(unittest.TestCase):
    def test_deluxe_declaration_indentation(self):
        for edition in ('kr', 'en', 'jp', 'Joseon'):
            with self.subTest(edition=edition):
                source = (ROOT / f'{edition}_deluxe.ow').read_text(encoding='utf-8')
                header = source.splitlines()[:231]
                self.assertFalse(any(re.match(r'^ +\d+:', line) for line in header))
                for index in (16, 129, 170, 171, 172):
                    self.assertRegex(header[index], r'^\t\t\d+:')

    def test_initial_selection_cycles_two_editions_and_six_modes(self):
        selection = rule('Head Chefs: Select Mode')
        self.assertIn('Global.stageMode = Array(0, 0);', SOURCE)
        edition = re.search(r'Global.stageMode\[False\] = .* % (\d+);', selection)
        mode = re.search(r'Global.stageMode\[True\] = .* % (\d+);', selection)
        self.assertEqual(int(edition[1]), 2)
        self.assertEqual(int(mode[1]), 6)
        for initial in range(2):
            current = initial
            visited = []
            for _ in range(4):
                current = (current + 1) % int(edition[1])
                visited.append(current)
            self.assertEqual(set(visited), {0, 1})

    def test_only_two_editions_are_dispatched(self):
        dispatcher = rule('Global subroutine: Deluxe dispatcher dataInit')
        for part in range(1, 4):
            self.assertIn(f'Call Subroutine(dataInit_n3{part});', dispatcher)
            self.assertIn(f'Call Subroutine(dataInit_cafe{part});', dispatcher)
        stage = rule('Global subroutine: Start stage')
        for edition in ('n3', 'cafe'):
            self.assertIn(f'Call Subroutine(dataInit_{edition}3);', stage)
        self.assertNotRegex(SOURCE, r'Call Subroutine\(dataInit_gc[123]\)')
        for part in range(1, 4):
            self.assertIn(f'dataInit_gc{part};', rule(f'Global subroutine: Deluxe GC init{part}'))

    def test_practice_cycle_matches_internal_and_external_targets(self):
        reload = rule('Player: Reload button')
        count = int(re.search(r'Global.totalScore\[False\] = .* % (\d+);', reload)[1])
        self.assertEqual(count, 4)
        setup = rule('Global: Setting')
        labels = re.search(r'Global.stage == 5 \? String Split\(Custom String\("([^"]+)"\)', setup)[1].split('/')
        self.assertEqual(len(labels), count)
        switch = rule('Global subroutine: Other Menu')
        limit = int(re.search(r'If\(Global.totalScore\[False\] <= (\d+)\);', switch)[1])
        self.assertEqual(limit, 1)
        arrays = re.findall(r'Array\((Null, Null, Custom String\([^\n]+)\)\[Global.totalScore\[False\]\]', switch)
        self.assertEqual(len(arrays), 2)
        targets = [[None, None] + re.findall(r'Custom String\("([^"]+)"\)', array) for array in arrays]
        self.assertEqual(targets[0][2:], labels[2:])
        self.assertEqual(targets[1], [None, None, 'SPXXM', '8MAAN'])
        self.assertEqual([i for i in range(count) if i <= limit], [0, 1])
        self.assertIn('Global.stageMode[0] = Global.totalScore[False];', switch)
        self.assertLess(switch.index('Call Subroutine(dataInit);'), switch.index('Call Subroutine(menuInit);'))
        self.assertIn('Global.stage = 0;', switch)

    def test_display_lists_match_active_editions(self):
        expected = '\ub274 3\ud638\uc810/\ub274 \uce74\ud398'
        labels = re.findall(r'String Split\(Custom String\("([^"]+)"\), Custom String\("/"\)\)\[Global.stageMode\[0\]\]', SOURCE)
        self.assertEqual(labels.count(expected), 3)
        self.assertEqual(len(labels), 4)
        credits = next(label for label in labels if label != expected).split('/')
        self.assertEqual(len(credits), 2)
        self.assertTrue(all(credit.startswith('Joseon') for credit in credits))
        self.assertNotIn('\ucfe1\uc81c\uc694\ub9ac', SOURCE)
        setup = rule('Global: Setting')
        self.assertIn('Array(Color(Orange), Custom Color(100, 60, False, 255))[Global.stageMode[0]]', setup)

    def test_edition_assignments_have_no_other_entry_path(self):
        assignments = re.findall(r'Global.stageMode(?:\[(?:0|False)\])?\s*=(?!=)\s*([^;]+);', SOURCE)
        self.assertEqual(assignments, [
            'Array(0, 0)',
            '(Global.stageMode[False] + Is Button Held(Global.scbRank, Button(Ability 2))) % 2',
            'Global.totalScore[False]',
        ])


if __name__ == '__main__':
    unittest.main()
