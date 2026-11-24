"""Reject accidentally tracked runtime data and common private credential formats."""
from pathlib import Path
import re,subprocess
root=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=root,text=True).splitlines()
errors=[]
for name in files:
    p=root/name
    if p.suffix in ['.sql','.pem','.key'] or p.name in ['wp-config.php','credentials.json','queue.json','editorial-config.json','daily-status.json','editorial-health.json','run-history.jsonl'] or name.startswith(('wp-content/uploads/','.local/','private/')):errors.append(name)
    if p.is_file() and p.suffix in ['.php','.py','.md','.yml','.js','.cjs','.txt']:
        text=p.read_text(errors='replace')
        if re.search(r'-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----',text):errors.append(name)
        if re.search(r'(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_]{24,}',text):errors.append(name)
if errors:raise SystemExit('Private runtime data detected: '+', '.join(sorted(set(errors))))
print('Public source boundaries checked:',len(files),'files')
