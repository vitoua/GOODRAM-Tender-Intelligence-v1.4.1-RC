from datetime import datetime
import re,httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean,cpvs,date_any,soup_text,find_after
BASE='https://evo.isepvo.sk/evoportal/sk-sk/Public/OrderSearch'
async def fetch(countries,start,min_eur):
 out=[];stats={'list_status':0,'ids':0,'details_ok':0,'active':0,'relevant':0};seen=set()
 async with httpx.AsyncClient(timeout=45,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4'}) as c:
  r=await c.get(BASE+'/Index');stats['list_status']=r.status_code;r.raise_for_status();s,_=soup_text(r.text)
  for a in s.select('a[href*="OrderSearch/Detail"],a[href*="ordersearch/detail"]'):
   m=re.search(r'[?&]id=(\d+)',a.get('href',''),re.I)
   if m:seen.add(m.group(1))
  stats['ids']=len(seen)
  for oid in list(seen)[:300]:
   url=BASE+'/Detail?id='+oid;d=await c.get(url);d.raise_for_status();stats['details_ok']+=1;s,text=soup_text(d.text)
   title=find_after(text,'Názov zákazky',['Obstarávateľ','Upozornenie']) or clean(s.title.get_text());buyer=find_after(text,'Obstarávateľ',['Upozornenie','Detail zákazky']);status=find_after(text,'Stav zákazky',['Vstúpiť do zákazky','CPV zákazky'])
   pub=date_any(find_after(text,'Dátum zverejnenia',['Elektronická aukcia','Dokumenty zákazky']));deadline=date_any(find_after(text,'Lehota na predkladanie ponúk',['Predložiť ponuku','Dátum ostatné']))
   if pub and pub<start or not deadline or deadline<datetime.now() or 'aktívna' not in status.lower():continue
   stats['active']+=1;codes=cpvs(find_after(text,'CPV zákazky',['NUTS zákazky']));desc=title
   if not relevant('slovakia',codes,title):continue
   stats['relevant']+=1;out.append(Tender(oid,'slovakia','SVK',title,buyer,deadline=deadline,published=pub,url='https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek/detail/'+oid,description=desc,procurement_id=oid,cpv=codes))
 return out,stats
