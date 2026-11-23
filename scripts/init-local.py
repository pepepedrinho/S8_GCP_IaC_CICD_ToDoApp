"""Create local secrets once; never display values or replace existing secrets."""
from pathlib import Path
import secrets
import json
root = Path(__file__).resolve().parents[1] / '.local' / 'secrets'
root.mkdir(parents=True, exist_ok=True)
root.chmod(0o700)
for name in ('mongo_root_password', 'mongo_app_password'):
    path = root / name
    if not path.exists():
        path.write_text(secrets.token_hex(24), encoding='utf-8')
        path.chmod(0o444)
uri = root / 'mongodb_uri'
if not uri.exists():
    password = (root / 'mongo_app_password').read_text().strip()
    uri.write_text(f'mongodb://todo:{password}@mongo:27017/todo-app?authSource=todo-app', encoding='utf-8')
    uri.chmod(0o444)
config = root / 'mongo_tools_config'
if not config.exists():
    config.write_text(json.dumps({'password': (root / 'mongo_root_password').read_text().strip()}), encoding='utf-8')
    config.chmod(0o444)
print('Local secrets ready; values omitted.')
