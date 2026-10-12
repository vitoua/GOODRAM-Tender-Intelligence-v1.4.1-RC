from datetime import datetime
from app.main import app
from app.filters import all_filters
from app.sources import NAMES, DESC
from app.connectors.latvia import parse_notice
from app.connectors.estonia import parse_record
required={'ted','prozorro','bzp','germany','ekap','nen','slovakia','cvpis','ekr','latvia','estonia'}
assert app.version=='1.4.1-rc'
assert required<=set(all_filters())
assert required<=set(NAMES)
for lang in ('pl','uk','en','es'):
 assert 'latvia' in DESC[lang] and 'estonia' in DESC[lang]
lv=parse_notice({'id':'LV-1','title':'SSD un serveru piegāde','buyerName':'Test buyer','publicationDate':'2026-10-01','submissionDeadline':'2026-12-01','cpv':['30233100']},'https://open.iub.gov.lv/data/notice/x.json')
assert lv.country=='LVA' and lv.procurement_id=='LV-1' and '30233100' in lv.cpv
ee=parse_record({'id':'EE-1','title':'SSD server','buyerName':'Buyer','deadline':'2026-12-01','cpv':'30233100'},'https://riigihanked.riik.ee/')
assert ee.country=='EST' and ee.procurement_id=='EE-1'
print('v1.4.1 RC tests ok')
