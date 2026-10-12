from datetime import datetime
import httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.common import dt
URL='https://public-api.prozorro.gov.ua/api/2.5/tenders'
async def fetch(countries,start,min_eur):
 out=[];offset=None;stats={'pages':0,'scanned':0,'details_ok':0,'after_date':0,'active':0,'relevant':0}
 async with httpx.AsyncClient(timeout=45,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.3'}) as c:
  while stats['pages']<20:
   params={'limit':100,'descending':1};
   if offset:params['offset']=offset
   r=await c.get(URL,params=params);r.raise_for_status();body=r.json();page=body.get('data',[]);stats['pages']+=1
   if not page:break
   for row in page:
    stats['scanned']+=1
    try:d=await c.get(f"{URL}/{row['id']}");d.raise_for_status();x=d.json().get('data',{});stats['details_ok']+=1
    except:continue
    pub=dt(x.get('dateCreated') or x.get('dateModified'))
    if pub and pub<start:continue
    stats['after_date']+=1;deadline=dt((x.get('tenderPeriod') or {}).get('endDate'))
    if not deadline or deadline<datetime.now():continue
    stats['active']+=1;items=x.get('items') or [];codes=[i.get('classification',{}).get('id','') for i in items];text=' '.join([x.get('title',''),x.get('description','')]+[i.get('description','') for i in items])
    if not relevant('prozorro',codes,text):continue
    stats['relevant']+=1;n=x.get('tenderID') or row['id'];value=(x.get('value') or {}).get('amount');currency=(x.get('value') or {}).get('currency','UAH');out.append(Tender(n,'prozorro','UKR',x.get('title') or n,(x.get('procuringEntity') or {}).get('name',''),value,currency,deadline,pub,f'https://prozorro.gov.ua/tender/{n}',x.get('description',''),n,codes))
   offset=(body.get('next_page') or {}).get('offset')
   if not offset:break
 return out,stats
