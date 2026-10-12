import hashlib,json,sqlite3,httpx
from app.config import settings
DB='translation_cache.sqlite3'
def setup():
 with sqlite3.connect(DB) as c:c.execute('create table if not exists translations(k text primary key,v text not null)')
def get(k):
 with sqlite3.connect(DB) as c:
  row=c.execute('select v from translations where k=?',(k,)).fetchone();return row[0] if row else None
def put(k,v):
 with sqlite3.connect(DB) as c:c.execute('insert or replace into translations values(?,?)',(k,v))
async def translate(text,target):
 if not text:return text
 setup();k=hashlib.sha256((target+'|'+text).encode()).hexdigest();cached=get(k)
 if cached:return cached
 try:
  if settings.azure_translator_key:
   h={'Ocp-Apim-Subscription-Key':settings.azure_translator_key,'Content-Type':'application/json'}
   if settings.azure_translator_region:h['Ocp-Apim-Subscription-Region']=settings.azure_translator_region
   async with httpx.AsyncClient(timeout=25) as c:r=await c.post(settings.azure_translator_endpoint.rstrip('/')+'/translate',params={'api-version':'3.0','to':target},headers=h,json=[{'text':text}]);r.raise_for_status();out=r.json()[0]['translations'][0]['text']
  else:
   async with httpx.AsyncClient(timeout=25) as c:r=await c.get('https://api.mymemory.translated.net/get',params={'q':text[:4500],'langpair':'auto|'+target});r.raise_for_status();out=r.json()['responseData']['translatedText']
  put(k,out);return out
 except:return text
async def ensure(items,lang):
 target={'uk':'uk','pl':'pl','en':'en','es':'es'}.get(lang,'pl')
 for x in items:
  if target not in x.translations:x.translations[target]={'title':await translate(x.title,target),'description':await translate(x.description,target)}
