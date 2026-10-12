from datetime import datetime
def dt(v):
 if not v:return None
 for x in (str(v),str(v)[:19],str(v)[:10]):
  try:return datetime.fromisoformat(x.replace('Z','+00:00')).replace(tzinfo=None)
  except:pass
 return None
