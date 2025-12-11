import re, codecs
pat = re.compile(r'Custom String\("(.*?)"\)')
ko = codecs.open('ko.txt','r','utf-8').read()
en = codecs.open('en.txt','r','utf-8').read()
ks = pat.findall(ko)
es = pat.findall(en)
pairs=[(k,e) for k,e in zip(ks,es) if k!=e]
from itertools import islice
for k,e in islice(pairs,0,50):
    print(k.encode('unicode_escape').decode(), '=>', e.encode('unicode_escape').decode())
