import httpx
from app.config import settings
from app.models import Tender
from app.filters import source_filter
async def fetch(countries,start,min_eur):
 if not settings.apify_api_token:raise RuntimeError('APIFY_API_TOKEN is not configured')
 payload={'query':' OR '.join(source_filter('ekap')['keywords']),'advert_date_from':start.date().isoformat(),'tender_type':'goods','page_size':100};url='https://api.apify.com/v2/acts/afkdigital~turkey-public-tender-tracker/run-sync-get-dataset-items'
 async with httpx.AsyncClient(timeout=180) as c:r=await c.post(url,params={'token':settings.apify_api_token},json=payload);r.raise_for_status();rows=r.json()
 out=[]
 for x in rows:
  n=str(x.get('ikn') or x.get('id'));out.append(Tender(n,'ekap','TUR',x.get('title') or x.get('tenderTitle') or n,x.get('authority',''),url=x.get('url','https://ekap.kik.gov.tr/'),description=x.get('description',''),procurement_id=n,cpv=x.get('cpvCodes') or []))
 return out,{'scanned':len(rows),'relevant':len(out)}
