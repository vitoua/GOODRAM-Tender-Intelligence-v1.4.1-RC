import io,json,zipfile,httpx
from datetime import date,datetime,timedelta
from app.models import Tender
from app.filters import relevant
from app.connectors.common import dt
async def fetch(countries,start,min_eur):
 out=[];stats={'days':0,'files':0,'relevant':0}
 async with httpx.AsyncClient(timeout=65) as c:
  for i in range(1,min(31,(date.today()-start.date()).days+2)):
   day=date.today()-timedelta(days=i);r=await c.get('https://oeffentlichevergabe.de/api/notice-exports',params={'pubDay':day.isoformat(),'format':'ocds.zip'});stats['days']+=1
   if r.status_code in (400,404):continue
   r.raise_for_status()
   with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    for fn in z.namelist():
     stats['files']+=1;rel=(json.loads(z.read(fn)).get('releases') or [{}])[0];t=rel.get('tender') or {};items=t.get('items') or [];codes=[i.get('classification',{}).get('id','') for i in items];title=t.get('title','');desc=t.get('description','');deadline=dt((t.get('tenderPeriod') or {}).get('endDate'))
     if not deadline or deadline<datetime.now() or not relevant('germany',codes,title+' '+desc):continue
     stats['relevant']+=1;n=rel.get('ocid') or rel.get('id') or fn;buyer=next((p.get('name','') for p in rel.get('parties',[]) if 'buyer' in p.get('roles',[])),'');v=t.get('value') or {};out.append(Tender(n,'germany','DEU',title,buyer,v.get('amount'),v.get('currency','EUR'),deadline,dt(rel.get('date')),f'https://oeffentlichevergabe.de/ui/de/notices/{n}',desc,n,codes))
 return out,stats
