from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts" / "jp_deluxe" / "item_name_translations.tsv"
TARGET = ROOT / "scripts" / "jp_deluxe" / "item_name_translation_proposals.tsv"
HEADER = ("edition", "item_index", "kr", "en", "suggested_jp", "basis")


def parse_map(raw: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for line in raw.strip().splitlines():
        english, japanese, basis = line.split("\t")
        if english in result:
            raise RuntimeError(f"duplicate proposal key: {english}")
        result[english] = (japanese, basis)
    return result


FULL = parse_map(r"""
Freeze Gun	冷却銃	descriptive
Frozen Milk	冷凍ミルク	composed
Shaved Ice Base	かき氷ベース	descriptive
Sweet Red Beans	あんこ	localized
Red Bean Shaved Ice	パッピンス	localized
Soybean Powder	きな粉	localized
Injeolmi Shaved Ice	インジョルミピンス	localized
Red Bean Injeolmi Shaved Ice	インジョルミパッピンス	localized
Cookie Dough	クッキー生地	composed
Matcha Powder	抹茶パウダー	composed
Sliced Almonds	薄切りアーモンド	state_term
Roasted Almonds	ローストアーモンド	state_term
Bagel Dough	ベーグル生地	composed
Iced Chocolate	アイスチョコ	localized
Iced Mint Chocolate	アイスチョコミント	localized
Stretched Bread Dough	伸ばしたパン生地	state_term
Melted Sugar	溶かした砂糖	state_term
Glazed Donut	グレーズドドーナツ	localized
Black Tea Leaves	紅茶葉	composed
Brewed Tea Leaves	抽出済み茶葉	descriptive
Boiled Water	お湯	localized
Brown Sugar Pearls	黒糖タピオカ	localized
Cooked Tapioca Pearls	ゆでタピオカ	state_term
Bubble Tea	タピオカティー	localized
Almond Flour	アーモンドパウダー	composed
Mashed Butter	潰したバター	state_term
Crème Brûlée	クレームブリュレ	localized
Black Tea Powder	紅茶パウダー	composed
Meringue Cookie	メレンゲクッキー	composed
Macaron Batter	マカロン生地	composed
Macaron Shells	マカロンコック	localized
Soufflé Batter	スフレ生地	composed
Soufflé Pancake	スフレパンケーキ	localized
Strawberry Soufflé Pancake	イチゴスフレパンケーキ	composed
Blueberry Soufflé Pancake	ブルーベリースフレパンケーキ	composed
Creamed Butter	クリーム状バター	descriptive
Yogurt Powder	ヨーグルトパウダー	composed
Sweet Red Bean Bread	あんパン	localized
Choco Chip Bread	チョコチップパン	composed
Red Bean Butter Bun	あんバターパン	localized
Red Bean Butter Dough	あんバター生地	composed
Iced Condensed Milk Latte	アイス練乳ラテ	composed
Iced Tea (Extra Shot)	アイスティー（ショット追加）	descriptive
Cinnamon Powder	シナモンパウダー	composed
Taro Powder	タロイモパウダー	composed
Caramel Pudding	キャラメルプリン	localized
Glutinous Rice Flour	もち米粉	localized
Glutinous Rice Dough	もち米生地	composed
Glutinous Rice Donut	もち米ドーナツ	composed
Frozen Grapes	冷凍ブドウ	state_term
Fried Bread	揚げパン	localized
Twisted Donut	ねじりドーナツ	descriptive
Walnut Cake	クルミ菓子	descriptive
Matcha+Milk+Sugar	抹茶＋ミルク＋砂糖	composed
Oolong Tea Leaves+Milk+Sugar	ウーロン茶葉＋ミルク＋砂糖	composed
Black Tea Leaves+Milk+Sugar	紅茶葉＋ミルク＋砂糖	composed
Dried Herbs+Milk+Sugar	乾燥ハーブ＋ミルク＋砂糖	composed
Cheese Omelette	チーズオムレツ	localized
Bacon & Eggs	ベーコンエッグ	localized
Tart Dough	タルト生地	composed
Baked Tart Shell	焼いたタルト台	state_term
Raw Walnut Pie	クルミパイ（焼く前）	state_term
Raw Strawberry Pie	イチゴパイ（焼く前）	state_term
Raw Apple Pie	アップルパイ（焼く前）	state_term
Apple Pie	アップルパイ	localized
Raw Blueberry Pie	ブルーベリーパイ（焼く前）	state_term
Raw Walnut Tart	クルミタルト（焼く前）	state_term
Raw Egg Tart	エッグタルト（焼く前）	state_term
Raw Cream Cheese Tart	クリームチーズタルト（焼く前）	state_term
Apple Tart	アップルタルト	localized
Apple Tea	アップルティー	localized
Apple Juice	アップルジュース	localized
Apple Fizz	アップルソーダ	localized
Lemon Fizz	レモンソーダ	localized
Grapefruit Fizz	グレープフルーツソーダ	localized
Strawberry Fizz	イチゴソーダ	localized
Blueberry Fizz	ブルーベリーソーダ	localized
Mango Fizz	マンゴーソーダ	localized
Grilled Beef	焼いた牛肉	state_term
Stir-fried Beef	炒めた牛肉	state_term
Sliced Boiled Beef	薄切りしたゆで牛肉	state_term
Beef Short Rib Soup	カルビタン	localized
Char-grilled Pork Trotters	チョッパルの直火焼き	localized
Rice Soup	クッパ	localized
Beef Rice Soup	牛肉クッパ	localized
Pork Rice Soup	ポーククッパ	localized
Pork Belly Rice Bowl	サムギョプサル丼	localized
Beef Bulgogi	牛プルコギ	localized
Pork Bulgogi	ポークプルコギ	localized
Marinated Pork	ポークの甘辛炒め	descriptive
Soy Sauce Rice	醤油ご飯	composed
Sliced Tuna	捌いたマグロ	state_term
Soy Sauce Marinated Tuna	マグロ漬け	localized
Tuna Rice Bowl	鉄火丼	localized
Sliced Eel	捌いたウナギ	state_term
Sweet&Spicy Grilled Eel	ウナギの蒲焼き	localized
Eel Rice Bowl	うな丼	localized
Egg & Eel Rice Bowl	うな玉丼	localized
Salmon	サーモン	localized
Sliced Salmon	捌いたサーモン	state_term
Salmon Sashimi	サーモンの刺身	localized
Salmon Sushi	サーモン寿司	localized
Soy Sauce Marinated Salmon	サーモン漬け	localized
Salmon Rice Bowl	サーモン丼	localized
Soy Sauce Egg Rice	卵かけご飯	localized
Rice Dough	米粉生地	descriptive
Rolled Rice Dough	伸ばした米粉生地	state_term
Rice Paper	ライスペーパー	localized
Soaked Rice Paper	水で戻したライスペーパー	state_term
Raw Meat Spring Roll	生肉チャーゾー	descriptive
Fried Meat Spring Roll	肉チャーゾー	localized
Raw Shrimp Spring Roll	生エビチャーゾー	descriptive
Fried Shrimp Spring Roll	エビチャーゾー	localized
Fresh Spring Roll Base	生春巻きベース	descriptive
Vegetable Fresh Spring Roll	野菜の生春巻き	descriptive
Meat Fresh Spring Roll	肉入り生春巻き	descriptive
Shrimp Fresh Spring Roll	エビの生春巻き	descriptive
Shrimp Rice Noodle Soup	エビフォー	localized
Vegetable Pad Thai	野菜パッタイ	descriptive
Shrimp Pad Thai	エビパッタイ	descriptive
Bun cha	ブンチャー	localized
Curry Powder	カレーパウダー	composed
Char-grilled Whole Chicken	丸鶏の直火焼き	descriptive
Tandoori Chicken	タンドリーチキン	localized
Boiled Chickpeas	ゆでひよこ豆	state_term
Chickpea Curry	ひよこ豆カレー	descriptive
Bean Rice	豆ご飯	descriptive
Chickpea Pilaf	ひよこ豆ピラフ	descriptive
Chicken Pilaf	チキンピラフ	localized
Lamb Pilaf	ラムピラフ	localized
Beef Pilaf	ビーフピラフ	localized
Chicken Curry	チキンカレー	localized
Lamb Curry	ラムカレー	localized
Cooked Rice	炊いた米	state_term
Donjang Sauce	テンジャンソース	localized
Grilled Pork Intestines	ポークホルモン焼き	descriptive
Bread Pieces	パン切れ	descriptive
Hash Browns	ハッシュドポテト	localized
Potato Pancake	ジャガイモチヂミ	descriptive
Cheese Potato Pancake	チーズジャガイモチヂミ	descriptive
Pork Trotters Set	チョッパル定食	localized
Sausage Platter	ソーセージ盛り合わせ	descriptive
Potato Salad	ポテトサラダ	localized
Raw Cutlet	生カツレツ	state_term
Cutlet	カツレツ	localized
Raw Meatball	生ミートボール	state_term
Mulled Wine	ホットワイン	localized
Stewed Apples	リンゴの甘煮	descriptive
Raw Meat Pie	ミートパイ（焼く前）	state_term
Raw Beef Wellington	ビーフウェリントン（焼く前）	state_term
Beef Wellington	ビーフウェリントン	localized
Batter	衣	localized
Raw Scotch Egg	生スコッチエッグ	state_term
Scotch Egg	スコッチエッグ	localized
Egg Tart	エッグタルト	localized
Raw Apple Tart	アップルタルト（焼く前）	state_term
Raw Apple Jam Tart	リンゴジャムタルト（焼く前）	state_term
Bulgogi Kimbap	プルコギキンパ	localized
Spicy Pork Kimbap	ジェユクキンパ	localized
Seasoned Raw Beef	ユッケ	localized
Galbi Marinade	カルビだれ	localized
Beef Short Ribs	牛カルビ	localized
Pork Ribs	ポークカルビ	localized
Tuna Gunkan Sushi	マグロ軍艦巻き	localized
Raw Shrimp Sushi	生エビ寿司	localized
Tom Yum Goong	トムヤムクン	localized
Tom Yum Goong Noodle Soup	トムヤムクンフォー	localized
Beef Rice Noodle Soup	牛肉フォー	localized
Chicken Rice Noodle Soup	鶏肉フォー	localized
Chicken Cheeseburger	チキンチーズバーガー	localized
Vindaloo Curry	ヴィンダルーカレー	localized
Vongole Risotto	ボンゴレリゾット	localized
Curried Sausage	カレーソーセージ	descriptive
Raw Blood Sausage	生スンデ	state_term
Blood Sausage	スンデ	localized
Pie and Mash	パイ・アンド・マッシュ	localized
Raw Sardine Pie	イワシパイ（焼く前）	state_term
Raw Shrimp Patty	生エビパティ	state_term
Shrimp Patty	エビパティ	descriptive
Whole Apple Tanghulu	丸ごとリンゴ飴	localized
Bread Rusk	パンラスク	localized
Sugar Toast	シュガートースト	localized
Apple Tanghulu	リンゴ飴	localized
French Toast	フレンチトースト	localized
Apple Jam Toast	リンゴジャムトースト	composed
Choco-Dipped Apple	チョコリンゴ	descriptive
Chocolate Toast	チョコトースト	composed
Choco-Dipped Berry	チョコイチゴ	descriptive
Strawberry Jam Toast	イチゴジャムトースト	composed
Raw Cheese Stick	生チーズスティック	composed
Banana Choco Toast	バナナチョコトースト	composed
Lamb Skewers	ラム串焼き	localized
Spicy Vegetable Broth	辛口野菜だし	descriptive
Mild Lamb Hotpot	ラムの白湯火鍋	descriptive
Spicy Lamb Hotpot	ラムの麻辣火鍋	descriptive
Mild Pork Hotpot	ポークの白湯火鍋	descriptive
Spicy Pork Hotpot	ポークの麻辣火鍋	descriptive
Soy-braised Pork	ポークの醤油煮	descriptive
Soy-grilled Pork	ポークの醤油焼き	descriptive
Doubanjiang Marinade	豆板醤だれ	descriptive
Doubanjiang Stir-fried Vegetables	野菜の豆板醤炒め	descriptive
Doubanjiang Stir-fried Lamb	ラムの豆板醤炒め	descriptive
Doubanjiang Stir-fried Pork	ポークの豆板醤炒め	descriptive
Mild Beef Hotpot	牛肉の白湯火鍋	descriptive
Spicy Beef Hotpot	牛肉の麻辣火鍋	descriptive
Doubanjiang Stir-fried Beef	牛肉の豆板醤炒め	descriptive
Doubanjiang Stir-fried Shrimp	エビの豆板醤炒め	descriptive
Tortilla Pieces	トルティーヤ片	descriptive
Taco Base	タコスベース	descriptive
Gambas Taco	ガンバスタコス	localized
Chicken Taco	チキンタコス	localized
Chicken Quesadilla	チキンケサディーヤ	localized
Lamb Taco	ラムタコス	localized
Lamb Quesadilla	ラムケサディーヤ	localized
Boiled Lamb	ゆでラム肉	state_term
Sliced Boiled Lamb	薄切りしたゆでラム肉	state_term
Sliced Sardine	捌いたイワシ	state_term
Beef Stew	ビーフシチュー	localized
Chicken Stew	チキンシチュー	localized
Tomato Lamb Stew	ラムのトマトシチュー	localized
Lamb Stew	ラムシチュー	localized
Boiled Lamb Taco	ゆでラム肉タコス	composed
PD+Beef+PD	パイ生地＋牛肉＋パイ生地	composed
PD+Apple+PD	パイ生地＋リンゴ＋パイ生地	composed
PD+Sardine+PD	パイ生地＋イワシ＋パイ生地	composed
B+Chicken+C	パン＋チキン＋チーズ	composed
B+Bulgogi	パン＋プルコギ	composed
B+Shrimp	パン＋エビ	composed
""")


SPECIAL_KR = {
    "치즈 붕어빵": ("チーズプンオパン", "localized"),
    "피자 붕어빵": ("ピザプンオパン", "localized"),
    "붕어빵": ("プンオパン", "localized"),
    "슈크림 붕어빵": ("カスタードプンオパン", "localized"),
    "초코 붕어빵": ("チョコプンオパン", "localized"),
    "앙버터 붕어빵": ("あんバタープンオパン", "localized"),
    "팥절미 붕어빵": ("インジョルミあんこプンオパン", "localized"),
    "오 레": ("オ・レ", "wordplay"),
}


ATOMS = {
    "Beef": "牛肉", "Pork": "ポーク", "Lamb": "ラム肉", "Chicken": "鶏肉", "Meat": "ミート",
    "Shrimp": "エビ", "Tuna": "マグロ", "Eel": "ウナギ", "Salmon": "サーモン", "Sardine": "イワシ",
    "Clams": "アサリ", "Vegetables": "野菜", "Broth": "出汁", "Soy Sauce": "醤油",
    "Sweet&Spicy Sauce": "ヤンニョムソース", "Curry": "カレー", "Cream": "クリーム",
    "Creamy Tomato": "トマトクリーム", "Tomato": "トマト", "Wine": "ワイン", "Pasta": "パスタ",
    "Cooked Rice": "炊いた米", "Rice": "ご飯", "Rice Noodles": "ライスヌードル", "Noodles": "麺",
    "Potato": "ジャガイモ", "Pickled Cabbage": "キャベツの漬物", "Sausage": "ソーセージ",
    "Cheese": "チーズ", "Pie Dough": "パイ生地", "Pastry Dough": "パイ生地", "Apple": "リンゴ",
    "Egg": "卵", "Seaweed": "海苔", "Bulgogi": "プルコギ", "Spicy Pork": "ジェユク",
    "Galbi Marinade": "カルビだれ", "Doubanjiang": "豆板醤", "Tortilla": "トルティーヤ",
    "Fresh Spring Roll": "生春巻き", "Pork Trotters": "チョッパル", "Steak": "ステーキ",
    "Okra": "オクラ", "Patty": "パティ", "Cookie Dough": "クッキー生地",
    "Bread": "パン", "Sugar": "砂糖", "Water": "水", "Strawberry": "イチゴ",
    "Blueberry": "ブルーベリー", "Mango": "マンゴー", "Banana": "バナナ", "Melon": "メロン",
    "Grapes": "ブドウ", "Lemon": "レモン", "Grapefruit": "グレープフルーツ",
    "Chocolate": "チョコ", "Choco": "チョコ", "Chocolate Chips": "チョコチップ", "Milk": "ミルク",
    "Yogurt": "ヨーグルト", "Vanilla": "バニラ", "Matcha": "抹茶", "Oolong": "ウーロン",
    "Herbal": "ハーブ", "Herbs": "ハーブ", "Black Tea": "紅茶", "Black Tea Leaves": "紅茶葉",
    "Tea Leaves": "茶葉", "Oolong Tea Leaves": "ウーロン茶葉", "Dried Herbs": "乾燥ハーブ",
    "Tapioca Pearls": "タピオカ", "Almond": "アーモンド", "Sweet Red Bean": "あんこ",
    "Red Bean": "あんこ", "Injeolmi": "インジョルミ", "Walnut": "クルミ", "Butter": "バター",
    "Egg White": "卵白", "Egg Yolk": "卵黄", "Whipped Cream": "生クリーム",
    "Custard Cream": "カスタードクリーム", "Cream Cheese": "クリームチーズ",
    "Condensed Milk": "練乳", "Marshmallow": "マシュマロ", "Cinnamon": "シナモン",
    "Bacon": "ベーコン", "Scrambled Eggs": "スクランブルエッグ", "Muffin": "マフィン",
    "Dough": "生地", "Taro": "タロイモ", "Coffee Cubes": "コーヒーキューブ",
}


MODIFIERS = {
    "Strawberry Chocolate": "イチゴチョコ", "Matcha Red Bean": "抹茶あんこ",
    "Matcha Chocolate": "抹茶チョコ", "Mint Chocolate": "チョコミント",
    "Chocolate Chip": "チョコチップ", "Almond Choco Chip": "アーモンドチョコチップ",
    "Whole Almond": "丸ごとアーモンド", "Brown Sugar": "黒糖", "Earl Grey": "アールグレイ",
    "Strawberry Banana": "イチゴバナナ", "Mango Banana": "マンゴーバナナ",
    "Mixed Berry": "ミックスベリー", "Strawberry Yogurt": "イチゴヨーグルト",
    "Blueberry Yogurt": "ブルーベリーヨーグルト", "Mango Yogurt": "マンゴーヨーグルト",
    "Banana Yogurt": "バナナヨーグルト", "Chocolate Yogurt": "チョコヨーグルト",
    "Melon Yogurt": "メロンヨーグルト", "Strawberry Cream Cheese": "イチゴクリームチーズ",
    "Red Bean Butter": "あんバター", "Yogurt Cream": "ヨーグルトクリーム",
    "Coffee Cube": "コーヒーキューブ", "Cream Cheese": "クリームチーズ",
    "Glutinous Rice": "もち米", "Chocolate Syrup": "チョコシロップ",
    "Chocolate Cream": "チョコクリーム", "Strawberry Cream": "イチゴクリーム",
    "Vanilla Cream": "バニラクリーム", "Matcha Cream": "抹茶クリーム",
    "Strawberry Jam": "イチゴジャム", "Blueberry Jam": "ブルーベリージャム",
    "Meat Sauce": "ミートソース", "Tomato Beef": "トマトビーフ", "Cream Beef": "クリームビーフ",
    "Tomato Chicken": "トマトチキン", "Cream Chicken": "クリームチキン",
    "Tomato Okra Beef": "トマトオクラビーフ", "Tomato Okra": "トマトオクラ",
    "Tomato Lamb": "トマトラム", "Vegetable": "野菜", "Apple Jam": "リンゴジャム",
    "Raw Egg": "生エッグ", "Caramel": "キャラメル",
}


SUFFIXES = (
    (" Yogurt Ice Cream", "ヨーグルトアイス"), (" Ice Cream", "アイス"),
    (" Yogurt Smoothie", "ヨーグルトスムージー"), (" Smoothie", "スムージー"),
    (" Shaved Ice", "かき氷"), (" Cookie Dough", "クッキー生地"), (" Cookie", "クッキー"),
    (" Bagel Dough", "ベーグル生地"), (" Bagel", "ベーグル"), (" Pancake", "パンケーキ"),
    (" Donut", "ドーナツ"), (" Filling", "フィリング"), (" Macaron", "マカロン"),
    (" Frappe", "フラッペ"), (" Bubble Tea", "タピオカティー"), (" Milk Tea", "ミルクティー"),
    (" Latte", "ラテ"), (" Cream", "クリーム"), (" Bread", "パン"), (" Muffin", "マフィン"),
    (" Pie", "パイ"), (" Tart", "タルト"), (" Juice", "ジュース"), (" Tea", "ティー"),
    (" Syrup", "シロップ"), (" Shake", "シェイク"), (" Parfait", "パフェ"),
    (" Risotto", "リゾット"), (" Pasta", "パスタ"), (" Stew Base", "シチューベース"),
    (" Stew", "シチュー"), (" Curry", "カレー"), (" Pilaf", "ピラフ"),
    (" Rice Bowl", "丼"), (" Noodle Soup", "麺スープ"), (" Soup", "スープ"),
    (" Sushi", "寿司"), (" Sandwich", "サンドイッチ"), (" Cheeseburger", "チーズバーガー"),
    (" Burger", "バーガー"), (" Quesadilla", "ケサディーヤ"), (" Taco", "タコス"),
    (" Nachos", "ナチョス"), (" Hot Dog", "ホットドッグ"), (" Fondue", "フォンデュ"),
    (" Toast", "トースト"), (" Powder", "パウダー"), (" Salad", "サラダ"),
)


PREFIXES = (
    ("Raw ", "生"), ("Frozen ", "冷凍"), ("Sliced ", "薄切り"), ("Grilled ", "焼いた"),
    ("Stir-fried ", "炒めた"), ("Boiled ", "ゆで"), ("Smoked ", "燻製"),
    ("Roasted ", "ロースト"), ("Steamed ", "蒸し"), ("Minced ", "みじん切り"),
    ("Toasted ", "トースト"),
)


def modifier(text: str) -> str:
    if text in MODIFIERS:
        return MODIFIERS[text]
    if text in ATOMS:
        return ATOMS[text]
    words = text.split()
    rendered: list[str] = []
    index = 0
    phrases = sorted(set(MODIFIERS) | set(ATOMS), key=lambda value: len(value.split()), reverse=True)
    while index < len(words):
        for phrase in phrases:
            parts = phrase.split()
            if words[index:index + len(parts)] == parts:
                rendered.append(MODIFIERS.get(phrase, ATOMS.get(phrase, "")))
                index += len(parts)
                break
        else:
            raise KeyError(text)
    return "".join(rendered)


def component(text: str) -> str:
    if text in FULL:
        return FULL[text][0]
    if text in ATOMS:
        return ATOMS[text]
    for prefix, japanese in PREFIXES:
        if text.startswith(prefix):
            return japanese + component(text[len(prefix):])
    for suffix, japanese in SUFFIXES:
        if text.endswith(suffix):
            return modifier(text[:-len(suffix)]) + japanese
    return modifier(text)


def translate(edition: str, kr: str, en: str) -> tuple[str, str]:
    if kr in SPECIAL_KR:
        return SPECIAL_KR[kr]
    if en in FULL:
        return FULL[en]
    if "+" in en:
        return "＋".join(component(part.strip()) for part in en.split("+")), "composed"
    return component(en), "composed"


def build_rows() -> list[dict[str, str]]:
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle, delimiter="\t"))

    proposals: list[dict[str, str]] = []
    failures: list[tuple[str, str, str, str]] = []
    for row in source_rows:
        if row["jp"]:
            continue
        try:
            suggestion, basis = translate(row["edition"], row["kr"], row["en"])
        except KeyError:
            failures.append((row["edition"], row["item_index"], row["kr"], row["en"]))
            continue
        if re.search(r"[A-Za-z]", suggestion):
            failures.append((row["edition"], row["item_index"], row["kr"], row["en"]))
            continue
        if "豚" in suggestion:
            raise RuntimeError(f"forbidden Japanese character: {row!r} -> {suggestion!r}")
        proposals.append(
            {
                "edition": row["edition"], "item_index": row["item_index"],
                "kr": row["kr"], "en": row["en"],
                "suggested_jp": suggestion, "basis": basis,
            }
        )
    if failures:
        details = "\n".join("\t".join(row) for row in failures)
        raise RuntimeError(f"untranslated proposal rows: {len(failures)}\n{details}")
    return proposals


