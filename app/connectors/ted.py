from datetime import datetime
import httpx,re
from app.models import Tender
from app.filters import source_filter,relevant
from app.connectors.common import dt
URL='https://api.ted.europa.eu/v3/notices/search';FIELDS=['publication-number','notice-title','buyer-name','buyer-country','publication-date','deadline','description-proc','classification-cpv','total-value','total-value-cur']
def first(v):
 if isinstance(v,dict):return first(v.get('eng') or v.get('pol') or next(iter(v.values()),''))
 if isinstance(v,list):return first(v[0]) if v else ''
 return str(v or '')
async def fetch(countries,start,min_eur):
 raw={};stats={'queries':0,'unsupported_codes':0,'scanned':0,'relevant':0}
 async with httpx.AsyncClient(timeout=60) as c:
  for code in source_filter('ted')['codes']:
   p={'query':f'classification-cpv={code} AND publication-date>={start:%Y%m%d}','fields':FIELDS,'page':1,'limit':100,'scope':'ACTIVE','paginationMode':'PAGE_NUMBER','onlyLatestVersions':True};r=await c.post(URL,json=p);stats['queries']+=1
   if r.status_code==400 and ('not supported' in r.text or 'QUERY_UNSUPPORTED_FIELD_VALUE' in r.text):stats['unsupported_codes']+=1;continue
   r.raise_for_status()
   for x in r.json().get('notices',[]):raw[first(x.get('publication-number'))]=x
 out=[];stats['scanned']=len(raw)
 for n,x in raw.items():
  co=first(x.get('buyer-country'))[:3].upper();deadline=dt(first(x.get('deadline')));pub=dt(first(x.get('publication-date')));codes=[first(z) for z in x.get('classification-cpv',[])];title=first(x.get('notice-title'));desc=first(x.get('description-proc'))
  if co not in countries or not deadline or deadline<datetime.now() or not relevant('ted',codes,title+' '+desc):continue
  stats['relevant']+=1
  try:value=float(first(x.get('total-value')))
  except:value=None
  out.append(Tender(n,'ted',co,title,first(x.get('buyer-name')),value,first(x.get('total-value-cur')) or 'EUR',deadline,pub,f'https://ted.europa.eu/en/notice/-/detail/{n}',desc,n,codes,value if first(x.get('total-value-cur'))=='EUR' else None))
 return out,stats
