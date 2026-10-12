from app.main import app
from app.filters import all_filters
assert app.version=='1.3.0'
assert set(['ted','prozorro','bzp','germany','ekap'])<=set(all_filters())
paths={r.path for r in app.routes};assert {'/','/analytics','/cpv','/keywords','/sources','/status','/about','/refresh/start'}<=paths
print('full tests ok')
