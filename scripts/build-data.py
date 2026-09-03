import json, collections, os, gzip

USFM = ["GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA","1KI","2KI","1CH","2CH",
"EZR","NEH","EST","JOB","PSA","PRO","ECC","SNG","ISA","JER","LAM","EZK","DAN","HOS","JOL",
"AMO","OBA","JON","MIC","NAM","HAB","ZEP","HAG","ZEC","MAL","MAT","MRK","LUK","JHN","ACT",
"ROM","1CO","2CO","GAL","EPH","PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS",
"1PE","2PE","1JN","2JN","3JN","JUD","REV"]

# ---------- Scripture: Berean Standard Bible, public domain (CC0, 30 Apr 2023) ----------
src = json.load(open('bsb.json', encoding='utf-8-sig'))
TEXT, CH_COUNT = {}, {}
for i, book in enumerate(src['books']):
    code = USFM[i]
    CH_COUNT[code] = len(book['chapters'])
    for ch in book['chapters']:
        for v in ch['verses']:
            t = ' '.join(v['text'].split())
            if t:
                TEXT[(code, ch['chapter'], v['verse'])] = t
print(f"BSB verses: {len(TEXT)}")

# ---------- Cross references: OpenBible.info, CC BY 4.0 ----------
OSIS = {"Gen":"GEN","Exod":"EXO","Lev":"LEV","Num":"NUM","Deut":"DEU","Josh":"JOS","Judg":"JDG",
"Ruth":"RUT","1Sam":"1SA","2Sam":"2SA","1Kgs":"1KI","2Kgs":"2KI","1Chr":"1CH","2Chr":"2CH",
"Ezra":"EZR","Neh":"NEH","Esth":"EST","Job":"JOB","Ps":"PSA","Prov":"PRO","Eccl":"ECC",
"Song":"SNG","Isa":"ISA","Jer":"JER","Lam":"LAM","Ezek":"EZK","Dan":"DAN","Hos":"HOS",
"Joel":"JOL","Amos":"AMO","Obad":"OBA","Jonah":"JON","Mic":"MIC","Nah":"NAM","Hab":"HAB",
"Zeph":"ZEP","Hag":"HAG","Zech":"ZEC","Mal":"MAL","Matt":"MAT","Mark":"MRK","Luke":"LUK",
"John":"JHN","Acts":"ACT","Rom":"ROM","1Cor":"1CO","2Cor":"2CO","Gal":"GAL","Eph":"EPH",
"Phil":"PHP","Col":"COL","1Thess":"1TH","2Thess":"2TH","1Tim":"1TI","2Tim":"2TI","Titus":"TIT",
"Phlm":"PHM","Heb":"HEB","Jas":"JAS","1Pet":"1PE","2Pet":"2PE","1John":"1JN","2John":"2JN",
"3John":"3JN","Jude":"JUD","Rev":"REV"}

def parse(tok):
    tok = tok.split('-')[0]
    p = tok.split('.')
    if len(p) != 3: return None
    b = OSIS.get(p[0])
    if not b: return None
    try: return (b, int(p[1]), int(p[2]))
    except ValueError: return None

XR = collections.defaultdict(list)
kept = dropped = 0
with open('bible-crossrefs-dataset-main/data/00_raw/openbible/cross_references.txt') as f:
    next(f)
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 3: continue
        a, b = parse(parts[0]), parse(parts[1])
        if not a or not b or a not in TEXT or b not in TEXT:
            dropped += 1; continue
        try: votes = int(parts[2])
        except ValueError: dropped += 1; continue
        XR[a].append((b, votes)); kept += 1
for k in XR: XR[k].sort(key=lambda x: -x[1])
print(f"cross-references kept: {kept}  dropped (unresolvable): {dropped}")
print(f"verses with references: {len(XR)}")

# ---------- emit, sharded per book so a reader loads only what they open ----------
os.makedirs('data/verses', exist_ok=True)
os.makedirs('data/xrefs', exist_ok=True)
key = lambda t: f"{t[0]}.{t[1]}.{t[2]}"
TOP = 8   # app shows 5; extra headroom for filtering
total_v = total_x = 0

for code in USFM:
    V = {f"{c}.{v}": TEXT[(code, c, v)] for (bk, c, v) in TEXT if bk == code}
    X = {}
    for (bk, c, v), refs in XR.items():
        if bk != code: continue
        X[f"{c}.{v}"] = [[key(t), n] for t, n in refs[:TOP]]
    vj = json.dumps(V, separators=(',', ':'), ensure_ascii=False)
    xj = json.dumps(X, separators=(',', ':'), ensure_ascii=False)
    open(f'data/verses/{code}.json', 'w', encoding='utf-8').write(vj)
    open(f'data/xrefs/{code}.json', 'w', encoding='utf-8').write(xj)
    total_v += len(vj); total_x += len(xj)

index = {
    "translation": "BSB",
    "translationName": "Berean Standard Bible",
    "license": "Public domain (CC0), dedicated 30 April 2023",
    "xrefSource": "OpenBible.info cross-references, CC BY 4.0",
    "verses": len(TEXT),
    "links": kept,
    "topPerVerse": TOP,
    "books": [{"id": c, "chapters": CH_COUNT[c]} for c in USFM],
}
json.dump(index, open('data/index.json', 'w'), separators=(',', ':'))
print(f"verses {total_v/1024/1024:.1f} MB · xrefs {total_x/1024/1024:.1f} MB · total {(total_v+total_x)/1024/1024:.1f} MB")
