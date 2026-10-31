"""Regression checks for original-style Workshop table compression."""

import importlib.util
import json
from pathlib import Path
import re
import unittest

from scripts.check_ow_syntax import Parser


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'joseon_tables', ROOT / '.codex/artifact/20261017_joseon_deluxe_port/read_tables.py')
tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tables)
SOURCE = (ROOT / 'Joseon_deluxe.ow').read_text(encoding='utf-8')


class JoseonCompressionTests(unittest.TestCase):
    def test_numeric_tables_use_split_lookup_and_sparse_overrides(self):
        for edition in ('N3', 'CAFE'):
            block = tables.rule(SOURCE, f'Global subroutine: Deluxe {edition} init1')
            block += tables.rule(SOURCE, f'Global subroutine: Deluxe {edition} init2')
            data = tables.load_tables(block)
            for name in ('CUTTING_RESULT', 'ADDITIONAL_MATERIAL_LIST', 'RAW_MIX'):
                with self.subTest(edition=edition, table=name):
                    node = tables.Expr(tables.assignment(block, name)).parse()
                    self.assertEqual(node[:2], ('call', 'Mapped Array'))
                    self.assertIn('Index Of Array Value(Global.MIXING_RECIPE, Current Array Element)',
                                  tables.assignment(block, name))
            for name in ('CUTTING_RESULT', 'ADDITIONAL_MATERIAL_LIST'):
                nested = {i: value for i, value in enumerate(data[name]) if isinstance(value, list)}
                overrides = re.findall(r'Global\.' + name + r'\[(\d+)\] = Array\(', block)
                self.assertEqual(set(map(int, overrides)), set(nested))
                self.assertTrue(nested)
            self.assertEqual(len(data['ITEM_NAME']), len(data['CUTTING_RESULT']))
            self.assertEqual(len(data['ITEM_NAME']), len(data['ADDITIONAL_MATERIAL_LIST']))

    def test_mixing_components_are_combined_before_final_results(self):
        for edition in ('N3', 'CAFE'):
            block = tables.rule(SOURCE, f'Global subroutine: Deluxe {edition} init2')
            combine = 'Global.RAW_MIX = Mapped Array(Global.RAW_MIX, Current Array Element * 1000 + Global.RAW_RESULT[Current Array Index]);'
            self.assertEqual(block.count(combine), 1)
            self.assertEqual(len(re.findall(r'Global\.RAW_RESULT =', block)), 2)
            self.assertLess(block.index('Global.RAW_RESULT ='), block.index(combine))
            self.assertLess(block.index(combine), block.rindex('Global.RAW_RESULT ='))

    def test_menu_rows_decode_to_numbers_and_string_segments_fit(self):
        for edition in ('N3', 'CAFE'):
            for part in (1, 2):
                block = tables.rule(SOURCE, f'Global subroutine: Deluxe {edition} init{part}')
                for token in Parser(block).tokens:
                    if token.kind == 'string':
                        self.assertLessEqual(len(json.loads(token.value)), 90)
                if part != 2:
                    continue
                for name in tables.MENU_FIELDS:
                    node = tables.Expr(tables.assignment(block, name)).parse()
                    self.assertEqual(node[:2], ('call', 'String Split'))
                    self.assertIn(f'For Global Variable(checkingIndex, False, Count Of(Global.{name}), True);', block)
                    self.assertIn(f'String Split(Global.{name}[Global.checkingIndex], Custom String(","))', block)


if __name__ == '__main__':
    unittest.main()
