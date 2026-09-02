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

SUBROUTINE_NAMES = (
    "itemPhysics", "itemCooking", "despawnItem", "pot0", "pot1", "callCustomer",
    "startStage", "dataInit", "rotatingFridge", "createItem", "selectMode", "saveProgress",
    "loadProgress", "gameSummary", "knifeHud", "purchaseUpgrade", "perkHud", "setHint",
    "destroyItem", "destroyServeBot", "dropTips", "destroyPerk", "footHud", "serveFail",
    "gameSummaryTP", "validateServe", "changeHero", "stageFail", "dataInit_org1",
    "dataInit_org2", "dataInit_org3", "dataInit_cafe1", "dataInit_cafe2", "dataInit_cafe3",
    "dataInit_gc1", "dataInit_gc2", "dataInit_gc3", "dataInit_customerCommon",
    "menuInit", "otherMenu",
)


class BuildError(RuntimeError):
    pass


MAX_UI_STRING_SEGMENT = 90
SERIALIZED_UI_TABLES = {
    "edition_names": {
        "values": ("모듬회밥!", "카페!", "쿡제요리"),
        "groups": ((0, 1, 2),),
        "index": "Global.stageMode[0]",
        "count": 3,
    },
    "edition_credits": {
        "values": (
            "Gummybear&변기클라우드\\r\\n난이도 : ★★★☆☆",
            "Joseon&Deadlock\\r\\n난이도 : ★★☆☆☆",
            "Joseon\\r\\n난이도 : ★★★★☆",
        ),
        "groups": ((0,), (1, 2)),
        "index": "Global.stageMode[0]",
        "count": 1,
    },
    "mode_names": {
        "values": ("연습 모드", "캐주얼 다이닝", "파인 다이닝", "스타 비스트로", "마스터쿡 챌린지", "헤드셰프 챌린지"),
        "groups": ((0, 1, 2), (3, 4, 5)),
        "index": "Global.stageMode[1]",
        "count": 2,
    },
    "mode_descriptions": {
        "values": (
            "자유롭게 연습할 수 있는 샌드박스 모드 입니다",
            "5개의 메뉴가 등장하는 수습 난이도를 클리어하세요",
            "모든 메뉴가 등장하는 숙련 난이도를 클리어하세요",
            "까다로운 손님들이 등장하는 전문 난이도를 클리어하세요",
            "Hell's Kitchen 클리어에 도전하세요",
            "완벽의 영역에 도전하세요",
        ),
        "groups": ((0,), (1, 2), (3,), (4, 5)),
        "index": "Global.stageMode[1]",
        "count": 1,
    },
    "practice_edition_names": {
        "values": ("모듬회밥!", "카페!", "쿡제요리", "Joseon-뉴 3호점", "Gummybear-오리지널"),
        "groups": ((0, 1, 2, 3, 4),),
        "index": "Global.totalScore[False]",
        "count": 1,
    },
    "difficulty_names": {
        "values": ("수습 난이도", "숙련 난이도", "전문 난이도", "Hell's Kitchen"),
        "groups": ((0, 1, 2, 3),),
        "index": "Global.difficulty",
        "count": 2,
    },
}


def serialized_string_array(values: tuple[str, ...], groups: tuple[tuple[int, ...], ...]) -> str:
    if sorted(index for group in groups for index in group) != list(range(len(values))):
        raise BuildError("serialized UI string groups do not cover each value exactly once")
    if any("/" in value for value in values):
        raise BuildError("serialized UI string value contains the '/' delimiter")
    segments = ["/".join(values[index] for index in group) for group in groups]
    rendered = f'Custom String("{segments[-1]}")'
    for segment in reversed(segments[:-1]):
        rendered = f'Custom String("{segment}/{{0}}", {rendered})'
    for position, segment in enumerate(segments):
        payload = segment + ("/{0}" if position < len(segments) - 1 else "")
        if len(payload) > MAX_UI_STRING_SEGMENT:
            raise BuildError(
                f"serialized UI string segment exceeds {MAX_UI_STRING_SEGMENT} chars: {payload!r}"
            )
    return f'String Split({rendered}, Custom String("/"))'


def serialized_ui_expression(key: str, values: tuple[str, ...] | None = None) -> str:
    spec = SERIALIZED_UI_TABLES[key]
    selected = tuple(values if values is not None else spec["values"])
    return f'{serialized_string_array(selected, spec["groups"])}[{spec["index"]}]'


def serialize_ui_string_arrays(text: str) -> tuple[str, dict[str, int]]:
    report: dict[str, int] = {}
    for key, spec in SERIALIZED_UI_TABLES.items():
        values = tuple(spec["values"])
        pattern = r"Array\(\s*" + r"\s*,\s*".join(
            rf'Custom String\(\s*"{re.escape(value)}"\s*\)' for value in values
        ) + r"\s*\)\[" + re.escape(str(spec["index"])) + r"\]"
        replacement = serialized_ui_expression(key)
        text, count = re.subn(pattern, lambda _: replacement, text)
        if count != spec["count"]:
            raise BuildError(
                f"serialized UI table {key}: expected {spec['count']} matches, got {count}"
            )
        report[key] = count
    return text, report


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


def replace_subroutine_declarations(text: str) -> str:
    start = text.index("subroutines\r\n{")
    open_at = text.index("{", start)
    end = data_builder.scan_balanced(text, open_at, "{", "}")
    replacement = (
        "subroutines\r\n{\r\n"
        + "".join(f"\t{index}: {name}\r\n" for index, name in enumerate(SUBROUTINE_NAMES))
        + "}"
    )
    return text[:start] + replacement + text[end:]


