from app.main import app
from app.filters import all_filters
from app.sources import NAMES
required={'ted','prozorro','bzp','germany','ekap','nen','slovakia','cvpis','ekr'}
assert app.version=='1.4.0'
assert required<=set(all_filters())
assert required<=set(NAMES)
for name in ('nen','slovakia','cvpis','ekr'):
 __import__('app.connectors.'+name)
print('v1.4 tests ok')
