from pathlib import Path
import hashlib,json,stat
c=Path(__file__).resolve().parent
r=c/'repo'
assert (r/'GUIDE.md').read_bytes()==b'Settings live at config/settings.toml.\n'
assert (r/'config/settings.toml').is_file()
assert not (r/'config/old-settings.toml').exists()
a=json.loads((c/'initial-manifest.json').read_bytes())
b=json.loads((c/'snapshot-manifest.json').read_bytes())
for name,entry in b.items():
 p=r/name
 actual={'deleted':False,'mode':format(stat.S_IMODE(p.stat().st_mode),'04o'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 assert actual==entry,name
 if name!='GUIDE.md': assert actual==a[name],name
print('PASS: guide names existing config/settings.toml; old path absent; candidate manifest matches; settings, wrapper, and initial dirty notes retain bytes and modes.')
