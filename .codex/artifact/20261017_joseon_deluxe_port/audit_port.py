import copy
import hashlib
import json
import random
import re
import sys
from read_tables import *

text=(ROOT/'Joseon_deluxe.ow').read_text()
manifest=json.loads((ART/'migration_manifest.json').read_text())
tables=[]
sources=[load_tables((ART/'inputs/n3_kr.ow').read_text()),load_tables((ART/'inputs/nc_kr.ow').read_text())]
for source, filename in zip(sources, ('n3_kr.ow', 'nc_kr.ow')):
    for field, corrections in manifest['source_corrections'].get(filename, {}).items():
        for index, value in corrections.items():
            source[field][int(index)] = value * 5 if field == 'ITEM_SCORE' else value
for label in ['N3','CAFE','GC']:
    t=load_tables(rule(text,'Global subroutine: Deluxe '+label+' init1')+rule(text,'Global subroutine: Deluxe '+label+' init2'))
    for k in MENU_FIELDS:
        if t[k] and isinstance(t[k][0],str):t[k]=[[int(i) for i in row.split(',')] for row in t[k]]
    tables.append(t)


def nested_codes(v):
    if isinstance(v,list):return [x for e in v for x in nested_codes(e)]
    return [] if v is None else [v]


for edition in [0,1]:
    src,dst=sources[edition],tables[edition]
    mapping={int(k):v for k,v in manifest['editions'][edition]['mapping'].items()}
    assert len(set(mapping.values()))==len(mapping)
    assert dst['ITEM_NAME'][21]=='물'
    for k,vals in src.items():
        if k in ITEM_FIELDS:
            for i,v in enumerate(vals):
                if i<=18 or (edition==1 and i==19):continue
                expected=map_nested(v,mapping) if k in RESULT_FIELDS else v
                assert dst[k][mapping[i]]==expected,(edition,k,i,dst[k][mapping[i]],expected)
        elif k in MENU_FIELDS:assert dst[k]==map_nested(vals,mapping),(edition,k)
        elif k=='RAW_MIX':assert dst[k]==[mapping[v//1000]*1000+mapping[v%1000] for v in vals]
        elif k=='RAW_RESULT':assert dst[k]==[mapping[v] for v in vals]
        else:assert dst[k]==vals,(edition,k)
    size=len(dst['ITEM_NAME'])
    for k in ITEM_FIELDS:assert len(dst[k])==size,(edition,k,len(dst[k]),size)
    for k in RESULT_FIELDS|MENU_FIELDS:
        assert all(isinstance(v,int) and 0<=v<size for v in nested_codes(dst[k])),(edition,k)
    print('DATA PASS',edition,size,'items',len(dst['RAW_MIX']),'mixed recipes')

assert all(t['ITEM_NAME'][21]=='물' for t in tables)
assert all(t['ITEM_COLOR'][21]==tables[0]['ITEM_COLOR'][21] for t in tables)
assert all(t['ITEM_SCORE'][21]==tables[0]['ITEM_SCORE'][21] for t in tables)
for k in RESULT_FIELDS-{'ADDITIONAL_MATERIAL_LIST'}:
    assert not any(nested_codes(tables[2].get(k,[]))),k
assert tables[2]['RAW_MIX']==tables[2]['RAW_RESULT']==[]
print('PLACEHOLDER PASS',len(tables[2]['ITEM_NAME']),'items; recipes empty')

# Check the actual tool pools rather than merely trusting edition branches.
for edition,label in enumerate(['N3','CAFE','GC']):
    block=rule(text,'Global subroutine: Deluxe '+label+' init3')
    active=parse_value(re.search(r'Global.DELUXE_DATA\[1\]\s*=\s*([^;]*);',block)[1],{})
    stock=parse_value(re.search(r'Global.DELUXE_DATA\[2\]\s*=\s*([^;]*);',block)[1],{})
    active=list(map(int,active))
    stock=[[None if v=='N' else int(v) for v in row.split(',')] for row in stock]
    assert 19 not in active and all(19 not in row for row in stock),(edition,active,stock)
    assert (20 in active)==(edition==1)
    assert len(stock[0])==len(stock[1])==6
assert 'Event Player.itemPerk == 7' not in text
assert 'Else If(Global.stageMode[0] == 1 && Event Player.itemPerk == 8);' in text
assert 'waterCode' not in text
assert 'Else If(Distance Between(Vector(233.820, 2.230, 167.720), Event Player.handPosition) < 1);' in rule(text,'Player: Control item')
assert 'Global.createItemData = Array(Vector(233.820, 2.230, 167.720), Vector(False, False, False), 21, Null, Null);' in text
assert 'Create In-World Text(Players Within Radius(Vector(233.820, 2.230, 167.720), 3, Team 1, Off),' in text
assert 'Create Effect(All Players(Team 1), Sphere, Color(Aqua), Vector(233.820, 2.230, 167.720),' in text
hint=rule(text,'Global subroutine: Set Hint Text')
assert not any(s in hint for s in ['Global.loadingMenu =','Global.currentMenu =','Global.currentCustomer ='])
assert 'https://ow-restaurant.com/ko' in hint
assert manifest['active_editions'] == [0, 1]
assert manifest['deferred_editions'] == [2]
assert 'Global.stageMode[False] + Is Button Held' in text and '% 2;' in rule(text,'Head Chefs: Select Mode')
assert not re.search(r'Call Subroutine\(dataInit_gc[123]\)', text)
assert tables[1]['ICE_RESULT'][:21]==[0]*21
print('RUNTIME REFERENCES PASS: active pools, shared water, box exclusion, cooling-gun ordinal and site-only tutorial')


def closure(t,seed):
    known=set(seed);changed=True
    while changed:
        previous=len(known)
        for k in ['CUTTING_RESULT','GRILLING_RESULT','FRYING_RESULT','POT_RESULT','PAN_RESULT','ICE_RESULT','IMPACT_RESULT']:
            for item in list(known):
                if item<len(t[k]):known.update(v for v in nested_codes(t[k][item]) if v>0)
        for pair,result in zip(t['RAW_MIX'],t['RAW_RESULT']):
            if pair//1000 in known and pair%1000 in known:known.add(result)
        changed=len(known)!=previous
    return known


unreachable=[];theme_report=[]
for edition,t in enumerate(tables[:2]):
    for theme,fridge in enumerate(t['FRIDGE_LIST']):
        base=set(fridge)|{21,0}
        reach=closure(t,base)
        misses={}
        for key in ['MENU_LIST','HAZARD_MENU_LIST','WEAVER_MENU_LIST']:
            missing=[]
            for item in t[key][theme]:
                available=reach
                if key=='WEAVER_MENU_LIST':available=closure(t,base|set(nested_codes(t['ADDITIONAL_MATERIAL_LIST'][item])))
                if item not in available:
                    missing.append({'id':item,'name':t['ITEM_NAME'][item]})
            if missing:misses[key]=missing
        theme_report.append({'edition':edition,'theme':theme,'name':t['STAGE_NAME'][theme],'orders':len(t['MENU_LIST'][theme]),'missing':misses})
        if misses:unreachable.append(theme_report[-1])
print('REACHABILITY',json.dumps(unreachable,ensure_ascii=False))

stage_report=[]
for edition in manifest['active_editions']:
    label = ['N3','CAFE','GC'][edition]
    expr=assignment(rule(text,'Global subroutine: Deluxe '+label+' init3'),'STAGE_CODE')
    for mode in range(6):
        stage_groups=None
        for seed in range(500):
            env={'Global.stageMode':[edition,mode],'__rng__':random.Random(seed)}
            stages=parse_value(expr,env)
            assert len(stages)==[6,15,15,15,13,20][mode],(edition,mode,len(stages))
            assert all(isinstance(v,int) and 0<=v<len(tables[edition]['STAGE_NAME']) for v in nested_codes(stages)),(edition,mode,stages)
            assert all(isinstance(group,list) and all(isinstance(v,int) for v in group) for group in stages),(edition,mode,stages)
            if stage_groups is None:stage_groups=[set() for _ in stages]
            for i,group in enumerate(stages):stage_groups[i].add(tuple(group))
        stage_report.append({'edition':edition,'mode':mode,'stage_count':len(stage_groups),'stages':[{'display':i+1,'index':i,'possible_themes':[list(t) for t in sorted(g)]} for i,g in enumerate(stage_groups)]})
print('STAGES PASS',len(stage_report),'edition/mode combinations, 500 seeds each')
if '--report' in sys.argv:
    (ART/'audit_result.json').write_text(json.dumps({'theme_checks':theme_report,'stage_checks':stage_report,'unreachable':unreachable},ensure_ascii=False,indent=2)+'\n')
