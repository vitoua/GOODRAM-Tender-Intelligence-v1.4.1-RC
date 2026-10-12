from datetime import datetime
import re,httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean,cpvs,date_any,soup_text,find_after
BASE='https://nen.nipez.cz'
async def fetch(countries,start,min_eur):
 out=[];stats={'pages':0,'list_links':0,'details_ok':0,'after_date':0,'active':0,'relevant':0};seen=set()
 async with httpx.AsyncClient(timeout=45,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4'}) as c:
  for page in range(1,11):
   url=BASE+'/verejne-zakazky'+('' if page==1 else f'/p:vz:page={page}');r=await c.get(url);r.raise_for_status();stats['pages']+=1;s,_=soup_text(r.text)
   links=[]
   for a in s.select('a[href*="/verejne-zakazky/detail-zakazky/"]'):
    href=a.get('href','');m=re.search(r'/detail-zakazky/([^?#]+)',href)
    if m and m.group(1) not in seen:seen.add(m.group(1));links.append((m.group(1),str(httpx.URL(BASE).join(href))))
   stats['list_links']+=len(links)
   if not links:break
   for nid,url in links:
    d=await c.get(url);d.raise_for_status();stats['details_ok']+=1;s,text=soup_text(d.text)
    title=find_after(text,'Název zadávacího postupu',['Zadavatel','Systémové číslo NEN']) or clean(s.title.get_text())
    buyer=find_after(text,'Zadavatel',['Systémové číslo NEN','Aktuální stav'])
    pub=date_any(find_after(text,'Datum uveřejnění ZP na profil',['Datum uveřejnění ZP na Věstník','Specifikace podání','Kontaktní osoba']))
    if pub and pub<start:continue
    stats['after_date']+=1;deadline=date_any(find_after(text,'Lhůta pro podání nabídek',['Kontaktní osoba','Předmět']))
    status=find_after(text,'Aktuální stav ZP',['Rozdělení na části','Evidenční číslo'])
    if not deadline or deadline<datetime.now() or any(x in status.lower() for x in ('zrušen','zadán','ukončen')):continue
    stats['active']+=1;codes=cpvs(text);desc=find_after(text,'Popis předmětu',['Kód z číselníku','Hlavní místo plnění'])
    if not relevant('nen',codes,title+' '+desc):continue
    stats['relevant']+=1;out.append(Tender(nid,'nen','CZE',title,buyer,deadline=deadline,published=pub,url=url,description=desc,procurement_id=nid,cpv=codes))
 return out,stats
