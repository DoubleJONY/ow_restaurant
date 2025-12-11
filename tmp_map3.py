import re, codecs
pat = re.compile(r'Custom String\("(.*?)"\)')
ko_text = codecs.open('ko.txt','r','utf-8').read()
en_text = codecs.open('en.txt','r','utf-8').read()
ko_strings = pat.findall(ko_text)
en_strings = pat.findall(en_text)
pairs = [(k,e) for k,e in zip(ko_strings,en_strings) if k!=e]
# unique order preserving
mapping = {}
for k,e in pairs:
    if k not in mapping:
        mapping[k]=e
print('unique diff', len(mapping))
from itertools import islice
for k,e in islice(mapping.items(),0,40):
    print(f'{k} => {e}')