def edition_phase_actions(variants: tuple[str, str, str]) -> str:
    return (
        "\t\tIf(Global.stageMode[0] == 0);\r\n"
        f"\t\t\tCall Subroutine({variants[0]});\r\n"
        "\t\tElse If(Global.stageMode[0] == 1);\r\n"
        f"\t\t\tCall Subroutine({variants[1]});\r\n"
        "\t\tElse;\r\n"
        f"\t\t\tCall Subroutine({variants[2]});\r\n"
        "\t\tEnd;\r\n"
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


COMMON_DIFFICULTY_INIT = '''		Global.customerCallTime = Array(16, 12, 8, 4, 20)[Global.difficulty];
		Global.setUpTime = Array(120, 40, 30, 30, 120)[Global.difficulty];
		Global.scoreDecrease = Array(Array(Null, Null, Null, Null, Null, Null), Array(5, Null, 5, 5, 5, 5),
			Array(15, Null, 15, 35, 15, 15), Array(50, Null, 50, 50, 50, 50))[Global.difficulty];
		Global.despawnTime = Array(30, 25, 20, 15, 60)[Global.difficulty];
		Global.additionalScore = Global.stageMode == 5 ? 15 : Array(Null, 5, 10, 15)[Global.difficulty];
		Global.failEnd = Array(99, 5, 3, 2, 3, 1)[Global.stageMode];
'''.replace("\n", "\r\n")


def combined_data_init_rule() -> str:
    return (
        'rule("Global subroutine: Deluxe dispatcher dataInit")\r\n'
        "{\r\n"
        "\tevent\r\n"
        "\t{\r\n"
        "\t\tSubroutine;\r\n"
        "\t\tdataInit;\r\n"
        "\t}\r\n\r\n"
        "\tactions\r\n"
        "\t{\r\n"
        + edition_phase_actions(("dataInit_org1", "dataInit_cafe1", "dataInit_gc1"))
        + edition_phase_actions(("dataInit_org2", "dataInit_cafe2", "dataInit_gc2"))
        + COMMON_INIT2
        + edition_phase_actions(("dataInit_org3", "dataInit_cafe3", "dataInit_gc3"))
        + "\t\tCall Subroutine(dataInit_customerCommon);\r\n"
        + "\t}\r\n"
        "}"
    )


def patch_customer_common(rule: str) -> str:
    close = "\r\n\t}\r\n}"
    if not rule.endswith(close):
        raise BuildError("customer common rule close not found")
    return rule[:-len(close)] + "\r\n" + COMMON_DIFFICULTY_INIT + close


OTHER_MENU_RULE = '''rule("Global subroutine: Other Menu")
{
	event
	{
		Subroutine;
		otherMenu;
	}

	actions
	{
		If(Global.totalScore[False] <= 2);
			Set Objective Description(All Players(All Teams), Custom String("로드 중..."), Visible To and String);
			Small Message(All Players(All Teams), Custom String("데이터 초기화 중..."));
			Global.potTime = Null;
			Global.fridgeCode = Empty Array;
			Wait(2, Ignore Condition);
			For Global Variable(despawnIndex, False, Count Of(Global.itemCode), True);
				Destroy Effect(Global.itemEffect[Global.despawnIndex]);
				Destroy In-World Text(Global.itemText[Global.despawnIndex]);
				Global.itemPosition[Global.despawnIndex] = Down;
				Global.itemCode[Global.despawnIndex] = -1;
				Global.itemCount -= True;
			End;
			Global.stageMode[0] = Global.totalScore[False];
			Call Subroutine(dataInit);
			Wait(0.016, Ignore Condition);
			Global.stage = 0;
			Call Subroutine(menuInit);
			Global.storageData = Mapped Array(String Split(Custom String("0/0/0/0/0/0/0/0"), Custom String("/")), Array(False, False, False));
			Global.potTime = Null;
			Set Objective Description(All Players(All Teams), Custom String("연습 모드"), Visible To and String);
		Else;
			Small Message(All Players(All Teams), Custom String("{0} 의 워크샵 코드는 {1} 입니다! ",
			Array(Null, Null, Null, Custom String("Joseon-뉴 3호점"), Custom String("Gummybear-오리지널"))[Global.totalScore[False]],
			Array(Null, Null, Null, Custom String("SSZ1Z1"), Custom String("8MAAN"))[Global.totalScore[False]]));
		End;
	}
}'''.replace("\n", "\r\n")


MENU_INIT_RULE = '''rule("Global subroutine: Menu init")
{
	event
	{
		Subroutine;
		menuInit;
	}

	actions
	{
		Global.totalScore[False] = Global.stage == 0 ? 0 : (Global.totalScore[False] + True) % Count Of(Global.FRIDGE_LIST);
		Global.currentMenu = Empty Array;
		Modify Global Variable(currentMenu, Append To Array, Global.MENU_LIST[Global.totalScore[False]]);
		Global.loadingMenu = Randomized Array(Global.currentMenu);
		Global.currentMenuHaz = Empty Array;
		Modify Global Variable(currentMenuHaz, Append To Array,
				Global.HAZARD_MENU_LIST[Global.totalScore[False]]);
		Global.loadingMenuHaz = Randomized Array(Global.currentMenuHaz);
		Global.currentMenuWeaver = Empty Array;
		Modify Global Variable(currentMenuWeaver, Append To Array,
				Global.WEAVER_MENU_LIST[Global.totalScore[False]]);
		Global.loadingMenuWeaver = Randomized Array(Global.currentMenuWeaver);
		Global.fridgeCode = Global.FRIDGE_LIST[Global.totalScore[False]];
	}
}'''.replace("\n", "\r\n")


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


PERK_HUD_RULE = r'''rule("Global subroutine: Perk Hud")
{
	event
	{
		Subroutine;
		perkHud;
	}

	actions
	{
		Abort If(Event Player.itemPerk == -1);
		Create HUD Text(Event Player, Custom String("〔{0}〕", Array(Input Binding String(Button(Ultimate)), Input Binding String(Button(Ultimate)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Secondary Fire)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Secondary Fire)),
				Input Binding String(Button(Ultimate)), Input Binding String(Button(Ultimate)),
				Input Binding String(Button(Secondary Fire)))[Event Player.itemPerk]),
			Custom String("{1}{0}", Array(True, True, False, False, False, False, True, True, False)[Event Player.itemPerk]
				? Custom String("") : Custom String("-{0}%", Round To Integer(Event Player.itemPerkDurability, Up)),
				Evaluate Once(Global.ITEM_NAME[Global.PERK_LIST[False][Event Player.itemPerk]])),
			Global.stageMode[1] < 2 ?
			Array(
				Custom String("100초간 도마에서 써는 속도와\r\n이동속도가 증가합니다"),
				Custom String("잠시 모든 시간이 느려지며\r\n칼+이속+조리기구 속도가 폭주합니다"),
				Custom String("손에 재료를 들고 사용하면\r\n재료의 신선도 회복합니다"),
				Custom String("필요 없는 재료를 빨아들여\r\n설거지로 부터 해방되세요"),
				Custom String("손에 재료를 들고 사용하면\r\n음식이 복사가 됩니다"),
				Custom String("{0}까지 가지 않아도\r\n재료를 구울 수 있습니다", Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴")),
				Custom String("햄스터가 아르바이트를 구한다\r\n라고 함"),
				Custom String("현재 라운드에 도움이 되는 재료 팩을 꺼냅니다\r\n팩은 칼로 뜯을 수 있습니다"),
				Custom String("제빙기까지 가지 않아도\r\n재료를 얼릴 수 있습니다"))[Event Player.itemPerk]
				: Custom String(" \r\n")
				, Right, 2,
			Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]],
			Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]], Color(White), String and Color, Default Visibility);
		Event Player.itemPerkText = Last Text ID;
	}
}'''.replace("\n", "\r\n")

KNIFE_HUD_RULE = r'''rule("Global subroutine: Knife Hud")
{
	event
	{
		Subroutine;
		knifeHud;
	}

	actions
	{
		If(Event Player.knifeCode == 0);
			Create HUD Text(Event Player, Custom String(" {1} - {0}% ", Round To Integer(Event Player.durability, Up),
				Global.ITEM_NAME[Global.KNIFE[Event Player.knifeCode]]), Global.stageMode[1] < 2 ? Custom String("다이소에서 파는\r\n평범한 칼입니다") : Custom String(" \r\n"), Null, Right, True, Custom Color(
				255 - Event Player.durability * 0.950, Event Player.durability * 2.320, Event Player.durability * 0.270, 255), Color(White), Null,
				String and Color, Default Visibility);
			Event Player.knifeText = Last Text ID;
		Else If(Event Player.knifeCode == 1);
			Create HUD Text(Event Player, Custom String(" {1} - {0}% ", Round To Integer(Event Player.durability, Up), Evaluate Once(
				Global.ITEM_NAME[Global.KNIFE[Event Player.knifeCode]])), Global.stageMode[1] < 2 ? Custom String("내구도와 성능이 무난한\r\n주방용 칼입니다") : Custom String(" \r\n"), Null, Right, True, Custom Color(
				255 - Event Player.durability * 1.860, Event Player.durability * 2.550, Event Player.durability * 0.870, 255), Color(White), Null,
				String and Color, Default Visibility);
			Event Player.knifeText = Last Text ID;
        Else If(Event Player.knifeCode == 6);
			Create HUD Text(Event Player, Custom String(" {1} - {0}% ", Round To Integer(Event Player.durability, Up), Evaluate Once(
				Global.ITEM_NAME[Global.KNIFE[Event Player.knifeCode]])), Global.stageMode[1] < 2 ? Custom String("재료를 손에 들고 바로 썰 수 있는\r\n전설적인 칼입니다") : Custom String(" \r\n"), Null, Right, True, Custom Color(
				Event Player.durability * 1.760, 0, Event Player.durability * 2.500, 255), Color(White), Null,
				String and Color, Default Visibility);
			Event Player.knifeText = Last Text ID;
		Else If(Event Player.knifeCode != -1);
			Create HUD Text(Event Player, Custom String(" {1} - {0}% ", Round To Integer(Event Player.durability, Up), Evaluate Once(
				Global.ITEM_NAME[Global.KNIFE[Event Player.knifeCode]])),
					Global.stageMode[1] < 2 ? Array(Null, Null,
					Custom String("내구도와 성능이 뛰어난\r\n고급 칼입니다"),
					Custom String("재료를 손에 들고 썰 수 있는\r\n희귀한 칼입니다"),
					Custom String("내구도와 성능이 압도적인\r\n희귀한 칼입니다"),
					Custom String("도마에서 아주 빠른 속도로\r\n연격할 수 있습니다"))[Event Player.knifeCode]
					: Custom String(" \r\n")
				 , Null, Right, True, Custom Color(
				255 - Event Player.durability * 2.250, Event Player.durability * 2.300, Event Player.durability * 1.510, 255), Color(White), Null,
				String and Color, Default Visibility);
			Event Player.knifeText = Last Text ID;
		End;
	}
}'''.replace("\n", "\r\n")


FOOT_HUD_RULE = r'''rule("Global subroutine: Foot Hud")
{
	event
	{
		Subroutine;
		footHud;
	}

	actions
	{
		Abort If(Event Player.footPerk == -1);
		Create HUD Text(Event Player,
			Custom String("〔{0}〕", Array(
				Input Binding String(Button(Jump)),
				Input Binding String(Button(Ability 1)),
				Input Binding String(Button(Ability 1))
			)[Event Player.footPerk]),
			Custom String("{1}{0}", Custom String("-{0}%",
			Round To Integer(Event Player.footPerkDurability, Up)),
			Evaluate Once(Global.ITEM_NAME[Global.PERK_LIST[True][Event Player.footPerk]])),
			Global.stageMode[1] < 2 ?
			Array(
				Custom String("공중에서 높게 점프하여\r\n높은 곳에 올라갈 수 있습니다"),
				Custom String("앞으로 빠르게 대시하는\r\n다재다능한 신발입니다"),
				Custom String("주문서에 있는 음식을 들고 사용하면\r\n테이블 앞으로 순간이동합니다"))[Event Player.footPerk]
				: Custom String(" \r\n")
			, Right, 3, Global.ITEM_COLOR[Global.PERK_LIST[True][Event Player.footPerk]], Global.ITEM_COLOR[Global.PERK_LIST[True][Event Player.footPerk]], Color(White),
				String and Color, Default Visibility);
		Event Player.footPerkText = Last Text ID;
	}
}'''.replace("\n", "\r\n")

DELUXE_BOOTSTRAP = '''		Global.stageMode = Array(0, 0);
		Global.DELUXE_DATA = Array(0);'''.replace("\n", "\r\n")


TOTAL_SCORE_INIT = '''		Global.totalScore = Array Slice(Array(
			Array(0, Custom String("연습 모드")), Array(6077, Custom String("JOSEON")),
			Array(6007, Custom String("JOSEON")), Array(0, Custom String("없음")),
			Array(10993, Custom String("JOSEON")), Array(4726, Custom String("REVENGE")),
			Array(0, Custom String("연습 모드")), Array(0, Custom String("없음")),
			Array(6083, Custom String("Joseon")), Array(14315, Custom String("REVENGE")),
			Array(0, Custom String("없음")), Array(0, Custom String("없음")),
			Array(0, Custom String("연습 모드")), Array(0, Custom String("없음")),
			Array(0, Custom String("없음")), Array(0, Custom String("없음")),
			Array(0, Custom String("없음")), Array(0, Custom String("없음"))), Global.stageMode[0] * 6, 6);'''.replace("\n", "\r\n")


def patch_global_setting(rule: str) -> str:
    rule = replace_once(
        rule,
        "\t\tDestroy All Dummy Bots;\r\n\t\tCall Subroutine(dataInit);",
        "\t\tDestroy All Dummy Bots;\r\n" + DELUXE_BOOTSTRAP + "\r\n\t\tCall Subroutine(dataInit);",
        "Deluxe bootstrap",
    )
    rule = replace_once(
        rule,
        "\t\tCall Subroutine(dataInit);\r\n\t\tCall Subroutine(dataInit2);",
        "",
        "defer data init until edition selection",
    )
    rule = replace_once(
        rule,
        "\t\tGlobal.DELUXE_DATA = Array(0);\r\n\r\n\t\tGlobal.itemPosition",
        "\t\tGlobal.DELUXE_DATA = Array(0);\r\n\t\tGlobal.itemPosition",
        "bootstrap action spacing",
    )
    rule = replace_once(
        rule,
        "\t\tGlobal.storageData = Array(Array(False, False, False), Array(False, False, False), Array(False, False, False), Array(False, False, False), Array(False, False, False), Array(False, False, False), Array(False, False, False), Array(False, False, False));",
        "\t\tGlobal.storageData = Mapped Array(String Split(Custom String(\"0/0/0/0/0/0/0/0\"), Custom String(\"/\")), Array(False, False, False));",
        "compact storage data",
    )
    rule = replace_once(
        rule,
        '\t\tGlobal.totalScore = Array(Array(0, Custom String("연습 모드")), Array(6077, Custom String("JOSEON")), Array(6007, Custom String("JOSEON")), Array(0, Custom String("없음")), Array(10993, Custom String("JOSEON")), Array(4726, Custom String("REVENGE")));\r\n',
        "",
        "defer edition total score until selection",
    )
    edition_hud_old = (
        '\t\tCreate HUD Text(All Players(Team 1), Null, Null, Custom String(\r\n'
        '\t\t\t"\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n"), Top, -999, Null, Null, Null, Visible To,\r\n'
        '\t\t\tDefault Visibility);'
    )
    # ITEM_COLOR for soy sauce: ORG code 77 and GC code 22 both resolve to
    # Custom Color(100, 60, False, 255).
    edition_hud_new = (
        edition_hud_old
        + '\r\n\t\tGlobal.globalText[0] = Last Text ID;\r\n'
        '\t\tCreate HUD Text(All Players(Team 1), Custom String(" 〔 {0} 〕 ", Array(Custom String("모듬회밥!"), '
        'Custom String("카페!"), Custom String("쿡제요리"))[Global.stageMode[0]]),\r\n'
        '\t\t\tCustom String("제작: {0}", Array(Custom String("Gummybear&변기클라우드\\r\\n난이도 : ★★★☆☆"), '
        'Custom String("Joseon&Deadlock\\r\\n난이도 : ★★☆☆☆"), Custom String("Joseon\\r\\n난이도 : ★★★★☆"))[Global.stageMode[0]]),\r\n'
        '\t\t\tLocal Player == Global.scbRank ? Custom String("[{0}]: 테마 변경", Input Binding String(Button(Ability 2))) '
        ': Custom String(" 방장이 테마를 결정하는 중입니다"), Top, -998, Array(Color(Orange), '
        'Custom Color(100, 60, False, 255), Color(Blue))[Global.stageMode[0]], Color(Yellow), Color(White), String and Color,\r\n'
        '\t\t\tDefault Visibility);\r\n'
        '\t\tGlobal.globalText[1] = Last Text ID;\r\n'
        '\t\tCreate HUD Text(All Players(Team 1), Null, Null, Custom String(\r\n'
        '\t\t\t"\\r\\n"), Top, -997, Null, Null, Null, Visible To,\r\n'
        '\t\t\tDefault Visibility);\r\n'
        '\t\tGlobal.globalText[2] = Last Text ID;'
    )
    rule = replace_once(rule, edition_hud_old, edition_hud_new, "edition selection HUD")
    rule = replace_once(
        rule,
        "\t\tGlobal.globalText[2] = Last Text ID;\r\n"
        "\t\tGlobal.globalText[False] = Last Text ID;",
        "\t\tGlobal.globalText[2] = Last Text ID;",
        "remove superseded edition spacer HUD slot",
    )
    rule = replace_once(
        rule,
        '결정하는 중입니다"), Top, -998, Custom Color(Array(255, 140, 110, 255, 255, 38)[Global.stageMode],',
        '결정하는 중입니다"), Top, -996, Custom Color(Array(255, 140, 110, 255, 255, 38)[Global.stageMode],',
        "mode HUD priority",
    )
    rule = replace_once(
        rule,
        '"\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n"),\r\n'
        '\t\t\tTop, -997, Null, Null, Null, Visible To, Default Visibility);',
        '"\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n"),\r\n'
        '\t\t\tTop, -995, Null, Null, Null, Visible To, Default Visibility);',
        "lower HUD spacer priority",
    )
    rule = replace_once(
        rule,
        "\t\tGlobal.globalText[True] = Last Text ID;",
        "\t\tGlobal.globalText[3] = Last Text ID;",
        "mode HUD slot",
    )
    rule = replace_once(
        rule,
        "\t\t\tTop, -995, Null, Null, Null, Visible To, Default Visibility);\r\n"
        "\t\tGlobal.globalText[2] = Last Text ID;",
        "\t\t\tTop, -995, Null, Null, Null, Visible To, Default Visibility);\r\n"
        "\t\tGlobal.globalText[4] = Last Text ID;",
        "lower HUD spacer slot",
    )
    rule = replace_once(
        rule,
        "\t\tGlobal.stageMode = 0;\r\n\t\tCall Subroutine(selectMode);\r\n\t\tGlobal.difficulty =",
        "\t\tGlobal.stageMode[1] = 1;\r\n\t\tCall Subroutine(selectMode);\r\n"
        "\t\tSet Objective Description(All Players(All Teams), Custom String(\"로드 중...\"), Visible To and String);\r\n"
        "\t\tSmall Message(All Players(All Teams), Custom String(\"데이터 초기화 중...\"));\r\n"
        + TOTAL_SCORE_INIT
        + "\r\n"
        "\t\tGlobal.difficulty =",
        "reload selected edition data",
    )
    rule = replace_once(
        rule,
        "\t\tCall Subroutine(dataInit3);",
        "\t\tCall Subroutine(dataInit);",
        "merged selected edition data init",
    )
    deluxe_patch_notes = r'''		Create In-World Text(Players Within Radius(Vector(206.991, 1, 188.239), 14, All Teams, Off),
		Custom String("{0} v260902\r\n\r\n{1}레스토랑 테마 통합\r\n  레스토랑 모듬회밥에 카페&디저트 와 쿡제요리가 통합되었습니다\r\n{2}", Icon String(Fire), Icon String(Plus),
		Custom String("  테마는 게임 진입시와 연습모드에서 변경할 수 있습니다")),
		Vector(213.2373, 3, 178.7080), 1, Do Not Clip, Visible To Position String and Color,
			Color(Red), Default Visibility);
		Create In-World Text(Players Within Radius(Vector(206.991, 1, 188.239), 14, All Teams, Off),
		Custom String("{0} 버그 수정\r\n\r\n{1}", Icon String(Flag),
		Custom String("  게임 시작 시 일부 모드의 추가 시작 아이템이 데이터 초기화 전에 생성되어 사라지는 문제를 수정했습니다.")),
		Vector(213.2373, 2, 178.7080), 1, Do Not Clip, Visible To Position String and Color,
			Color(White), Default Visibility);
		Create In-World Text(Filtered Array(Players Within Radius(Vector(217.370, 2.5, 172.520), 10, All Teams, Off), Current Array Element == Host Player),
			Global.difficulty == 4 ? Custom String("[{0}] - 연습모드용 아이템 생성", Input Binding String(Button(Ability 2))) : Custom String(""),
			Vector(217.370, 2.5, 172.520), 1, Do Not Clip, Visible To Position String and Color, Color(Orange), Default Visibility);'''.replace("\n", "\r\n")
    patch_notes_pattern = re.compile(
        r'\t\tCreate In-World Text\(Players Within Radius\(Vector\(206\.991, 1, 188\.239\), 14, All Teams, Off\),.*?'
        r'거대식가의 서빙 성공 보상이 5 -> 10 으로 증가하였습니다\..*?Color\(White\), Default Visibility\);',
        re.DOTALL,
    )
    rule, patch_notes_count = patch_notes_pattern.subn(lambda _: deluxe_patch_notes, rule, count=1)
    if patch_notes_count != 1:
        raise BuildError(f"Deluxe patch notes: expected exactly one match, got {patch_notes_count}")
    ice_label = '''		Create In-World Text(Players Within Radius(Vector(226.649, 2, 159.387), 10, Team 1, Off), Global.stageMode[0] == 1 ? Custom String("제빙기") :  Custom String(""),
			Vector(226.649, 3, 159.387), 3, Do Not Clip, Visible To and String, Color(Blue), Default Visibility);'''.replace("\n", "\r\n")
    pan_label = (
        '\t\tCreate In-World Text(Players Within Radius(Vector(224.926, 2, 158.167), 10, Team 1, Off), Custom String("팬"), Vector(224.926,\r\n'
        "\t\t\t2.750, 158.167), 3, Do Not Clip, Visible To, Color(Red), Default Visibility);"
    )
    rule = replace_once(rule, pan_label, pan_label + "\r\n" + ice_label, "ice-machine label position")
    rule = replace_once(
        rule,
        'Custom String("〔{0}〕:  물 내리기", Input Binding String(',
        'Custom String("〔{0}〕:  물 내리기  ", Input Binding String(',
        "sink interaction label spacing",
    )
    rule = replace_once(
        rule,
        'Local Player.knifeCode + True ? Custom String("〔{0}〕:  썰기", Input Binding String(Button(Interact))) : Custom String(\r\n'
        '\t\t\t"칼이 없습니다")',
        'Local Player.knifeCode + True ? Custom String("〔{0}〕:  썰기  ", Input Binding String(Button(Interact))) : Custom String(\r\n'
        '\t\t\t" 칼이 없습니다  ")',
        "cutting interaction label spacing",
    )
    rule = replace_once(
        rule,
        'Array(Custom String("Joseon-쿡제요리"), Custom String("Joseon-카페"), Custom String("Joseon-뉴 3호점"), Custom String("Gummybear-오리지널"))',
        'Array(Custom String("모듬회밥!"), Custom String("카페!"), Custom String("쿡제요리"), Custom String("Joseon-뉴 3호점"), Custom String("Gummybear-오리지널"))',
        "practice edition menu labels",
    )
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
    second_starter = (
        "\t\t\tGlobal.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50,\r\n"
        "\t\t\t\t-70)) * 0.100, Global.DELUXE_DATA[2][1][Global.stageMode], 100, Null);\r\n"
        "\t\t\tCall Subroutine(createItem);"
    )
    delayed_mode_starters = '''			If(Global.stageMode == 3);
				Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 63, 100, Null);
				Call Subroutine(createItem);
			Else If(Global.stageMode == 5);
				Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 354, 100, Null);
				Call Subroutine(createItem);
			End;'''.replace("\n", "\r\n")
    rule = replace_once(
        rule,
        second_starter,
        second_starter + "\r\n" + delayed_mode_starters,
        "delayed mode-specific starters",
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
    rule = replace_once(rule, old, new, "merged edition/mode input")
    rule = replace_once(
        rule,
        "\t\tDestroy HUD Text(Global.globalText[False]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[True]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[2]);",
        "\t\tDestroy HUD Text(Global.globalText[0]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[1]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[2]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[3]);\r\n"
        "\t\tDestroy HUD Text(Global.globalText[4]);",
        "selection HUD cleanup slots",
    )
    early_mode_starters = '''		If(Global.stageMode == 3);
			Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 63, 100, Null);
			Call Subroutine(createItem);
		Else If(Global.stageMode == 5);
			For Global Variable(scbRank, False, 6, True);
				All Players(Team 1)[Global.scbRank].dollar = 500;
				Wait(0.016, Ignore Condition);
			End;
			Global.fryingPower = 1.25;
			Global.grillingPower = 1.25;
			Global.potPower = 1;
			Global.panPower = 1.25;
			Global.createItemData = Array(Vector(217.370, 2, 172.520), Direction From Angles(Random Integer(False, 360), Random Integer(-50, -70)) * 0.100, 354, 100, Null);
			Call Subroutine(createItem);
		End;'''.replace("\n", "\r\n")
    delayed_mode_setup = '''		If(Global.stageMode == 5);
			For Global Variable(scbRank, False, 6, True);
				All Players(Team 1)[Global.scbRank].dollar = 500;
				Wait(0.016, Ignore Condition);
			End;
			Global.fryingPower = 1.25;
			Global.grillingPower = 1.25;
			Global.potPower = 1;
			Global.panPower = 1.25;
		End;'''.replace("\n", "\r\n")
    return replace_once(
        rule,
        early_mode_starters,
        delayed_mode_setup,
        "remove pre-data-init mode starters",
    )


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


def patch_spawn(rule: str) -> str:
    old = '''		Create In-World Text(Event Player, Array(Custom String("연습 모드"),
			Custom String("캐주얼 다이닝"), Custom String("파인 다이닝"), Custom String("스타 비스트로"), Custom String("마스터쿡 챌린지"), Custom String("헤드셰프 챌린지"))[Global.stageMode], Vector(222.559, 5.100, 164.417) + Direction From Angles((Evaluate Once(Total Time Elapsed)
			- Total Time Elapsed) * 5 + 200, 33.500), 1.500, Do Not Clip, Visible To Position String and Color, Color(Orange),
			Default Visibility);'''.replace("\n", "\r\n")
    new = '''		Create In-World Text(Event Player, Array(Custom String("모듬회밥!"), Custom String("카페!"), Custom String("쿡제요리"))[Global.stageMode[0]], Vector(222.559, 5.100, 164.417) + Direction From Angles((Evaluate Once(Total Time Elapsed)
			- Total Time Elapsed) * 5 + 200, 33.500), 1.500, Do Not Clip, Visible To Position String and Color, Color(Orange), Default Visibility);'''.replace("\n", "\r\n")
    rule = replace_once(rule, old, new, "spawn edition label")
    return replace_once(
        rule,
        'Custom String("GummyBear#11798\\r\\nMod : 변기클라우드#3523\\r\\nEnglish Version : HTNZ3")',
        'Custom String("한국어 : SPXXM\\r\\nEnglish : HTNZ3\\r\\n日本語 : 4ND1P")',
        "spawn language codes",
    )


def patch_control_item_hud(rule: str) -> str:
    replacements = {
        'Custom String("〔{0}〕:  칼 장착",': 'Custom String("〔{0}〕:  칼 장착  ",',
        'Custom String("〔{0}〕:  아이템 장착",': 'Custom String("〔{0}〕:  아이템 장착  ",',
        'Custom String("〔{0}〕:  줍기",': 'Custom String("〔{0}〕:  줍기  ",',
        'Custom String("〔{0}〕:  썰기",': 'Custom String("〔{0}〕:  썰기  ",',
    }
    for old, new in replacements.items():
        rule = replace_once(rule, old, new, f"control-item HUD spacing: {old}")
    return rule


def patch_interact(rule: str) -> str:
    old = '''					If(Global.stage == 5);
						Small Message(All Players(All Teams), Custom String("{0} 의 워크샵 코드는 {1} 입니다! ",
							Array(Custom String("Joseon-쿡제요리"), Custom String("Joseon-카페"), Custom String("Joseon-뉴 3호점"), Custom String("Gummybear-오리지널"))[Global.totalScore[False]],
							Array(Custom String("P6ZAA"), Custom String("WM3MW"), Custom String("SSZ1Z1"), Custom String("8MAAN"))[Global.totalScore[False]]));'''.replace("\n", "\r\n")
    new = '''					If(Global.stage == 5);
						Call Subroutine(otherMenu);'''.replace("\n", "\r\n")
    return replace_once(rule, old, new, "practice edition switching")


def patch_reload(rule: str) -> str:
    menu_setup = '''			Global.totalScore[False] = Global.stage == 0 ? 0 : (Global.totalScore[False] + True) % Count Of(Global.FRIDGE_LIST);
			Global.currentMenu = Empty Array;
			Modify Global Variable(currentMenu, Append To Array, Global.MENU_LIST[Global.totalScore[False]]);
			Global.loadingMenu = Randomized Array(Global.currentMenu);
			Global.currentMenuHaz = Empty Array;
			Modify Global Variable(currentMenuHaz, Append To Array,
					Global.HAZARD_MENU_LIST[Global.totalScore[False]]);
			Global.loadingMenuHaz = Randomized Array(Global.currentMenuHaz);
			Global.currentMenuWeaver = Empty Array;
			Modify Global Variable(currentMenuWeaver, Append To Array,
					Global.WEAVER_MENU_LIST[Global.totalScore[False]]);
			Global.loadingMenuWeaver = Randomized Array(Global.currentMenuWeaver);
			Global.fridgeCode = Global.FRIDGE_LIST[Global.totalScore[False]];'''.replace("\n", "\r\n")
    rule = replace_once(
        rule,
        menu_setup,
        "\t\t\tCall Subroutine(menuInit);",
        "shared practice menu initialization",
    )
    return replace_once(
        rule,
        "Global.totalScore[False] = (Global.totalScore[False] + True) % 4;",
        "Global.totalScore[False] = (Global.totalScore[False] + True) % 5;",
        "practice edition menu count",
    )


def patch_start_stage(rule: str) -> str:
    old = "\t\t\tCall Subroutine(dataInit3);"
    new = '''			If(Global.stageMode[0] == 0);
				Call Subroutine(dataInit_org3);
			Else If(Global.stageMode[0] == 1);
				Call Subroutine(dataInit_cafe3);
			Else;
				Call Subroutine(dataInit_gc3);
			End;
			Call Subroutine(dataInit_customerCommon);'''.replace("\n", "\r\n")
    return replace_once(rule, old, new, "difficulty-up phase3 refresh")


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
        + "\r\n\t\tElse;\r\n"
        + "\t\t\tIf(Global.stage == 0);\r\n"
        + "\t\t\t\tGlobal.currentCustomer = Array(Hero(Soldier: 76), Hero(Soldier: 76));\r\n"
        + "\t\t\t\tGlobal.hintText = Array(\r\n"
        + "\t\t\t\t\tCustom String(\"https://ow-restaurant.com/ko 에서\\r\\n이 테마의 레시피를 확인하실 수 있습니다.\")\r\n"
        + "\t\t\t\t);\r\n"
        + "\t\t\tEnd;\r\n"
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

    # Menu code 11 is ORG's butcher-restaurant stage, but CAFE and GC reuse
    # the same numeric code for unrelated menus. Keep every butcher-stage
    # runtime branch ORG-only while preserving LifeWeaver's independent
    # customer behavior across all editions.
    butcher_condition = (
        "Array Contains(Global.STAGE_CODE[Global.stage], 11) || "
        "(Global.difficulty == 4 && Global.totalScore[False] == 11)"
    )
    customer_condition = f"{butcher_condition} || Hero Of(Event Player) == Hero(LifeWeaver)"
    guarded_customer_condition = (
        f"(Global.stageMode[0] == 0 && ({butcher_condition})) || "
        "Hero Of(Event Player) == Hero(LifeWeaver)"
    )
    text = replace_once(
        text,
        customer_condition,
        guarded_customer_condition,
        "ORG butcher customer order behavior",
    )
    unguarded_butcher = re.compile(
        rf"(?<!Global\.stageMode\[0\] == 0 && \(){re.escape(butcher_condition)}"
    )
    text, guarded_count = unguarded_butcher.subn(
        f"Global.stageMode[0] == 0 && ({butcher_condition})",
        text,
    )
    if guarded_count != 3:
        raise BuildError(
            "ORG butcher runtime branches: expected three remaining matches, "
            f"got {guarded_count}"
        )
    return text


def build_text() -> str:
    source = data_builder.read_ow(BASE)
    source = replace_subroutine_declarations(source)
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
    text = modify_rule(text, "Global: Setting", patch_global_setting)
    text = modify_rule(text, "Player: Secondary fire button", patch_secondary)
    text = modify_rule(text, "Player: Ultimate button", patch_ultimate)
    text = modify_rule(text, "Player: Spawn", patch_spawn)
    text = modify_rule(text, "Player: Control item", patch_control_item_hud)
    text = modify_rule(text, "Player: Interact", patch_interact)
    text = modify_rule(text, "Player: Reload button", patch_reload)
    text = modify_rule(text, "Global subroutine: Item cooking", patch_item_cooking)
    text = modify_rule(text, "Global subroutine: Start stage", patch_start_stage)
    text = modify_rule(text, "Global subroutine: Set Hint Text", patch_set_hint)
    text = modify_rule(text, "Host Player: Select Mode", patch_select_mode)
    text = replace_subroutine_rule(text, "knifeHud", KNIFE_HUD_RULE)
    text = replace_subroutine_rule(text, "perkHud", PERK_HUD_RULE)
    text = replace_subroutine_rule(text, "footHud", FOOT_HUD_RULE)

    text = replace_subroutine_rule(text, "dataInit", "")
    text = replace_subroutine_rule(text, "dataInit2", "")
    text = replace_subroutine_rule(text, "dataInit3", combined_data_init_rule())

    text = patch_common_runtime(text)
    text = replace_once(
        text,
        'Array(Custom String("튀김기"), Custom String("솥"), Custom String("그릴"), Custom String("팬"))',
        'Array(Global.stageMode[0] == 1 ? Custom String("튀김기&제빙기") : Custom String("튀김기"), Custom String("솥"), Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Custom String("팬"))',
        "upgrade station label",
    )

    text = text.replace("v260827", "v260902").replace("v260828", "v260902").replace("v260829", "v260902")
    text = text.rstrip("\r\n") + "\r\n\r\n" + generated
    legacy_drink_name = "에너지 드링크/수상한 드링크/점프 부츠"
    release_drink_name = "에너지 드링크/싼데비슷한 드링크/점프 부츠"
    if text.count(legacy_drink_name) != 3:
        raise BuildError(
            f"Deluxe ITEM_NAME drink rename: expected 3, got {text.count(legacy_drink_name)}"
        )
    text = text.replace(legacy_drink_name, release_drink_name)
    text = replace_subroutine_rule(
        text,
        "dataInit_customerCommon",
        patch_customer_common(data_builder.find_rule(text, "dataInit_customerCommon")),
    )
    text = text.rstrip("\r\n") + "\r\n\r\n" + OTHER_MENU_RULE + "\r\n\r\n" + MENU_INIT_RULE + "\r\n"
    text = re.sub(r"\bGlobal\.stageMode\b(?!\[)", "Global.stageMode[1]", text)
    text = text.replace("Global.stageMode[1] = Array(0, 0);", "Global.stageMode = Array(0, 0);")
    summary_mode_old = '''Custom String("{0}", Array(Custom String("연습 모드"),
			Custom String("캐주얼 다이닝"), Custom String("파인 다이닝"), Custom String("스타 비스트로"), Custom String("마스터쿡 챌린지"), Custom String("헤드셰프 챌린지"))[Global.stageMode[1]])'''.replace("\n", "\r\n")
    summary_mode_new = '''Custom String("[{0}] {1}", Array(Custom String("모듬회밥!"), Custom String("카페!"), Custom String("쿡제요리"))[Global.stageMode[0]], Array(Custom String("연습 모드"),
			Custom String("캐주얼 다이닝"), Custom String("파인 다이닝"), Custom String("스타 비스트로"), Custom String("마스터쿡 챌린지"), Custom String("헤드셰프 챌린지"))[Global.stageMode[1]])'''.replace("\n", "\r\n")
    text = replace_once(text, summary_mode_old, summary_mode_new, "summary edition and mode label")
    text, serialized_ui_report = serialize_ui_string_arrays(text)
    text = re.sub(r"}(?:\r\n){3,}(?=rule\()", "}\r\n\r\n", text)
    text = re.sub(r"[ \t]+(?=\r\n)", "", text)
    text = re.sub(
        r"(?m)^( +)(?=\t)",
        lambda match: "\t" * (len(match.group(1)) // 4) + " " * (len(match.group(1)) % 4),
        text,
    )
    text = replace_once(
        text,
        "\t\t\tGlobal.KNIFE_DECREASE = Mapped Array(Global.KNIFE_DECREASE, Null);\r\n",
        "",
        "practice durability preservation",
    )
    text = replace_once(
        text,
        "\t\tSet Facing(Event Player, Vector(0.830, False, 0.560), To World);",
        "\t\tSet Facing(Event Player, Vector(0.830, False, 0.560), To World);\r\n"
        "\t\tAbort If(Global.superDrink < 0);",
        "guard Sandevistan reset",
    )
    text = replace_once(
        text,
        'Big Message(All Players(All Teams), Custom String("시공간이 뒤틀립니다!"));\r\n'
        "\t\t\tSet Move Speed(All Players(Team 1), 200);",
        'Big Message(All Players(All Teams), Custom String("{0}fgC72BD4FF>기초적인 임플란트 가동.", Global.tx));\r\n'
        "\t\t\tSet Move Speed(All Players(Team 1), 280);",
        "Sandevistan activation",
    )
    text = replace_once(
        text,
        "\t\t\tSet Slow Motion(50);",
        "\t\t\tSet Slow Motion(30);",
        "Sandevistan slow motion",
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
        "menuInit", "otherMenu",
    ):
        if len(re.findall(rf"(?mi)^[ \t]+{re.escape(name)};\r?$", text)) != 1:
            raise BuildError(f"generated subroutine event count mismatch: {name}")
    if text.count("Global.ICE_NEEDED =") != 1 or text.count("Global.ICE_RESULT =") != 2:
        raise BuildError("shared ICE_RESULT assignment count mismatch")
    if text.count("Global.CUSTOMER_LIST =") != 1:
        raise BuildError("shared CUSTOMER_LIST assignment count mismatch")
    customer_model = data_builder.parse_customer_list(
        re.sub(
            r"Global\.stageMode(?!\[)",
            "Global.stageMode[1]",
            data_builder.find_assignment(
                data_builder.find_rule(data_builder.read_ow(BASE), "dataInit3"),
                "CUSTOMER_LIST",
            ).expression,
        )
    )
    common_customer = data_builder.find_rule(text, "dataInit_customerCommon")
    if common_customer.count(data_builder.customer_decoder_loop(customer_model["palette"])) != 1:
        raise BuildError("serialized CUSTOMER_LIST decoder mismatch")
    if common_customer.count("For Global Variable(RAW_MIX, False, Count Of(Global.CUSTOMER_LIST), True);") != 1:
        raise BuildError("serialized CUSTOMER_LIST counter mismatch")
    if text.count("Call Subroutine(dataInit_customerCommon);") != 2:
        raise BuildError("shared customer/difficulty init call mismatch")
    serialized_list_count = len(data_builder.EDITION_SPECS) * len(
        data_builder.SERIALIZED_LIST_TABLES
    )
    if text.count("[Global.checkingIndex] = Mapped Array(") != serialized_list_count:
        raise BuildError("serialized menu-table decoder count mismatch")
    if re.search(r"Mapped Array\s*\([^;]*Mapped Array\s*\(", text, re.DOTALL):
        raise BuildError("nested Mapped Array remains in generated output")
    for edition in data_builder.EDITION_SPECS:
        block = data_builder.find_rule(text, f"dataInit_{edition}2")
        for table in data_builder.SERIALIZED_LIST_TABLES:
            expression = data_builder.find_assignment(block, table).expression
            decoded = data_builder.decode_serialized_list_expression(table, expression)
            if len(decoded) != 12:
                raise BuildError(f"{edition} {table} serialized group count mismatch")
            decoder = data_builder.serialized_list_decoder_loop(f"Global.{table}")
            if block.count(decoder) != 1:
                raise BuildError(f"{edition} {table} serialized decoder loop mismatch")
        phase3 = data_builder.find_rule(text, f"dataInit_{edition}3")
        if phase3.count(data_builder.deluxe_data_decoder_loop()) != 1:
            raise BuildError(f"{edition} DELUXE_DATA decoder loop mismatch")
    butcher_condition = (
        "Array Contains(Global.STAGE_CODE[Global.stage], 11) || "
        "(Global.difficulty == 4 && Global.totalScore[False] == 11)"
    )
    guarded_butcher_condition = f"Global.stageMode[0] == 0 && ({butcher_condition})"
    if text.count(guarded_butcher_condition) != 4:
        raise BuildError("ORG butcher-stage guard count mismatch")
    unguarded_butcher = re.compile(
        rf"(?<!Global\.stageMode\[0\] == 0 && \(){re.escape(butcher_condition)}"
    )
    if unguarded_butcher.search(text):
        raise BuildError("unguarded butcher-stage code 11 condition remains")
    for legacy_tutorial_bypass in (
        "If(Global.stageMode[0] != 0 && Global.difficulty == 4);",
        "If(Global.stageMode[0] != 0 && Global.stage == 0);",
        "Abort If(Global.stageMode[0] != 0);",
    ):
        if legacy_tutorial_bypass in text:
            raise BuildError(f"legacy tutorial bypass remains: {legacy_tutorial_bypass}")
    if text.count("https://ow-restaurant.com/ko 에서\\r\\n이 테마의 레시피를 확인하실 수 있습니다.") != 1:
        raise BuildError("CAFE/GC recipe hint mismatch")
    scalar_stage_mode = re.findall(r"\bGlobal\.stageMode\b(?!\[)", text)
    if scalar_stage_mode != ["Global.stageMode"] or text.count("Global.stageMode = Array(0, 0);") != 1:
        raise BuildError("stageMode must be an array with only [0]/[1] scalar access")
    for fragment in (
        "If(Is Button Held(Global.scbRank, Button(Ability 2)) || Is Button Held(Global.scbRank, Button(Reload)));",
        "Global.stageMode[0] = (Global.stageMode[0] + True) % 3;",
        "Global.stageMode[1] = (Global.stageMode[1] + True) % 6;",
        "\t\t\tLoop;\r\n\t\tEnd;\r\n\t\tDestroy HUD Text(Global.globalText[0]);",
        "\t\tCall Subroutine(selectMode);",
        "\t\tGlobal.storageLevel = Array(7, 3, 3, 0, -1, -1)[Global.stageMode[1]];\r\n"
        "\t\tCall Subroutine(dataInit);",
    ):
        if text.count(fragment) != 1:
            raise BuildError(f"combined edition/mode selector mismatch: {fragment}")
    if len(re.findall(r"(?mi)^[ \t]+dataInit[23];\r?$", text)) != 0:
        raise BuildError("retired dataInit2/dataInit3 subroutine event remains")
    if "Call Subroutine(dataInit2);" in text or "Call Subroutine(dataInit3);" in text:
        raise BuildError("retired dataInit2/dataInit3 call remains")
    if text.count("Call Subroutine(dataInit);") != 2:
        raise BuildError("merged dataInit call count mismatch")
    setting_start, setting_end = rule_span_by_title(text, "Global: Setting")
    select_start, select_end = rule_span_by_title(text, "Host Player: Select Mode")
    setting_rule = text[setting_start:setting_end]
    select_mode_rule = text[select_start:select_end]
    if setting_rule.count(TOTAL_SCORE_INIT) != 1:
        raise BuildError("edition totalScore initialization mismatch")
    total_score_at = setting_rule.find("Global.totalScore = Array Slice(Array(")
    if total_score_at < setting_rule.find("Call Subroutine(selectMode);"):
        raise BuildError("totalScore must initialize after edition selection")
    if total_score_at > setting_rule.find("Global.difficulty ="):
        raise BuildError("totalScore must initialize before difficulty")
    selection_slot_assignments = [
        setting_rule.find(f"Global.globalText[{index}] = Last Text ID;")
        for index in range(5)
    ]
    if -1 in selection_slot_assignments or selection_slot_assignments != sorted(selection_slot_assignments):
        raise BuildError("selection HUD slots are not assigned in creation order")
    for index in range(5):
        if setting_rule.count(f"Global.globalText[{index}] = Last Text ID;") != 1:
            raise BuildError(f"selection HUD slot {index} assignment mismatch")
        if select_mode_rule.count(f"Destroy HUD Text(Global.globalText[{index}]);") != 1:
            raise BuildError(f"selection HUD slot {index} cleanup mismatch")
    for assignment, expected in {
        "Global.MIXING_RECIPE = Mapped Array(Global.ITEM_NAME, Empty Array);": 1,
        "Global.UPGRADE_CODE = Array(Array(6, -1, -2)": 1,
        "Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7);": 1,
        "Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17, 19, 20)": 1,
        "Global.customerCallTime = Array(16, 12, 8, 4, 20)": 1,
    }.items():
        if text.count(assignment) != expected:
            raise BuildError(f"common dispatcher assignment count mismatch: {assignment}")
    for fragment, expected in {
        'Global.storageData = Mapped Array(String Split(Custom String("0/0/0/0/0/0/0/0"), Custom String("/")), Array(False, False, False));': 2,
        'Small Message(All Players(All Teams), Custom String("데이터 초기화 중..."));': 2,
        "Call Subroutine(menuInit);": 2,
        "Call Subroutine(otherMenu);": 1,
        "Abort If(Global.potTime[False] < 1);": 0,
        "Abort If(Global.potTime[True] < 1);": 0,
        "Start Rule(pot0, Restart Rule);": 1,
        "Start Rule(pot1, Restart Rule);": 1,
    }.items():
        if text.count(fragment) != expected:
            raise BuildError(f"practice edition reset mismatch: {fragment}")

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
    if [number for number, _ in subs_found] != list(range(len(SUBROUTINE_NAMES))):
        raise BuildError("subroutine IDs are not contiguous after dataInit merge")
    if tuple(name for _, name in subs_found) != SUBROUTINE_NAMES:
        raise BuildError("subroutine declaration order mismatch after dataInit merge")

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

    if any(version in text for version in ("v260827", "v260828", "v260829", "v260830")) or text.count("v260902") < 2:
        raise BuildError("project version was not updated consistently")
    if text.count(serialized_ui_expression("edition_names")) != 3:
        raise BuildError("Deluxe edition selector labels do not match ORG/CAFE/GC data")
    edition_color = (
        "Array(Color(Orange), Custom Color(100, 60, False, 255), Color(Blue))"
        "[Global.stageMode[0]]"
    )
    if text.count(edition_color) != 1:
        raise BuildError("Deluxe edition selector color mapping mismatch")
    for fragment in (
        'Global.stageMode[0] == 1 ? Custom String("제빙기") :  Custom String("")',
        'Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Vector(223.583,\r\n'
        '\t\t\t3, 157.286), 3, Do Not Clip, Visible To and String, Color(Orange)',
        'Global.stageMode[0] == 1 ? Custom String("{0} 팬:{1}% / 오븐:{2}%"',
        'Custom String("솥"), Global.stageMode[0] == 1 ? Custom String("오븐") : Custom String("그릴"), Custom String("팬")',
    ):
        if text.count(fragment) != 1:
            raise BuildError(f"CAFE oven label branch mismatch: {fragment}")
    for fragment in (
        "Global.stageMode[0] = Global.totalScore[False];",
        "If(Global.totalScore[False] <= 2);",
        "Call Subroutine(dataInit_customerCommon);",
    ):
        if fragment not in text:
            raise BuildError(f"runtime edition/difficulty reload mismatch: {fragment}")
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
                    "subroutines": len(SUBROUTINE_NAMES),
                    "selection_state": {"edition": "stageMode[0]", "mode": "stageMode[1]"},
                    "selection_inputs": {"edition": "Ability 2", "mode": "Reload", "confirm": "Jump"},
                    "practice_edition_reload": {
                        "dispatcher": "otherMenu",
                        "menu_initializer": "menuInit",
                        "storage_reset": True,
                        "pot_rules_restarted": True,
                    },
                    "workshop_elements": {
                        "last_measured_used": 32746,
                        "limit": 32768,
                        "last_measured_remaining": 22,
                        "current_output_measured_in_client": False,
                    },
                    "deluxe_data_slots": {
                        "1": "active item-perk drops",
                        "2": "edition runtime configuration",
                    },
                    "shared_customer_list": {
                        "source": "ORG/ko",
                        "dispatcher_call": True,
                        "serialized": True,
                        "hero_palette": 21,
                        "dynamic_rows": 3,
                    },
                    "serialized_deluxe_data": {
                        "slots": [1, 2],
                        "editions": sorted(data_builder.EDITION_SPECS),
                        "round_trip_checked": True,
                    },
                    "serialized_menu_tables": {
                        "tables": sorted(data_builder.SERIALIZED_LIST_TABLES),
                        "editions": sorted(data_builder.EDITION_SPECS),
                        "group_count_each": 12,
                        "round_trip_checked": True,
                    },
                    "serialized_ui_tables": {
                        "tables": {key: spec["count"] for key, spec in SERIALIZED_UI_TABLES.items()},
                        "max_segment_chars": MAX_UI_STRING_SEGMENT,
                    },
                    "ice_result_reuse": {"ORG": "MELT_LIST", "CAFE": "ice conversion"},
                    "tutorial_routing": {"ORG": "implemented", "CAFE": "empty", "GC": "empty"},
                    "source_rule_size_check": source_rule_size_check,
                    "create_item_sites": len(site_lines) - 1,
                    "control_flow_checked": True,
                    "preserved_legacy_implicit_end_rules": ["Player: Reload button"],
                    "version": "v260902",
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
