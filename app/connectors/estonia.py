"""Estonia RHR beta discovery connector.
The official register exposes public search and an Open Data section, but no stable REST API
was confirmed. This connector discovers public SPA assets/endpoints and reports diagnostics.
"""
from __future__ import annotations
import json,re,httpx
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean,date_any
BASE='https://riigihanked.riik.ee/'
UA={'User-Agent':'Mozilla/5.0 GOODRAM-Tender-Intelligence/1.4.1'}
CANDIDATES=['api','open-data','opendata','notices','procurements','search']

def _candidate_urls(html,base):
 s=BeautifulSoup(html,'html.parser');assets=[]
 for tag in s.select('script[src],link[href]'):
  u=urljoin(base,tag.get('src') or tag.get('href'))
  if urlparse(u).netloc=='riigihanked.riik.ee': assets.append(u)
 urls=set(re.findall(r'https?://[^\"\'<> ]+',html))
 for m in re.findall(r'[\"\']([^\"\']*(?:api|open-data|opendata|procurement|notice)[^\"\']*)[\"\']',html,re.I):
  if len(m)<400:urls.add(urljoin(base,m))
 return list(dict.fromkeys(assets)),list(urls)

def _records(data):
 if isinstance(data,list):return data
 if isinstance(data,dict):
  for k in ('items','content','results','data','procurements','notices'):
   if isinstance(data.get(k),list):return data[k]
 return []

def _pick(d,*names):
 for n in names:
  if isinstance(d,dict) and d.get(n) not in ('',None):return d[n]
 return ''

def parse_record(d,url=''):
 pid=str(_pick(d,'id','procurementId','referenceNumber','noticeId'))
 title=clean(str(_pick(d,'title','name','procurementName')));buyer=clean(str(_pick(d,'buyerName','contractingAuthority','buyer')))
 desc=clean(str(_pick(d,'description','shortDescription')));deadline=date_any(str(_pick(d,'deadline','submissionDeadline','tenderDeadline')));pub=date_any(str(_pick(d,'publicationDate','publishedAt','createdAt')))
 codes=re.findall(r'\b\d{8}\b',json.dumps(d,ensure_ascii=False));pid=pid or 'ee-'+str(abs(hash((title,buyer,url))))
 return Tender(pid,'estonia','EST',title,buyer,deadline=deadline,published=pub,url=url or BASE,description=desc,procurement_id=pid,cpv=list(dict.fromkeys(codes)))

async def fetch(countries,start,min_eur):
 stats={'homepage_status':0,'assets_checked':0,'candidate_endpoints':[],'json_endpoints':[],'records':0,'relevant':0};out=[]
 async with httpx.AsyncClient(timeout=35,follow_redirects=True,headers=UA) as c:
  r=await c.get(BASE);stats['homepage_status']=r.status_code;r.raise_for_status();assets,candidates=_candidate_urls(r.text,str(r.url))
  # Inspect a bounded number of public JS assets for API paths.
  for u in assets[:25]:
   try:
    a=await c.get(u);stats['assets_checked']+=1
    if a.status_code==200 and ('javascript' in (a.headers.get('content-type') or '') or u.endswith('.js')):
     _,found=_candidate_urls(a.text,u);candidates.extend(found)
   except Exception:pass
  candidates=list(dict.fromkeys(u for u in candidates if urlparse(u).netloc.endswith('riigihanked.riik.ee')))
  stats['candidate_endpoints']=candidates[:40]
  for u in candidates[:40]:
   try:
    q=await c.get(u)
    ct=(q.headers.get('content-type') or '').lower()
    if q.status_code==200 and ('json' in ct or q.text.lstrip().startswith(('{','['))):
     data=q.json();recs=_records(data);stats['json_endpoints'].append({'url':u,'records':len(recs)})
     for raw in recs[:500]:
      if not isinstance(raw,dict):continue
      t=parse_record(raw,u);stats['records']+=1
      if t.published and t.published<start:continue
      if not relevant('estonia',t.cpv,t.title+' '+t.description):continue
      stats['relevant']+=1;out.append(t)
   except Exception:pass
  if not stats['json_endpoints']:
   raise RuntimeError('Estonia RHR beta discovery found no public JSON feed. '+json.dumps(stats,ensure_ascii=False)[:1600])
 return out,stats
