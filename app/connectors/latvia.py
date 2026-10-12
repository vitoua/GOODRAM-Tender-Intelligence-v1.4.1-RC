"""Latvia IUB Open Data connector.
Official public entry point: https://open.iub.gov.lv/data/notice
The service exposes daily JSON files in year/month/day directories.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import json, re, httpx
from bs4 import BeautifulSoup
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean, date_any
BASE = 'https://open.iub.gov.lv/data/notice'
UA = {'User-Agent':'GOODRAM-Tender-Intelligence/1.4.1 (+public-open-data-client)'}

def _walk(obj):
 if isinstance(obj,dict):
  yield obj
  for v in obj.values(): yield from _walk(v)
 elif isinstance(obj,list):
  for v in obj: yield from _walk(v)

def _first(obj, names, default=''):
 wanted={x.casefold() for x in names}
 for d in _walk(obj):
  for k,v in d.items():
   if str(k).casefold() in wanted and isinstance(v,(str,int,float)) and str(v).strip(): return v
 return default

def _cpvs(obj):
 vals=[]
 for d in _walk(obj):
  for k,v in d.items():
   if 'cpv' in str(k).casefold() or 'classification' in str(k).casefold():
    vals += re.findall(r'\b\d{8}\b',json.dumps(v,ensure_ascii=False))
 return list(dict.fromkeys(vals))

def parse_notice(obj, source_url=''):
 pid=str(_first(obj,['noticeId','notice-id','noticeIdentifier','id','BT-701-notice']) or '')
 title=clean(str(_first(obj,['title','noticeTitle','procurementTitle','name','BT-21-Procedure']) or ''))
 buyer=clean(str(_first(obj,['buyerName','organisationName','organizationName','contractingAuthorityName']) or ''))
 desc=clean(str(_first(obj,['description','shortDescription','procurementDescription','BT-24-Procedure']) or ''))
 pub=date_any(str(_first(obj,['publicationDate','published','datePublished','BT-05(a)-notice']) or ''))
 deadline=date_any(str(_first(obj,['deadline','submissionDeadline','tenderDeadline','BT-131(d)-Lot']) or ''))
 value=_first(obj,['estimatedValue','totalValue','valueAmount','BT-27-Procedure'])
 try:value=float(str(value).replace(',','.')) if value not in ('',None) else None
 except:value=None
 currency=str(_first(obj,['currency','valueCurrency','BT-27-Procedure-Currency']) or 'EUR')
 codes=_cpvs(obj)
 if not pid: pid='lv-'+str(abs(hash((title,buyer,str(pub),source_url))))
 return Tender(pid,'latvia','LVA',title,buyer,value,currency,deadline,pub,source_url,desc,pid,codes,value if currency=='EUR' else None)

def _links(html, base):
 s=BeautifulSoup(html,'html.parser');out=[]
 for a in s.select('a[href]'):
  u=urljoin(base,a.get('href'))
  if urlparse(u).netloc=='open.iub.gov.lv' and '/data/notice' in u:out.append(u)
 return list(dict.fromkeys(out))

async def fetch(countries,start,min_eur):
 stats={'index_requests':0,'json_files':0,'json_records':0,'parsed':0,'relevant':0,'skipped_old':0,'skipped_value':0,'last_url':''}
 notices=[];visited=set();queue=[BASE]
 async with httpx.AsyncClient(timeout=50,follow_redirects=True,headers=UA) as c:
  # Crawl only public index pages and filenames that can belong to the selected date range.
  while queue and stats['index_requests']<80 and stats['json_files']<45:
   url=queue.pop(0)
   if url in visited:continue
   visited.add(url);stats['last_url']=url
   r=await c.get(url)
   if r.status_code>=400: raise RuntimeError(f'Latvia IUB HTTP {r.status_code} at {url}; response={r.text[:500]}')
   ct=(r.headers.get('content-type') or '').lower()
   if 'json' in ct or url.lower().endswith('.json'):
    stats['json_files']+=1
    try:data=r.json()
    except Exception as e:raise RuntimeError(f'Latvia IUB JSON decode failed at {url}: {e}; response={r.text[:500]}')
    records=data if isinstance(data,list) else data.get('notices') or data.get('data') or data.get('items') or [data]
    if not isinstance(records,list):records=[records]
    stats['json_records']+=len(records)
    for raw in records:
     if not isinstance(raw,dict):continue
     t=parse_notice(raw,url);stats['parsed']+=1
     if t.published and t.published<start:stats['skipped_old']+=1;continue
     if t.deadline and t.deadline<datetime.now():continue
     if min_eur>0 and (t.value_eur is None or t.value_eur<min_eur):stats['skipped_value']+=1;continue
     if not relevant('latvia',t.cpv,t.title+' '+t.description):continue
     stats['relevant']+=1;notices.append(t)
   else:
    stats['index_requests']+=1
    for link in _links(r.text,str(r.url)):
     # Avoid crawling historical trees unrelated to the selected year.
     years=re.findall(r'/((?:20)\d{2})(?:/|$)',link)
     if years and int(years[-1])<start.year:continue
     if link not in visited:queue.append(link)
 if stats['json_files']==0:
  raise RuntimeError(f"Latvia IUB discovery found no JSON files; index_requests={stats['index_requests']}, last_url={stats['last_url']}")
 return notices,stats
