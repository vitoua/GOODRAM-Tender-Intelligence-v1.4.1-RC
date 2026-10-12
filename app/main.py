from datetime import datetime,timedelta
from io import BytesIO
import asyncio,json,uuid
from pathlib import Path
from fastapi import FastAPI,Form,Request,HTTPException
from fastapi.responses import JSONResponse,RedirectResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.models import Tender
from app.store import store
from app.i18n import tr
from app.sources import COUNTRIES,NAMES,DESC
from app.filters import all_filters
from app.translate import ensure
app=FastAPI(version='1.4.1-rc');app.mount('/static',StaticFiles(directory='app/static'),name='static');tpl=Jinja2Templates(directory='app/templates');JOB={'running':False,'progress':0,'message':'','current_log':''};LOCK=asyncio.Lock()
def lang(r):return r.cookies.get('lang') or settings.app_language
def context(r,extra=None):return {'request':r,'lang':lang(r),'t':tr(lang(r)),'source_names':NAMES,'source_descriptions':DESC.get(lang(r),DESC['en']),**(extra or {})}
def default_date():return (datetime.now()-timedelta(days=30)).date().isoformat()
@app.get('/health')
def health():return {'status':'ok','version':'1.4.1-rc','tenders':len(store.data),'job':JOB}
@app.get('/lang/{code}')
def language(code,request:Request):
 r=RedirectResponse(request.headers.get('referer') or '/',303);r.set_cookie('lang',code if code in ('pl','uk','en','es') else 'pl');return r
@app.get('/')
async def home(request:Request,q:str='',country:str='',source:str=''):
 items=[x for x in store.data.values() if (not q or q.casefold() in (x.title+x.buyer+x.description).casefold()) and (not country or x.country==country) and (not source or x.source==source)];await ensure(items,lang(request));items.sort(key=lambda x:x.deadline or datetime.max);return tpl.TemplateResponse(request=request,name='index.html',context=context(request,{'rows':items,'countries':COUNTRIES,'default_date':default_date(),'runs':store.runs,'q':q,'country':country,'source':source,'last_update':store.last_update}))
async def execute(selected,sources,start,min_value):
 async with LOCK:
  JOB.update(running=True,progress=2,message='Starting');plan=[]
  if 'ted' in sources:plan.append(('ted',[x for x in selected if x not in ('UKR','TUR')]))
  if 'prozorro' in sources and 'UKR' in selected:plan.append(('prozorro',['UKR']))
  if 'bzp' in sources and 'POL' in selected:plan.append(('bzp',['POL']))
  if 'germany' in sources and 'DEU' in selected:plan.append(('germany',['DEU']))
  if 'ekap' in sources and 'TUR' in selected:plan.append(('turkey',['TUR']))
  if 'nen' in sources and 'CZE' in selected:plan.append(('nen',['CZE']))
  if 'slovakia' in sources and 'SVK' in selected:plan.append(('slovakia',['SVK']))
  if 'cvpis' in sources and 'LTU' in selected:plan.append(('cvpis',['LTU']))
  if 'ekr' in sources and 'HUN' in selected:plan.append(('ekr',['HUN']))
  if 'latvia' in sources and 'LVA' in selected:plan.append(('latvia',['LVA']))
  if 'estonia' in sources and 'EST' in selected:plan.append(('estonia',['EST']))
  results=[]
  for i,(module_name,scope) in enumerate(plan,1):
   shown='ekap' if module_name=='turkey' else module_name;JOB.update(progress=int((i-1)/max(1,len(plan))*90)+5,message='Loading '+shown.upper())
   try:m=__import__('app.connectors.'+module_name,fromlist=['fetch']);items,stats=await asyncio.wait_for(m.fetch(scope,start,min_value),210);results.append((shown,items,None,stats))
   except Exception as e:
    import traceback
    log=traceback.format_exc()[-2200:];JOB['current_log']=log;results.append((shown,[],RuntimeError(f'{type(e).__name__}: {e} | log: {log}'),{'log_excerpt':log}))
  store.replace(results);JOB.update(running=False,progress=100,message='Complete')
@app.post('/refresh/start')
async def start(countries:list[str]=Form(default=[]),sources:list[str]=Form(default=[]),min_value_eur:float=Form(0),published_from:str=Form('')):
 if JOB['running']:return JSONResponse({'message':'Refresh already running'},409)
 if not countries or not sources:return JSONResponse({'message':'Select country and source'},400)
 asyncio.create_task(execute(countries,sources,datetime.fromisoformat(published_from or default_date()),min_value_eur));return {'ok':True}
@app.get('/refresh/status')
def status():return JOB
@app.get('/tenders/{tid:path}')
async def detail(tid,request:Request,view:str='translated'):
 x=next((v for v in store.data.values() if v.procurement_id==tid),None)
 if not x:raise HTTPException(404)
 await ensure([x],lang(request));return tpl.TemplateResponse(request=request,name='detail.html',context=context(request,{'x':x,'view':view}))
@app.get('/analytics')
def analytics(request:Request):return tpl.TemplateResponse(request=request,name='analytics.html',context=context(request,{'count':len(store.data)}))
@app.get('/cpv')
def cpv(request:Request):return tpl.TemplateResponse(request=request,name='cpv.html',context=context(request,{'filters':all_filters()}))
@app.get('/keywords')
def keywords(request:Request):return tpl.TemplateResponse(request=request,name='keywords.html',context=context(request,{'filters':all_filters()}))
@app.get('/sources')
def sources(request:Request):return tpl.TemplateResponse(request=request,name='sources.html',context=context(request,{'runs':{x['source']:x for x in store.runs}}))
@app.get('/status')
def system_status(request:Request):return tpl.TemplateResponse(request=request,name='status.html',context=context(request,{'runs':{x['source']:x for x in store.runs}}))
@app.get('/about')
def about(request:Request):return tpl.TemplateResponse(request=request,name='about.html',context=context(request))
@app.get('/export.xlsx')
def export():
 from openpyxl import Workbook
 wb=Workbook();ws=wb.active;ws.append(['Source','Country','ID','Title','Buyer','Published','Deadline','Value','Currency','CPV','URL'])
 for x in store.data.values():ws.append([x.source,x.country,x.procurement_id,x.title,x.buyer,x.published,x.deadline,x.value,x.currency,', '.join(x.cpv),x.url])
 ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;out=BytesIO();wb.save(out);out.seek(0);return StreamingResponse(out,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="GOODRAM-Tender-Intelligence-v1.4.1-RC.xlsx"'})
