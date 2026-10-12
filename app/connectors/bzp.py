from datetime import datetime
import httpx
from app.models import Tender
from app.filters import relevant
from app.connectors.common import dt
URL='https://ezamowienia.gov.pl/mo-board/api/v1/notice'
async def fetch(countries,start,min_eur):
 out=[];stats={'status':0,'scanned':0,'relevant':0};params={'PublicationDateFrom':start.date().isoformat(),'PageSize':100}
 async with httpx.AsyncClient(timeout=45,follow_redirects=True) as c:r=await c.get(URL,params=params);stats['status']=r.status_code;r.raise_for_status();body=r.json()
 rows=body if isinstance(body,list) else body.get('content') or body.get('items') or body.get('data') or [];stats['scanned']=len(rows)
 for x in rows:
  title=x.get('noticeTitle') or x.get('orderObject') or x.get('title') or '';desc=x.get('description') or '';codes=x.get('cpvCodes') or x.get('cpv') or []
  if isinstance(codes,str):codes=[codes]
  if not relevant('bzp',codes,title+' '+desc):continue
  stats['relevant']+=1;n=str(x.get('noticeNumber') or x.get('id'));out.append(Tender(n,'bzp','POL',title,x.get('contractingAuthorityName') or x.get('organizationName',''),deadline=dt(x.get('tenderDeadline') or x.get('submissionDeadline')),published=dt(x.get('publicationDate')),url=x.get('url') or 'https://ezamowienia.gov.pl/',description=desc,procurement_id=n,cpv=codes))
 return out,stats
