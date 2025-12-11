import re, codecs
pat = re.compile(r'Custom String\("(.*?)"\)')
ko_set = set(pat.findall(codecs.open('ko.txt','r','utf-8').read()))
en_set = set(pat.findall(codecs.open('en.txt','r','utf-8').read()))
print('ko count', len(ko_set), 'en count', len(en_set))
missing_in_ko = sorted(en_set - ko_set)[:20]
missing_in_en = sorted(ko_set - en_set)[:20]
print('only in en', len(en_set - ko_set))
for s in missing_in_ko[:15]:
    print('EN only:', s)
print('only in ko', len(ko_set - en_set))
for s in missing_in_en[:15]:
    print('KO only:', s)
