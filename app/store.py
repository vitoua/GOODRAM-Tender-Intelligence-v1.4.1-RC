from datetime import datetime
class Store:
 def __init__(self):self.data={};self.runs=[];self.last_update=None
 def replace(self,results):
  self.data={};self.runs=[]
  for source,items,error,stats in results:
   if error:self.runs.append({'source':source,'status':'error','count':0,'error':str(error)[:600],'stats':stats});continue
   for item in items:self.data[(item.source+':'+item.procurement_id)]=item
   self.runs.append({'source':source,'status':'ok','count':len(items),'error':'','stats':stats})
  self.last_update=datetime.now()
store=Store()
