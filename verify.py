from pathlib import Path
import json,csv,sqlite3,sys
ROOT=Path(__file__).resolve().parent
A=ROOT/'analysis'
def rows(n):
 r=list(csv.DictReader((A/n).open()))
 for x in r:
  for k,v in x.items():
   try:x[k]=float(v) if '.' in v else int(v)
   except(ValueError,TypeError):pass
 return r
sys.path.insert(0,str(A))
from controls import review_batch,regressions,review_posting
p=json.loads((A/'postings.json').read_text()); expected=json.loads((A/'findings.json').read_text())
actual=review_batch(p)
assert actual==expected
assert len(actual)==9
assert sum(any(f['status']=='flag' for f in x['findings']) for x in actual)==3
assert sum(any(f['status']=='review_required' for f in x['findings']) for x in actual)==2
assert {x['rule'] for x in regressions(p[0],p[1])}=={'AI','ARCHIVE_POSTING'}
bad=dict(p[0]);bad['posted_on']='bad-date'
assert any(x['status']=='review_required' for x in review_posting(bad))
print('PASS: all 9 version findings reproduced exactly; 3 flagged / 2 review required; two expected v1-to-v2 regressions; malformed date routes to review.')
