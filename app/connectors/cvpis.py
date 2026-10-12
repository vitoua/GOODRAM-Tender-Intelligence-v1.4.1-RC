import re,httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.htmlutil import clean,cpvs,date_any,soup_text,find_after
BASE='https://viesiejipirkimai.lt'
CANDIDATES=['/epps/cft/listContractDocuments.do','/epps/cft/prepareViewCfTWS.do','/epps/cft/listContractNotice.do']
async def fetch(countries,start,min_eur):
 out=[];stats={'discovery_attempts':[],'resource_ids':0,'details_ok':0,'relevant':0};ids=set()
 async with httpx.AsyncClient(timeout=50,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 GOODRAM-Tender-Intelligence/1.4'}) as c:
  for path in CANDIDATES:
   try:
    r=await c.get(BASE+path);stats['discovery_attempts'].append({'path':path,'status':r.status_code,'bytes':len(r.content)});r.raise_for_status();ids.update(re.findall(r'resourceId=(\d+)',r.text))
   except Exception as e:stats['discovery_attempts'].append({'path':path,'error':str(e)[:160]})
  stats['resource_ids']=len(ids)
  if not ids:raise RuntimeError('CVP IS discovery returned 0 resourceId values; tested public list candidates: '+str(stats['discovery_attempts']))
  for rid in list(ids)[:300]:
   url=BASE+'/epps/cft/prepareViewCfTWS.do?resourceId='+rid;d=await c.get(url);d.raise_for_status();stats['details_ok']+=1;s,text=soup_text(d.text);title=find_after(text,'Pavadinimas:',['Pirkimo unikalus ID','PV Pirkimo unikalus ID']);buyer=find_after(text,'Pirkimo vykdytojo pavadinimas:',['Pavadinimas:']);desc=find_after(text,'Aprašymas:',['Pirkimo objekto tipas:']);codes=cpvs(find_after(text,'BVPŽ kodai:',['Laimėtojo nustatymas','NUTS kodai']));deadline=date_any(find_after(text,'Pasiūlymų arba paraiškų dalyvauti pirkime pateikimo terminas :',['Kvietimų išsiuntimo terminas','Prašymų pateikti']))
   if not relevant('cvpis',codes,title+' '+desc):continue
   stats['relevant']+=1;out.append(Tender(rid,'cvpis','LTU',title,buyer,deadline=deadline,url=url,description=desc,procurement_id=rid,cpv=codes))
 return out,stats
