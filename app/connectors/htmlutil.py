import re
from datetime import datetime
from bs4 import BeautifulSoup

def clean(s): return ' '.join((s or '').replace('\xa0',' ').split())
def find_after(text,label,stops):
 p=text.lower().find(label.lower())
 if p<0:return ''
 s=text[p+len(label):]
 end=min([s.lower().find(x.lower()) for x in stops if s.lower().find(x.lower())>=0] or [len(s)])
 return clean(s[:end])
def cpvs(text): return list(dict.fromkeys(re.findall(r'\b\d{8}(?:-\d)?\b',text)))
def date_any(v):
 if not v:return None
 for f in ('%d.%m.%Y %H:%M','%d/%m/%Y %H:%M','%m/%d/%Y, %I:%M %p','%Y.%m.%d. %H:%M','%Y-%m-%dT%H:%M:%S','%Y-%m-%d'):
  try:return datetime.strptime(clean(v),f)
  except:pass
 m=re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})[^0-9]+(\d{1,2}):(\d{2})',v)
 if m:
  try:return datetime(int(m[3]),int(m[2]),int(m[1]),int(m[4]),int(m[5]))
  except:return None
 return None
def soup_text(html):return BeautifulSoup(html,'html.parser'),clean(BeautifulSoup(html,'html.parser').get_text(' ',strip=True))