def render(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def validate_applied_proposals() -> tuple[int, str]:
    if not TARGET.exists():
        raise RuntimeError(f"missing applied proposal record: {TARGET}")
    with TARGET.open("r", encoding="utf-8", newline="") as handle:
        proposals = list(csv.DictReader(handle, delimiter="\t"))
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle, delimiter="\t"))

    source_by_key = {
        (row["edition"], row["item_index"], row["kr"], row["en"]): row["jp"]
        for row in source_rows
    }
    for proposal in proposals:
        key = (
            proposal["edition"], proposal["item_index"],
            proposal["kr"], proposal["en"],
        )
        if source_by_key.get(key) != proposal["suggested_jp"]:
            raise RuntimeError(f"proposal is not applied to the translation table: {key!r}")
    digest = hashlib.sha256(TARGET.read_bytes()).hexdigest().upper()
    return len(proposals), digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build JP ITEM_NAME suggestions for blank rows.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = build_rows()
    if not rows:
        count, digest = validate_applied_proposals()
        print(f"applied check ok: rows={count} sha256={digest}")
        return 0
    expected = render(rows)
    digest = hashlib.sha256(expected).hexdigest().upper()
    result = f"rows={len(rows)} sha256={digest}"
    if args.check:
        if not TARGET.exists() or TARGET.read_bytes() != expected:
            print(f"mismatch: {TARGET}", file=sys.stderr)
            return 1
        print(f"check ok: {result}")
        return 0
    TARGET.write_bytes(expected)
    print(f"wrote {TARGET}: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
