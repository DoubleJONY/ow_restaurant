import re,codecs,collections
pat=re.compile(r'Custom String\("(.*?)"\)')
ks=pat.findall(codecs.open('ko.txt','r','utf-8').read())
es=pat.findall(codecs.open('en.txt','r','utf-8').read())
m=collections.defaultdict(set)
for k,e in zip(ks,es):
    m[k].add(e)
amb={k:v for k,v in m.items() if len(v)>1}
print('ambiguous',len(amb))
for k,v in list(amb.items())[:10]:
    print(k.encode('unicode_escape').decode(), '->', [x.encode('unicode_escape').decode() for x in v])
