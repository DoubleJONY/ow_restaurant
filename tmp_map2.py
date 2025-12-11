import re, codecs
pat = re.compile(r'Custom String\("(.*?)"\)')
ko_text = codecs.open('ko.txt','r','utf-8').read()
en_text = codecs.open('en.txt','r','utf-8').read()
ko_strings = pat.findall(ko_text)
en_strings = pat.findall(en_text)
print('counts', len(ko_strings), len(en_strings))
pairs = list(zip(ko_strings, en_strings))
# filter differing
pairs = [(k,e) for k,e in pairs if k!=e]
from collections import OrderedDict
mapping = OrderedDict()
for k,e in pairs:
    mapping.setdefault(k, e)
print('unique diff', len(mapping))
for k,e in list(mapping.items())[:30]:
    print(k.encode('unicode_escape').decode(), '=>', e.encode('unicode_escape').decode())
