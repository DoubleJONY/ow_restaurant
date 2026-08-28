#!/usr/bin/env python3
"""Assemble kr_deluxe.ow deterministically from the current Korean sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True
import build_deluxe_data as data_builder


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ko.ow"
TARGET = ROOT / "kr_deluxe.ow"
BUILD_DIR = ROOT / "build" / "kr_deluxe"


class BuildError(RuntimeError):
    pass


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise BuildError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def rule_span_by_title(text: str, title: str) -> tuple[int, int]:
    marker = f'rule("{title}")'
    start = text.find(marker)
    if start < 0:
        raise BuildError(f"rule not found: {title}")
    open_at = text.find("{", start + len(marker))
    end = data_builder.scan_balanced(text, open_at, "{", "}")
    return start, end


def rule_span_by_subroutine(text: str, subroutine: str) -> tuple[int, int]:
    event = re.search(rf"(?mi)^[ \t]+{re.escape(subroutine)};\r?$", text)
    if not event:
        raise BuildError(f"subroutine rule not found: {subroutine}")
    start = text.rfind('rule("', 0, event.start())
    if start < 0:
        raise BuildError(f"rule start not found: {subroutine}")
    open_at = text.find("{", start)
    end = data_builder.scan_balanced(text, open_at, "{", "}")
    return start, end


def modify_rule(text: str, title: str, transform: Callable[[str], str]) -> str:
    start, end = rule_span_by_title(text, title)
    return text[:start] + transform(text[start:end]) + text[end:]


def replace_subroutine_rule(text: str, subroutine: str, replacement: str) -> str:
    start, end = rule_span_by_subroutine(text, subroutine)
    return text[:start] + replacement + text[end:]


def dispatcher_rule(subroutine: str, variants: tuple[str, str, str], common: str = "") -> str:
    return (
        f'rule("Global subroutine: Deluxe dispatcher {subroutine}")\r\n'
        "{\r\n"
        "\tevent\r\n"
        "\t{\r\n"
        "\t\tSubroutine;\r\n"
        f"\t\t{subroutine};\r\n"
        "\t}\r\n\r\n"
        "\tactions\r\n"
        "\t{\r\n"
        "\t\tIf(Global.stageMode[0] == 0);\r\n"
        f"\t\t\tCall Subroutine({variants[0]});\r\n"
        "\t\tElse If(Global.stageMode[0] == 1);\r\n"
        f"\t\t\tCall Subroutine({variants[1]});\r\n"
        "\t\tElse;\r\n"
        f"\t\t\tCall Subroutine({variants[2]});\r\n"
        "\t\tEnd;\r\n"
        f"{common}"
        "\t}\r\n"
        "}"
    )


COMMON_INIT2 = '''		Global.MIXING_RECIPE = Mapped Array(Global.ITEM_NAME, Empty Array);
		Global.MIXING_RESULT = Mapped Array(Global.ITEM_NAME, Empty Array);
		For Global Variable(checkingIndex, False, Count Of(Global.RAW_MIX), True);
			Modify Global Variable At Index(MIXING_RECIPE, Global.RAW_MIX[Global.checkingIndex] % 1000, Append To Array,
				Round To Integer(Global.RAW_MIX[Global.checkingIndex] / 1000, Down));
			Modify Global Variable At Index(MIXING_RECIPE, Round To Integer(Global.RAW_MIX[Global.checkingIndex] / 1000, Down),
				Append To Array, Global.RAW_MIX[Global.checkingIndex] % 1000);
			Modify Global Variable At Index(MIXING_RESULT, Global.RAW_MIX[Global.checkingIndex] % 1000, Append To Array,
				Global.RAW_RESULT[Global.checkingIndex]);
			Modify Global Variable At Index(MIXING_RESULT, Round To Integer(Global.RAW_MIX[Global.checkingIndex] / 1000, Down),
				Append To Array, Global.RAW_RESULT[Global.checkingIndex]);
		End;
		Global.upgradePrice = Array(Array(100, 250, 750), Array(100, 100, 100), Array(100, 100, 100, 100), Array(100, 100, 100));
		Global.UPGRADE_CODE = Array(Array(6, -1, -2), Array(0, 1, 2), Array(3, 4, 5, 6), Array(7, 8, 9));
		Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7);
		Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17, 19, 20), Array(10, 13, 14));
		Global.KNIFE_AMOUNT = Array(1.200, 1.500, 1.500, 1.500, 3, 1.200, 6);
		Global.KNIFE_DECREASE = Array(0.150, 0.100, 0.050, 0.050, 0.050, 0.100, 0.030);
'''.replace("\n", "\r\n")


COMMON_INIT3 = '''		Call Subroutine(dataInit_customerCommon);
		Global.customerCallTime = Array(16, 12, 8, 4, 20)[Global.difficulty];
		Global.setUpTime = Array(120, 40, 30, 30, 120)[Global.difficulty];
		Global.scoreDecrease = Array(Array(Null, Null, Null, Null, Null, Null), Array(5, Null, 5, 5, 5, 5),
			Array(15, Null, 15, 35, 15, 15), Array(50, Null, 50, 50, 50, 50))[Global.difficulty];
		Global.despawnTime = Array(30, 25, 20, 15, 60)[Global.difficulty];
		Global.additionalScore = Global.stageMode == 5 ? 15 : Array(Null, 5, 10, 15)[Global.difficulty];
		Global.failEnd = Array(99, 5, 3, 2, 3, 1)[Global.stageMode];
'''.replace("\n", "\r\n")


COOLING_GUN_BRANCH = '''		Else If(Global.stageMode[0] == 1 && Event Player.itemPerk == 8);
			Play Effect(All Players(All Teams), Bad Pickup Effect, Color(Sky Blue),
				Eye Position(Event Player) + Facing Direction Of(Event Player) * 3, 1);
			Play Effect(All Players(All Teams), Brigitte Whip Shot Heal Area Sound, Null,
				Eye Position(Event Player) + Facing Direction Of(Event Player) * 3, 100);
			If(Event Player.controlingIndex != -1);
				Play Effect(All Players(All Teams), Bad Pickup Effect, Color(Sky Blue),
					Global.itemPosition[Event Player.controlingIndex], 1);
				If(Global.itemStatus[Event Player.controlingIndex] == 5);
					Global.itemProgress[Event Player.controlingIndex] += Global.superDrink == 6 ? 10 : 1;
				Else;
					Global.itemStatus[Event Player.controlingIndex] = 5;
					Global.itemProgress[Event Player.controlingIndex] = Global.superDrink == 6 ? 10 : 1;
				End;
				If(Global.itemProgress[Event Player.controlingIndex]
						>= Global.ICE_NEEDED[Global.itemCode[Event Player.controlingIndex]]);
					Global.itemCode[Event Player.controlingIndex]
						= Global.ICE_RESULT[Global.itemCode[Event Player.controlingIndex]];
					Global.itemProgress[Event Player.controlingIndex] = Null;
					Play Effect(All Players(All Teams), Brigitte Repair Pack Armor Sound, Null,
						Global.itemPosition[Event Player.controlingIndex], 50);
					Play Effect(All Players(All Teams), Good Explosion, Color(Sky Blue),
						Global.itemPosition[Event Player.controlingIndex], 0.500);
					Global.itemVelocity[Event Player.controlingIndex]
						+= Direction From Angles(False, Random Integer(False, 360)) * 0.005 + Vector(False, 0.075, False);
					Modify Global Variable At Index(itemCooker, Event Player.controlingIndex, Append To Array,
						Global.itemLastControl[Event Player.controlingIndex]);
				End;
			End;
			Event Player.controlingIndex = -1;
			Event Player.itemPerkDurability -= 1;
			Call Subroutine(destroyPerk);
			Wait(0.300, Ignore Condition);'''.replace("\n", "\r\n")


ICE_MACHINE_BRANCH = '''				Else If(Global.stageMode[0] == 1 && (Distance Between(Global.itemPosition[Global.cookingIndex],
						Vector(226.617, 2, 159.497)) < 0.550 || Distance Between(Global.itemPosition[Global.cookingIndex],
						Vector(226.617, 2.748, 159.497)) < 0.550));
					Play Effect(All Players(All Teams), Brigitte Repair Pack Impact Sound, Null,
						Vector(226.617, 2.748, 159.497), 50);
					Play Effect(All Players(All Teams), Good Explosion, Color(Sky Blue),
						Global.itemPosition[Global.cookingIndex], True);
					Global.itemDespawn[Global.cookingIndex] = Null;
					If(Global.itemStatus[Global.cookingIndex] == 5);
						Global.itemProgress[Global.cookingIndex] += Global.fryingPower;
					Else;
						Global.itemStatus[Global.cookingIndex] = 5;
						Global.itemProgress[Global.cookingIndex] = Global.fryingPower;
					End;
					If(Global.itemProgress[Global.cookingIndex]
							>= Global.ICE_NEEDED[Global.itemCode[Global.cookingIndex]]);
						Global.itemCode[Global.cookingIndex]
							= Global.ICE_RESULT[Global.itemCode[Global.cookingIndex]];
						Global.itemProgress[Global.cookingIndex] = Null;
						Play Effect(All Players(All Teams), Brigitte Repair Pack Armor Sound, Null,
							Vector(226.617, 2.748, 159.497), 50);
						Play Effect(All Players(All Teams), Good Explosion, Color(Aqua),
							Global.itemPosition[Global.cookingIndex], 0.500);
						Global.itemVelocity[Global.cookingIndex]
							+= Direction From Angles(False, Random Integer(False, 360)) * 0.005 + Vector(False, 0.075, False);
						Modify Global Variable At Index(itemCooker, Global.cookingIndex, Append To Array,
							Global.itemLastControl[Global.cookingIndex]);
					End;'''.replace("\n", "\r\n")


PERK_HUD_RULE = '''rule("Global subroutine: Perk Hud")
{
	event
	{
		Subroutine;
		perkHud;
	}

	actions
	{
		Abort If(Event Player.itemPerk == -1);
		Create HUD Text(Event Player, Array(
			Ability Icon String(Hero(Roadhog), Button(Ability 2)), Ability Icon String(Hero(Ana), Button(Ultimate)),
			Ability Icon String(Hero(Ashe), Button(Ability 2)), Ability Icon String(Hero(Sigma), Button(Ability 1)),
			Ability Icon String(Hero(Baptiste), Button(Ultimate)), Ability Icon String(Hero(Torbjörn), Button(Ultimate)),
			Ability Icon String(Hero(Wrecking Ball), Button(Ability 1)), Ability Icon String(Hero(Domina), Button(Ultimate)),
			Ability Icon String(Hero(Mei), Button(Ability 1)))[Event Player.itemPerk],
			Custom String("{1}{0}", Array(True, True, False, False, False, False, True, True, False)[Event Player.itemPerk]
				? Custom String("") : Custom String("-{0}%", Round To Integer(Event Player.itemPerkDurability, Up)),
				Evaluate Once(Global.ITEM_NAME[Global.PERK_LIST[False][Event Player.itemPerk]])),
			Custom String("〔{0}〕", Array(Input Binding String(Button(Ultimate)), Input Binding String(Button(Ultimate)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Secondary Fire)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Secondary Fire)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Ultimate)),
				Input Binding String(Button(Secondary Fire)))[Event Player.itemPerk]), Right, 2,
			Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]],
			Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]], Color(White), String and Color, Default Visibility);
		Event Player.itemPerkText = Last Text ID;
	}
}'''.replace("\n", "\r\n")


DELUXE_BOOTSTRAP = '''		Global.stageMode = Array(0, 0);
		Global.DELUXE_DATA = Array(0);'''.replace("\n", "\r\n")


def patch_global_setting(rule: str) -> str:
    rule = replace_once(
        rule,
        "\t\tDestroy All Dummy Bots;\r\n\t\tCall Subroutine(dataInit);",
        "\t\tDestroy All Dummy Bots;\r\n" + DELUXE_BOOTSTRAP + "\r\n\t\tCall Subroutine(dataInit);",
        "Deluxe bootstrap",
    )
    edition_hud_old = (
        '\t\tCreate HUD Text(All Players(Team 1), Null, Null, Custom String(\r\n'
        '\t\t\t"\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n"), Top, -999, Null, Null, Null, Visible To,\r\n'
        '\t\t\tDefault Visibility);'
    )
    edition_hud_new = (
        '\t\tCreate HUD Text(All Players(Team 1), Custom String(" 〔 {0} 〕 ", Array(Custom String("오리지널"), '
        'Custom String("카페"), Custom String("쿡제요리"))[Global.stageMode[0]]), Null,\r\n'
        '\t\t\tLocal Player == Global.scbRank ? Custom String("[{0}]: 에디션 변경", Input Binding String(Button(Ability 2))) '
        ': Custom String(" 방장이 에디션을 결정하는 중입니다"), Top, -999, Color(Orange), Null, Color(White), String and Color,\r\n'
        '\t\t\tDefault Visibility);'
    )
    rule = replace_once(rule, edition_hud_old, edition_hud_new, "edition selection HUD")
    rule = replace_once(
        rule,
        "\t\tGlobal.stageMode = 0;\r\n\t\tCall Subroutine(selectMode);\r\n\t\tGlobal.difficulty =",
        "\t\tGlobal.stageMode[1] = 1;\r\n\t\tCall Subroutine(selectMode);\r\n"
        "\t\tCall Subroutine(dataInit);\r\n\t\tCall Subroutine(dataInit2);\r\n\t\tGlobal.difficulty =",
        "reload selected edition data",
    )
    ice_label = '''		If(Global.stageMode[0] == 1);
			Create In-World Text(Players Within Radius(Vector(226.649, 2, 159.387), 10, Team 1, Off), Custom String("제빙기"),
				Vector(226.649, 3, 159.387), 3, Do Not Clip, Visible To, Color(Blue), Default Visibility);
		End;'''.replace("\n", "\r\n")
    pan_label = (
        '\t\tCreate In-World Text(Players Within Radius(Vector(224.926, 2, 158.167), 10, Team 1, Off), Custom String("팬"), Vector(224.926,\r\n'
        "\t\t\t2.750, 158.167), 3, Do Not Clip, Visible To, Color(Red), Default Visibility);"
    )
    rule = replace_once(rule, pan_label, pan_label + "\r\n" + ice_label, "ice-machine label position")
    rule = replace_once(
        rule,
        'Create In-World Text(Players Within Radius(Vector(223.583, 2, 157.286), 10, Team 1, Off), Custom String("그릴"), Vector(223.583,\r\n'
        '\t\t\t3, 157.286), 3, Do Not Clip, Visible To, Color(Orange), Default Visibility);',
        'Create In-World Text(Players Within Radius(Vector(223.583, 2, 157.286), 10, Team 1, Off), Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Vector(223.583,\r\n'
        '\t\t\t3, 157.286), 3, Do Not Clip, Visible To and String, Color(Orange), Default Visibility);',
        "cafe oven world label",
    )
    rule = replace_once(
        rule,
        'Custom String(\r\n\t\t\t"{0} 솥:{1}% / 튀김:{2}%", Hero Icon String(Hero(Junkrat)), 100 + 25 * Global.potPower, Global.fryingPower * 100)',
        'Global.stageMode[0] == 1 ? Custom String("{0} 솥:{1}% / 튀김&제빙:{2}%", Hero Icon String(Hero(Junkrat)), 100 + 25 * Global.potPower, Global.fryingPower * 100) : Custom String("{0} 솥:{1}% / 튀김:{2}%", Hero Icon String(Hero(Junkrat)), 100 + 25 * Global.potPower, Global.fryingPower * 100)',
        "cafe status label",
    )
    rule = replace_once(
        rule,
        'Custom String(\r\n\t\t\t"{0} 팬:{1}% / 그릴:{2}%", Hero Icon String(Hero(Junkrat)), Global.panPower * 100, Global.grillingPower * 100)',
        'Global.stageMode[0] == 1 ? Custom String("{0} 팬:{1}% / 오븐:{2}%", Hero Icon String(Hero(Junkrat)), Global.panPower * 100, Global.grillingPower * 100) : Custom String("{0} 팬:{1}% / 그릴:{2}%", Hero Icon String(Hero(Junkrat)), Global.panPower * 100, Global.grillingPower * 100)',
        "cafe oven status label",
    )
    rule = replace_once(
        rule,
        "\t\t\tGlobal.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50,\r\n"
        "\t\t\t\t-70)) * 0.100, 357, 100, Null);",
        "\t\t\tGlobal.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50,\r\n"
        "\t\t\t\t-70)) * 0.100, 12, 100, Null);",
        "practice starter",
    )
    rule = replace_once(
        rule,
        "Array(0, 357, 357, 361, 360, 361)[Global.stageMode]",
        "Global.DELUXE_DATA[2][0][Global.stageMode]",
        "first edition starter",
    )
    rule = replace_once(
        rule,
        "Array(0, 434, 361, 358, 358, 359)[Global.stageMode]",
        "Global.DELUXE_DATA[2][1][Global.stageMode]",
        "second edition starter",
    )
    close = "\r\n\t}\r\n}"
    if not rule.endswith(close):
        raise BuildError("Global Setting close not found")
    return rule


def patch_select_mode(rule: str) -> str:
    old = '''		Global.scbRank = Slot Of(Host Player) == -1 ? All Players(Team 1)[False] : Host Player;
		Wait Until(Is Button Held(Global.scbRank, Button(Reload)) || Is Button Held(Global.scbRank, Button(Jump)), 99999);
		If(Is Button Held(Global.scbRank, Button(Reload)));
			Global.stageMode = (Global.stageMode + True) % 6;
			Wait Until(!Is Button Held(Global.scbRank, Button(Reload)), 99999);
			Loop;
		End;'''.replace("\n", "\r\n")
    new = '''		Global.scbRank = Slot Of(Host Player) == -1 ? All Players(Team 1)[False] : Host Player;
		Wait Until(Is Button Held(Global.scbRank, Button(Ability 2)) || Is Button Held(Global.scbRank, Button(Reload))
			|| Is Button Held(Global.scbRank, Button(Jump)), 99999);
		If(Is Button Held(Global.scbRank, Button(Ability 2)) || Is Button Held(Global.scbRank, Button(Reload)));
			If(Is Button Held(Global.scbRank, Button(Ability 2)));
				Global.stageMode[0] = (Global.stageMode[0] + True) % 3;
				Wait Until(!Is Button Held(Global.scbRank, Button(Ability 2)), 99999);
			End;
			If(Is Button Held(Global.scbRank, Button(Reload)));
				Global.stageMode[1] = (Global.stageMode[1] + True) % 6;
				Wait Until(!Is Button Held(Global.scbRank, Button(Reload)), 99999);
			End;
			Loop;
		End;'''.replace("\n", "\r\n")
    return replace_once(rule, old, new, "merged edition/mode input")


def patch_secondary(rule: str) -> str:
    anchor = "\t\t\tWait(0.300, Ignore Condition);\r\n\t\tEnd;\r\n\t\tWait(0.050, Ignore Condition);"
    replacement = "\t\t\tWait(0.300, Ignore Condition);\r\n" + COOLING_GUN_BRANCH + "\r\n\t\tEnd;\r\n\t\tWait(0.050, Ignore Condition);"
    return replace_once(rule, anchor, replacement, "cooling-gun branch")


def patch_ultimate(rule: str) -> str:
    rule = replace_once(
        rule,
        "Array(61, 62, 63, 64, 65, 265, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 432, 433, 434)",
        "Array(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)",
        "clone exclusion",
    )
    rule = replace_once(
        rule,
        "Else If(Event Player.itemPerk == 6);",
        "Else If(Global.stageMode[0] == 0 && Event Player.itemPerk == 7);",
        "preserved-box gate",
    )
    if rule.count("Else If(Event Player.itemPerk == 7 && Count Of(All Players(Team 1))") != 2:
        raise BuildError("serving-ball branches: expected two")
    rule = rule.replace(
        "Else If(Event Player.itemPerk == 7 && Count Of(All Players(Team 1))",
        "Else If(Event Player.itemPerk == 6 && Count Of(All Players(Team 1))",
    )
    return rule


def patch_item_cooking(rule: str) -> str:
    anchor = "\r\n\t\t\t\tEnd;\r\n\t\t\tEnd;\r\n\t\tEnd;\r\n\t\tWait(True, Ignore Condition);"
    return replace_once(rule, anchor, "\r\n" + ICE_MACHINE_BRANCH + anchor, "ice-machine cooking branch")


def patch_control_item(rule: str) -> str:
    return rule


def patch_set_hint(rule: str) -> str:
    replacements = {
        "Array(3, 4, 8, 11, 7, 10, 25, 24)": "Array(63, 64, 352, 356, 354, 355, 25, 24)",
        "Array(126, 7)": "Array(126, 354)",
        "Array(55, 56, 57, 58, 59, 60, 7, 23)": "Array(55, 56, 57, 58, 59, 60, 354, 23)",
    }
    for old, new in replacements.items():
        rule = replace_once(rule, old, new, f"tutorial item map {old}")

    actions_open = "\tactions\r\n\t{\r\n"
    actions_close = "\r\n\t}\r\n}"
    if rule.count(actions_open) != 1 or not rule.endswith(actions_close):
        raise BuildError("setHint actions boundary mismatch")
    body_start = rule.index(actions_open) + len(actions_open)
    body = rule[body_start:-len(actions_close)]
    if not body.startswith("\t\tIf(Global.stage == 0);") or not body.endswith("\t\tEnd;"):
        raise BuildError("setHint tutorial body mismatch")
    indented_body = "\r\n".join("\t" + line if line else line for line in body.split("\r\n"))
    edition_body = (
        "\t\tIf(Global.stageMode[0] == 0);\r\n"
        + indented_body
        + "\r\n\t\tElse If(Global.stageMode[0] == 1);\r\n"
        + "\t\tElse;\r\n"
        + "\t\tEnd;"
    )
    return rule[:body_start] + edition_body + actions_close


def patch_common_runtime(text: str) -> str:
    # Canonical runtime references outside the generated data rules.
    exact = {
        "Else If(432 == Global.itemCode[Event Player.controlingIndex]);": "Else If(18 == Global.itemCode[Event Player.controlingIndex]);",
        "Else If(Global.itemCode[Global.checkingIndex] == 432);": "Else If(Global.itemCode[Global.checkingIndex] == 18);",
        "Random Integer(62, 65)": "Random Integer(2, 5)",
        "Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 63, 100, Null);": "Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 3, 100, Null);",
        "Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 354, 100, Null);": "Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 7, 100, Null);",
        "-70)) * 0.100, 354, 100, Null);": "-70)) * 0.100, 7, 100, Null);",
        "Global.upgradeList[True] = Array(61, 265, 62, 63, 64, 65, 354, 352, 353, 356, 357, 360, 361, 433, 434, 355, 358, 359);": "Global.upgradeList[True] = Global.DELUXE_DATA[2][2];",
        "Global.upgradeList[True] = Randomized Array(Array(352, 352, 352, 352, 353, 356, 356, 356, 356, 357, 357, 360, 361, 361, 433, 433, 433, 434, 434));": "Global.upgradeList[True] = Randomized Array(Global.DELUXE_DATA[2][3]);",
        "Global.upgradeList[2] = Randomized Array(Array(355, 355, 355, 355, 355, 358, 358, 358, 359));": "Global.upgradeList[2] = Randomized Array(Array(10, 10, 10, 10, 10, 13, 13, 13, 14));",
    }
    for old, new in exact.items():
        count = text.count(old)
        if old.startswith("Else If(432"):
            if count != 2:
                raise BuildError(f"money pickup comparisons: expected 2, got {count}")
            text = text.replace(old, new)
        else:
            text = replace_once(text, old, new, f"runtime map: {old[:50]}")

    active_random = "Random Value In Array(Global.PERK_LIST[Random Integer(0, 1)])"
    replacement = "Random Value In Array(Array(Global.DELUXE_DATA[1], Global.PERK_LIST[True])[Random Integer(False, True)])"
    if text.count(active_random) != 2:
        raise BuildError(f"active random paths: expected 2, got {text.count(active_random)}")
    text = text.replace(active_random, replacement)

    # Remaining money literal occurs in the multi-line drop/purchase create calls.
    money_tail = ", 432, 100, Null);"
    text = replace_once(text, money_tail, ", 18, 100, Null);", "upgrade money item")
    text = replace_once(text, ": 432, 100, Null);", ": 18, 100, Null);", "tip money item")

    # ORG melt behavior is both stored and evaluated only for ORG.
    melt_ref = "Array Contains(Global.MELT_LIST,"
    if text.count(melt_ref) != 5:
        raise BuildError(f"MELT runtime references: expected 5, got {text.count(melt_ref)}")
    text = text.replace(
        melt_ref,
        "Global.stageMode[0] == 0 && Array Contains(Global.ICE_RESULT,",
    )
    return text


def build_text() -> str:
    source = data_builder.read_ow(BASE)
    generated, _ = data_builder.build()

    text = replace_once(source, "\t\t126: MELT_LIST", "\t\t126: DELUXE_DATA", "global container")
    text = replace_once(text, "\t\t100: itemPrevPosition", "\t\t100: ICE_NEEDED", "ICE_NEEDED global slot")
    text = replace_once(text, "\t\t105: itemNormal", "\t\t105: ICE_RESULT", "ICE_RESULT global slot")
    text = replace_once(
        text,
        "Global.itemPrevPosition[Global.checkingIndex] = Global.itemPosition[Global.checkingIndex];",
        "",
        "remove unused itemPrevPosition write",
    )
    text = replace_once(
        text,
        "Global.itemNormal[Global.checkingIndex] = Global.normal;",
        "",
        "remove unused itemNormal write",
    )
    text = replace_once(
        text,
        "\t28: changeHero\r\n\t29: stageFail",
        "\t28: changeHero\r\n\t29: stageFail\r\n\t30: dataInit_org1\r\n"
        "\t31: dataInit_org2\r\n\t32: dataInit_org3\r\n\t33: dataInit_cafe1\r\n\t34: dataInit_cafe2\r\n"
        "\t35: dataInit_cafe3\r\n\t36: dataInit_gc1\r\n\t37: dataInit_gc2\r\n\t38: dataInit_gc3\r\n"
        "\t39: dataInit_customerCommon",
        "subroutine declarations",
    )

    text = modify_rule(text, "Global: Setting", patch_global_setting)
    text = modify_rule(text, "Player: Secondary fire button", patch_secondary)
    text = modify_rule(text, "Player: Ultimate button", patch_ultimate)
    text = modify_rule(text, "Player: Interact", patch_control_item)
    text = modify_rule(text, "Global subroutine: Item cooking", patch_item_cooking)
    text = modify_rule(text, "Global subroutine: Set Hint Text", patch_set_hint)
    text = modify_rule(text, "Host Player: Select Mode", patch_select_mode)
    text = replace_subroutine_rule(text, "perkHud", PERK_HUD_RULE)

    text = replace_subroutine_rule(
        text,
        "dataInit",
        dispatcher_rule("dataInit", ("dataInit_org1", "dataInit_cafe1", "dataInit_gc1")),
    )
    text = replace_subroutine_rule(
        text,
        "dataInit2",
        dispatcher_rule(
            "dataInit2", ("dataInit_org2", "dataInit_cafe2", "dataInit_gc2"), COMMON_INIT2
        ),
    )
    text = replace_subroutine_rule(
        text,
        "dataInit3",
        dispatcher_rule(
            "dataInit3", ("dataInit_org3", "dataInit_cafe3", "dataInit_gc3"), COMMON_INIT3
        ),
    )

    text = patch_common_runtime(text)
    text = replace_once(
        text,
        'Array(Custom String("튀김기"), Custom String("솥"), Custom String("그릴"), Custom String("팬"))',
        'Array(Global.stageMode[0] == 1 ? Custom String("튀김기&제빙기") : Custom String("튀김기"), Custom String("솥"), Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Custom String("팬"))',
        "upgrade station label",
    )

    text = text.replace("v260827", "v260828")
    text = text.rstrip("\r\n") + "\r\n\r\n" + generated
    text = re.sub(r"\bGlobal\.stageMode\b(?!\[)", "Global.stageMode[1]", text)
    text = text.replace("Global.stageMode[1] = Array(0, 0);", "Global.stageMode = Array(0, 0);")
    text = re.sub(r"[ \t]+(?=\r\n)", "", text)
    text = re.sub(
        r"(?m)^( +)(?=\t)",
        lambda match: "\t" * (len(match.group(1)) // 4) + " " * (len(match.group(1)) % 4),
        text,
    )
    return text


def validate_assembled(text: str) -> dict[str, object]:
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    in_string = escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                raise BuildError(f"unbalanced delimiter {char!r} at offset {index}")
            stack.pop()
    if in_string or stack:
        raise BuildError("unclosed string or delimiter in assembled output")

    if "Global.MELT_LIST" in text:
        raise BuildError("legacy MELT_LIST reference remains")
    if "Global.DELUXE_DATA[0]" in text or re.search(r"Global\.DELUXE_DATA\[(?:3|[4-9]|[1-9]\d+)\]", text):
        raise BuildError("uncompacted DELUXE_DATA slot reference remains")
    if "selectEdition" in text or "Select Deluxe Edition" in text:
        raise BuildError("retired standalone edition selector remains")
    for name in (
        "dataInit_org1", "dataInit_org2", "dataInit_org3",
        "dataInit_cafe1", "dataInit_cafe2", "dataInit_cafe3",
        "dataInit_gc1", "dataInit_gc2", "dataInit_gc3", "dataInit_customerCommon",
    ):
        if len(re.findall(rf"(?mi)^[ \t]+{re.escape(name)};\r?$", text)) != 1:
            raise BuildError(f"generated subroutine event count mismatch: {name}")
    if text.count("Global.ICE_NEEDED =") != 1 or text.count("Global.ICE_RESULT =") != 2:
        raise BuildError("shared ICE_RESULT assignment count mismatch")
    if text.count("Global.CUSTOMER_LIST =") != 1:
        raise BuildError("shared CUSTOMER_LIST assignment count mismatch")
    if text.count("Call Subroutine(dataInit_customerCommon);") != 1:
        raise BuildError("shared CUSTOMER_LIST dispatcher call mismatch")
    for legacy_tutorial_bypass in (
        "If(Global.stageMode[0] != 0 && Global.difficulty == 4);",
        "If(Global.stageMode[0] != 0 && Global.stage == 0);",
        "Abort If(Global.stageMode[0] != 0);",
    ):
        if legacy_tutorial_bypass in text:
            raise BuildError(f"legacy tutorial bypass remains: {legacy_tutorial_bypass}")
    empty_tutorial_branches = (
        "\t\tElse If(Global.stageMode[0] == 1);\r\n"
        "\t\tElse;\r\n"
        "\t\tEnd;\r\n\t}\r\n}"
    )
    if text.count(empty_tutorial_branches) != 1:
        raise BuildError("empty CAFE/GC tutorial branch mismatch")
    scalar_stage_mode = re.findall(r"\bGlobal\.stageMode\b(?!\[)", text)
    if scalar_stage_mode != ["Global.stageMode"] or text.count("Global.stageMode = Array(0, 0);") != 1:
        raise BuildError("stageMode must be an array with only [0]/[1] scalar access")
    for fragment in (
        "If(Is Button Held(Global.scbRank, Button(Ability 2)) || Is Button Held(Global.scbRank, Button(Reload)));",
        "Global.stageMode[0] = (Global.stageMode[0] + True) % 3;",
        "Global.stageMode[1] = (Global.stageMode[1] + True) % 6;",
        "\t\t\tLoop;\r\n\t\tEnd;\r\n\t\tDestroy HUD Text(Global.globalText[False]);",
        "\t\tCall Subroutine(selectMode);\r\n\t\tCall Subroutine(dataInit);\r\n\t\tCall Subroutine(dataInit2);",
    ):
        if text.count(fragment) != 1:
            raise BuildError(f"combined edition/mode selector mismatch: {fragment}")
    for assignment, expected in {
        "Global.MIXING_RECIPE = Mapped Array(Global.ITEM_NAME, Empty Array);": 1,
        "Global.UPGRADE_CODE = Array(Array(6, -1, -2)": 1,
        "Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7);": 1,
        "Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17, 19, 20)": 1,
        "Global.customerCallTime = Array(16, 12, 8, 4, 20)": 1,
    }.items():
        if text.count(assignment) != expected:
            raise BuildError(f"common dispatcher assignment count mismatch: {assignment}")

    global_section = text[text.index("\tglobal:") : text.index("\tplayer:")]
    globals_found = [(int(number), name) for number, name in re.findall(
        r"(?m)^[ \t]+(\d+):\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", global_section
    )]
    if [number for number, _ in globals_found] != list(range(128)):
        raise BuildError("global variable IDs are not exactly 0..127")
    if dict(globals_found).get(126) != "DELUXE_DATA":
        raise BuildError("global variable 126 is not DELUXE_DATA")
    if dict(globals_found).get(100) != "ICE_NEEDED" or dict(globals_found).get(105) != "ICE_RESULT":
        raise BuildError("global IDs 100/105 are not ICE_NEEDED/ICE_RESULT")
    if "itemPrevPosition" in text or "itemNormal" in text:
        raise BuildError("retired write-only globals remain")

    sub_start = text.index("subroutines\r\n{")
    sub_end = text.index("\r\n}\r\n\r\nrule(", sub_start)
    sub_section = text[sub_start:sub_end]
    subs_found = [(int(number), name) for number, name in re.findall(
        r"(?m)^[ \t]+(\d+):\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", sub_section
    )]
    if [number for number, _ in subs_found] != list(range(40)):
        raise BuildError("subroutine IDs are not exactly 0..39")

    create_assignments = data_builder.find_all_assignments(text, "createItemData")
    if len(create_assignments) != 33:
        raise BuildError(f"createItemData site count mismatch: {len(create_assignments)} != 33")
    forbidden_old_tools = {61, 62, 63, 64, 65, 265, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 432, 433, 434}
    for assignment in create_assignments:
        _, args, suffix = data_builder.unwrap_call(assignment.expression, "Array")
        if suffix or len(args) != 5:
            raise BuildError("createItemData assignment is not a five-field Array")
        literals = {int(value) for value in re.findall(r"(?<![.\d])-?\d+(?![.\d])", args[2])}
        stale = literals & forbidden_old_tools
        if stale:
            raise BuildError(f"stale ORG tool code in createItemData[2]: {sorted(stale)}")

    if "v260827" in text or text.count("v260828") < 2:
        raise BuildError("project version was not updated consistently")
    if text.count(
        'Array(Custom String("오리지널"), Custom String("카페"), Custom String("쿡제요리"))[Global.stageMode[0]]'
    ) != 1:
        raise BuildError("Deluxe edition selector labels do not match ORG/CAFE/GC data")
    for fragment in (
        'If(Global.stageMode[0] == 1);\r\n\t\t\tCreate In-World Text(Players Within Radius(Vector(226.649, 2, 159.387)',
        'Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Vector(223.583,\r\n'
        '\t\t\t3, 157.286), 3, Do Not Clip, Visible To and String, Color(Orange)',
        'Global.stageMode[0] == 1 ? Custom String("{0} 팬:{1}% / 오븐:{2}%"',
        'Custom String("솥"), Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Custom String("팬")',
    ):
        if text.count(fragment) != 1:
            raise BuildError(f"CAFE oven label branch mismatch: {fragment}")
    # Scan every rule independently.  The delimiter check above catches
    # malformed expressions; this block stack additionally catches actions
    # inserted on the wrong side of an If/Else/While/For/End boundary.
    cursor = 0
    rule_count = 0
    largest_rule = {"name": "", "bytes": 0}
    while True:
        start = text.find('rule("', cursor)
        if start < 0:
            break
        open_at = text.find("{", start)
        cursor = data_builder.scan_balanced(text, open_at, "{", "}")
        rule_text = text[start:cursor]
        rule_name = rule_text.split('"', 2)[1]
        rule_bytes = len(rule_text.replace("\r\n", "\n").encode("utf-8"))
        if rule_bytes > largest_rule["bytes"]:
            largest_rule = {"name": rule_name, "bytes": rule_bytes}
        block_stack: list[dict[str, object]] = []
        for relative_line, raw_line in enumerate(rule_text.splitlines(), 1):
            statement = raw_line.strip()
            if statement.startswith("disabled "):
                statement = statement[len("disabled "):]
            if re.match(r"^Else If\s*\(", statement):
                if not block_stack or block_stack[-1]["kind"] != "if":
                    raise BuildError(
                        f"Else If without matching If in {rule_name!r} line {relative_line}"
                    )
                if block_stack[-1]["else_seen"]:
                    raise BuildError(
                        f"Else If after Else in {rule_name!r} line {relative_line}"
                    )
            elif statement == "Else;":
                if not block_stack or block_stack[-1]["kind"] != "if":
                    raise BuildError(
                        f"Else without matching If in {rule_name!r} line {relative_line}"
                    )
                if block_stack[-1]["else_seen"]:
                    raise BuildError(
                        f"duplicate Else in {rule_name!r} line {relative_line}"
                    )
                block_stack[-1]["else_seen"] = True
            elif re.match(r"^If\s*\(", statement):
                block_stack.append({"kind": "if", "line": relative_line, "else_seen": False})
            elif re.match(r"^(?:While|For Global Variable|For Player Variable)\s*\(", statement):
                block_stack.append({"kind": "loop", "line": relative_line, "else_seen": False})
            elif statement == "End;":
                if not block_stack:
                    raise BuildError(f"End without opener in {rule_name!r} line {relative_line}")
                block_stack.pop()
        legacy_open_signature = {
            # Preserved verbatim from ko.ow: the final Else branch runs to the
            # end of the actions block and the export omits its trailing End.
            "Player: Reload button": [("if", True)],
        }.get(rule_name, [])
        open_signature = [
            (str(block["kind"]), bool(block["else_seen"])) for block in block_stack
        ]
        if open_signature != legacy_open_signature:
            if not block_stack:
                raise BuildError(
                    f"legacy open-block signature changed in {rule_name!r}: "
                    f"expected {legacy_open_signature}, got none"
                )
            opener = block_stack[-1]
            raise BuildError(
                f"unclosed {opener['kind']} in {rule_name!r} line {opener['line']}"
            )
        rule_count += 1
    if rule_count != 57:
        raise BuildError(f"assembled rule count mismatch: {rule_count} != 57")
    if largest_rule["bytes"] > 98 * 1024:
        raise BuildError(f"source rule exceeds 98 KiB: {largest_rule}")
    return {
        "largest_rule": largest_rule,
        "limit_bytes": 98 * 1024,
        "rules_over_limit": 0,
        "scope": "LF UTF-8 Workshop source only; compiler/runtime not invoked",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="assemble and validate without writing kr_deluxe.ow")
    args = parser.parse_args()
    text = build_text()
    source_rule_size_check = validate_assembled(text)
    output_text = text.replace("\r\n", "\n")
    digest = hashlib.sha256(output_text.encode("utf-8")).hexdigest().upper()
    if not args.check:
        TARGET.write_bytes(output_text.encode("utf-8"))
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        site_lines = ["line\titem_expression"]
        for assignment in data_builder.find_all_assignments(text, "createItemData"):
            _, call_args, _ = data_builder.unwrap_call(assignment.expression, "Array")
            line = text.count("\n", 0, assignment.start) + 1
            expression = re.sub(r"\s+", " ", call_args[2]).strip().replace("\t", " ")
            site_lines.append(f"{line}\t{expression}")
        (BUILD_DIR / "runtime_item_sites.tsv").write_text(
            "\n".join(site_lines) + "\n", encoding="utf-8"
        )
        (BUILD_DIR / "assembled_validation.json").write_text(
            json.dumps(
                {
                    "sha256": digest,
                    "bytes": len(output_text.encode("utf-8")),
                    "rules": 57,
                    "globals": 128,
                    "ice_global_ids": {"ICE_NEEDED": 100, "ICE_RESULT": 105},
                    "retired_write_only_globals_removed": ["itemPrevPosition", "itemNormal"],
                    "subroutines": 40,
                    "selection_state": {"edition": "stageMode[0]", "mode": "stageMode[1]"},
                    "selection_inputs": {"edition": "Ability 2", "mode": "Reload", "confirm": "Jump"},
                    "deluxe_data_slots": {
                        "1": "active item-perk drops",
                        "2": "edition runtime configuration",
                    },
                    "shared_customer_list": {"source": "ORG/ko", "dispatcher_call": True},
                    "ice_result_reuse": {"ORG": "MELT_LIST", "CAFE": "ice conversion"},
                    "tutorial_routing": {"ORG": "implemented", "CAFE": "empty", "GC": "empty"},
                    "source_rule_size_check": source_rule_size_check,
                    "create_item_sites": len(site_lines) - 1,
                    "control_flow_checked": True,
                    "preserved_legacy_implicit_end_rules": ["Player: Reload button"],
                    "version": "v260828",
                    "gc_water_ported": False,
                    "gc_water_blocker": "gc_kr.ow has no water item record or Primary Fire source branch",
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    print(f"rules={output_text.count('rule(\"')} bytes={len(output_text.encode('utf-8'))} sha256={digest}")


if __name__ == "__main__":
    main()
