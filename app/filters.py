import json,re
from pathlib import Path
CONFIG=Path('data/filters.json')
def all_filters():return json.loads(CONFIG.read_text())
def source_filter(source):return all_filters().get(source,{'codes':[],'keywords':[]})
def relevant(source,codes,text):
 f=source_filter(source);norm=[re.sub(r'\D','',str(x))[:8] for x in codes];code_ok=any(c==a or (a.endswith('0000') and c.startswith(a.rstrip('0'))) for c in norm for a in f['codes']);t=(text or '').casefold();kw_ok=any(k.casefold() in t for k in f['keywords']);return code_ok or kw_ok
