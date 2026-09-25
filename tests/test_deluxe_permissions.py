"""Static regression checks for shared head-chef controls; not an in-game test."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {lang: (ROOT / f'{lang}_deluxe.ow').read_text(encoding='utf-8') for lang in ('kr', 'en', 'jp')}


def rule(source, name):
    start = source.index(f'rule("{name}")')
    end = source.find('\nrule(', start + 1)
    return source[start:end if end != -1 else len(source)]


def normalized(source):
    return re.sub(r'\s+', ' ', re.sub(r'"(?:\\.|[^"\\])*"', '"TEXT"', source)).strip()


class HeadChefControlsTests(unittest.TestCase):
    def test_text_cleanup_visits_each_scalar_id(self):
        # Array arguments are not a bulk-delete contract. Verify exact ranges
        # and that the intro scratch index is consumed before progress loading.
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                mode = rule(source, 'Head Chefs: Select Mode')
                spawn = rule(source, 'Player: Spawn')
                patterns = (
                    (mode, r'For Global Variable\(scbRank, False, (\d+), True\);\s*Destroy HUD Text\(Global.globalText\[Global.scbRank\]\);\s*End;', 0, [0, 1, 2, 3, 4]),
                    (spawn, r'For Player Variable\(Event Player, progressIndex, 3, (\d+), True\);\s*Destroy In-World Text\(Event Player.tableText\[Event Player.progressIndex\]\);\s*End;', 3, [3, 4, 5, 6]),
                    (spawn, r'For Player Variable\(Event Player, progressIndex, False, (\d+), True\);\s*Destroy HUD Text\(Event Player.tableText\[Event Player.progressIndex\]\);\s*End;', 0, [0, 1, 2]),
                )
                for block, pattern, start, expected in patterns:
                    match = re.search(pattern, block)
                    self.assertIsNotNone(match)
                    self.assertEqual(list(range(start, int(match[1]))), expected)
                self.assertNotRegex(mode + spawn, r'Destroy (?:HUD|In-World) Text\(Array Slice')
                self.assertLess(spawn.rindex('For Player Variable(Event Player, progressIndex'), spawn.index('Call Subroutine(loadProgress);'))
                self.assertLess(spawn.index('Call Subroutine(loadProgress);'), spawn.index('Start Rule(saveProgress,'))

    def test_same_control_logic_in_all_locales(self):
        for name in ('Head Chefs: Select Mode', 'Head Chefs: Select Permission', 'Head Chefs: Set Permission'):
            reference = normalized(rule(SOURCES['kr'], name))
            for lang, source in SOURCES.items():
                with self.subTest(lang=lang, rule=name):
                    self.assertEqual(normalized(rule(source, name)), reference)

    def test_global_mode_has_no_event_player_or_fixed_host(self):
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                mode = rule(source, 'Head Chefs: Select Mode')
                self.assertIn('Subroutine;\n\t\tselectMode;', mode)
                self.assertNotIn('Event Player', mode)
                self.assertNotIn('Host Player', mode)
                candidate = mode[mode.index('Global.scbRank ='):mode.index('Loop If(')]
                self.assertIn('Filtered Array(All Players(Team 1), Current Array Element.permission == 3', candidate)
                for button in ('Ability 2', 'Reload', 'Jump'):
                    self.assertIn(f'Is Button Held(Current Array Element, Button({button}))', candidate)
                # Yield before retrying absent input; a missing chef cannot fall through to confirm.
                self.assertLess(mode.index('Wait(0.016, Ignore Condition);'), mode.index('Global.scbRank ='))
                self.assertLess(mode.index('Loop If(!Entity Exists(Global.scbRank));'), mode.index('Destroy HUD Text('))
                release_wait = mode[mode.index('Wait Until('):mode.index('99999);')]
                self.assertIn('!Entity Exists(Global.scbRank)', release_wait)
                self.assertIn('Global.scbRank.permission != 3', release_wait)
                self.assertEqual(mode.count('Destroy HUD Text('), 1)
                self.assertNotIn('createItem', mode)

    def test_targets_and_authorization_are_per_player(self):
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                self.assertNotIn('Global.selectPlayer', source)
                variables = source[:source.index('\nsubroutines')]
                self.assertNotIn('selectPlayer', variables.split('player:')[0])
                self.assertIn('56: selectPlayer', variables.split('player:')[1])
                for name in ('Head Chefs: Select Permission', 'Head Chefs: Set Permission'):
                    block = rule(source, name)
                    self.assertIn('Ongoing - Each Player;\n\t\tTeam 1;', block)
                    conditions = block.split('conditions', 1)[1].split('actions', 1)[0]
                    self.assertIn('Event Player.permission == 3;', conditions)
                    self.assertIn('Global.stageTime != False;', conditions)
                    self.assertNotIn('Host Player', block)
                targeting = rule(source, 'Head Chefs: Select Permission')
                self.assertIn('Player Closest To Reticle(Event Player, All Teams)', targeting)
                self.assertIn('Is Dummy Bot(Event Player.selectPlayer)', targeting)
                self.assertIn('Distance Between(Event Player, Event Player.selectPlayer) > 5', targeting)
                self.assertIn('Wait(0.250, Abort When False);', targeting)

    def test_practice_transaction_does_not_yield_before_item_creation(self):
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                controls = rule(source, 'Head Chefs: Set Permission')
                self.assertIn('Is Button Held(Event Player, Button(Ability 2)) == True;', controls)
                self.assertIn('Event Player.selectPlayer.permission = (Event Player.selectPlayer.permission + True) % 3;', controls)
                start = controls.index('Else If(Global.difficulty == 4);')
                end = controls.index('Call Subroutine(createItem);')
                self.assertNotIn('Wait', controls[start:end])
                self.assertNotIn('Wait', rule(source, 'Global subroutine: Create item (position, velocity, code, cooker)'))
                self.assertEqual(controls.count('Wait(3, Abort When False);'), 2)
                self.assertNotIn('Distance Between', controls)  # no new practice spawn distance restriction

    def test_mode_completion_gate_is_set_after_data_init(self):
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                setup = rule(source, 'Global: Setting')
                self.assertLess(setup.index('Call Subroutine(selectMode);'), setup.index('Call Subroutine(dataInit);'))
                self.assertLess(setup.index('Call Subroutine(dataInit);'), setup.index('Global.stageTime ='))
                self.assertEqual(len(re.findall(r'Global\.stageTime\s*=', source)), 1)
                # Startup lock is still per-player; the redundant host lock is gone.
                self.assertNotIn('Set Status(Host Player', source)
                spawn = rule(source, 'Player: Spawn')
                self.assertIn('Set Status(Event Player, Null, Rooted, 9999);', spawn)
                self.assertIn('Clear Status(Event Player, Rooted);', spawn)

    def test_host_references_only_remain_for_bootstrap_and_role_assignment(self):
        for lang, source in SOURCES.items():
            with self.subTest(lang=lang):
                uses = [line.strip() for line in source.splitlines() if 'Host Player' in line]
                self.assertEqual(len(uses), 5)
                self.assertTrue(all(line.startswith(('Create Dummy Bot(', 'Event Player.permission =', 'If(Slot Of(Host Player)', 'Host Player.permission =')) for line in uses))
                setup = rule(source, 'Global: Setting')
                self.assertIn('Local Player.permission == 3 && Local Player.selectPlayer != Null ? Local Player : Null', setup)
                self.assertEqual(setup.count('Local Player.permission == 3 ?'), 2)


if __name__ == '__main__':
    unittest.main()
