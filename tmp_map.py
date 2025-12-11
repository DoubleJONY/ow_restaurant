import re, codecs
ko = codecs.open('ko.txt','r','utf-8').read().splitlines()
en = codecs.open('en.txt','r','utf-8').read().splitlines()
pat = re.compile(r'Custom String\("(.*?)"\)')
pairs = []
for kl, el in zip(ko, en):
    ks = pat.findall(kl)
    es = pat.findall(el)
    pairs.extend(zip(ks, es))
pairs = [(k, e) for k, e in pairs if k != e]
mapping = {}
for k, e in pairs:
    mapping.setdefault(k, set()).add(e)
print('pairs', len(pairs))
print('unique', len(mapping))
for k in list(mapping)[:20]:
    print(k.encode('unicode_escape').decode(), '->', [v.encode('unicode_escape').decode() for v in mapping[k]])
