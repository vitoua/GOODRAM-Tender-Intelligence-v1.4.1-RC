from datetime import datetime
import re,httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean,cpvs,date_any,soup_text,find_after
BASE='https://ekr.gov.hu'
async def fetch(countries,start,min_eur):
 out=[];stats={'list_status':0,'ids':0,'details_ok':0,'active':0,'relevant':0};seen=set()
 async with httpx.AsyncClient(timeout=50,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 GOODRAM-Tender-Intelligence/1.4'}) as c:
  r=await c.get(BASE+'/eljarastar/',params={'aktualis':'true','order':'MEGINDITAS_DATUMA_DESC'});stats['list_status']=r.status_code;r.raise_for_status();s,text=soup_text(r.text)
  for a in s.select('a[href*="/eljarastar/eljaras/"]'):
   m=re.search(r'/eljarastar/eljaras/(EKR\d+)',a.get('href',''))
   if m:seen.add(m.group(1))
  if not seen:seen.update(re.findall(r'\bEKR\d{8,}\b',text))
  stats['ids']=len(seen)
  for eid in list(seen)[:300]:
   url=BASE+'/eljarastar/eljaras/'+eid;d=await c.get(url);d.raise_for_status();stats['details_ok']+=1;s,text=soup_text(d.text)
   title=clean((s.select_one('h1') or s.title).get_text(' ',strip=True));buyer=find_after(text,'Ajánlatkérő',['Részek','Stratégiai közbeszerzés']);deadline=date_any(find_after(text,'Ajánlattételi határidő',['Szerződések','Ajánlatkérő'])) or date_any(find_after(text,'Benyújtási határidő',['Szerződések','Ajánlatkérő']));pub=date_any(find_after(text,'Eljárás megindításának dátuma',['Nyelvek','Határidő']));codes=cpvs(find_after(text,'Eljárás szintű CPV-kód',['Szerződés típusa']))
   if pub and pub<start or not deadline or deadline<datetime.now():continue
   stats['active']+=1
   if not relevant('ekr',codes,title):continue
   stats['relevant']+=1;out.append(Tender(eid,'ekr','HUN',title,buyer,deadline=deadline,published=pub,url=url,description=title,procurement_id=eid,cpv=codes))
 return out,stats
