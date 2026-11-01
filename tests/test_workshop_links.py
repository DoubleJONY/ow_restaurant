"""Static Workshop branding and external-menu index checks."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def rule(source, name):
    start = source.index(f'rule("{name}")')
    end = source.find('\nrule(', start + 1)
    return source[start:end if end != -1 else len(source)]


class WorkshopLinkTests(unittest.TestCase):
    def test_joseon_resolved_workshop_branding(self):
        source = (ROOT / 'Joseon_deluxe.ow').read_text(encoding='utf-8')
        self.assertNotIn('Joseon Deluxe', source)
        self.assertNotIn('\ubbf8\uc815', source)
        self.assertIn('\ub808\uc2a4\ud1a0\ub791(WM3MW) v', source)
        self.assertIn('\ub808\uc2a4\ud1a0\ub791(WM3MW)\\r\\nJoseon#31496', source)
        self.assertIn('\uc5c5\ub370\uc774\ud2b8 \ud544\uc694! - \ucf54\ub4dc : WM3MW', source)

    def test_kr_external_menu_cycle_and_code_alignment(self):
        source = (ROOT / 'kr_deluxe.ow').read_text(encoding='utf-8')
        setup = rule(source, 'Global: Setting')
        labels = re.search(r'Global.stage == 5 \? String Split\(Custom String\("([^"]+)"\)', setup)[1].split('/')
        self.assertEqual(labels[:4], [
            '\ubaa8\ub4ec\ud68c\ubc25!', '\uce74\ud398!', '\ucfe1\uc81c\uc694\ub9ac', '\ud5ec\uc2a4\ud1a0\ub791!',
        ])
        reload = rule(source, 'Player: Reload button')
        count = int(re.search(r'Global.totalScore\[False\] = .* % (\d+);', reload)[1])
        self.assertEqual(count, 5)
        self.assertEqual(len(labels), count)
        switch = rule(source, 'Global subroutine: Other Menu')
        self.assertIn('If(Global.totalScore[False] <= 2);', switch)
        arrays = re.findall(r'Array\((Null, Null, Null, Custom String\([^\n]+)\)\[Global.totalScore\[False\]\]', switch)
        self.assertEqual(len(arrays), 2)
        targets = [re.findall(r'Custom String\("([^"]+)"\)', array) for array in arrays]
        self.assertEqual(targets[0], labels[3:])
        self.assertEqual(targets[1], ['WM3MW', '8MAAN'])


if __name__ == '__main__':
    unittest.main()
