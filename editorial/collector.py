"""Produce a private editorial evidence bundle, excluding tool payloads and reasoning."""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys

def clean(text):
    text = re.sub(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)', '[credencial omitida]', text, flags=re.S)
    text = re.sub(r'(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+', '[credencial omitida]', text)
    text = re.sub(r'https?://\S+', '[URL privada]', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[correo]', text)
    text = re.sub(r'(?i)(?:/Users/|/home/|/var/|/Volumes/)[^\s"\x27]+', '[ruta privada]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', text)
    text = re.sub(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b', '[ID]', text)
    text = re.sub(r'(?i)\b(?:password|passwd|api[_-]?key|secret|token|authorization)\s*[:=]\s*[^\s,;]+', '[credencial omitida]', text)
    text = re.sub(r'\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]+', '[credencial omitida]', text)
    text = re.sub(r'\+\d[\d ()-]{7,}\d', '[teléfono]', text)
    # Quoted JSON/shell credentials also occur in prose; keep them out of evidence.
    text = re.sub(r'''(?ix)(["']?\b(?:password|passwd|api[_-]?key|secret|token|authorization)\b["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;}]+)''', '[credencial omitida]', text)
    text = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[credencial omitida]', text)
    return text[:1800]

def collect(home=None):
    home=Path(home) if home else Path.home()
    items = []
    for path in (home/'.claude/projects').glob('*/*.jsonl'):
        human, assistant = [], []
        tools = collections.Counter()
        models = {}
        identifiers, fingerprints, timestamps = set(), set(), []
        errors = 0
        with path.open(errors='replace') as stream:
            for line in stream:
                try: row = json.loads(line)
                except ValueError: continue
                if not isinstance(row, dict): continue
                if row.get('isSidechain'): continue
                if row.get('timestamp'): timestamps.append(row['timestamp'])
                if row.get('sessionId'): identifiers.add(row['sessionId'])
                message = row.get('message') or {}
                if not isinstance(message, dict): continue
                content = message.get('content', [])
                if isinstance(content,str): content=[{'type':'text','text':content}]
                if not isinstance(content,list): continue
                blocks=[b for b in content if isinstance(b,dict)]
                kind=row.get('type')
                fingerprint=row.get('uuid')
                if fingerprint and fingerprint in fingerprints: continue
                if fingerprint: fingerprints.add(fingerprint)
                if kind=='user' and not row.get('isMeta') and not row.get('isCompactSummary') and not any(b.get('type')=='tool_result' for b in blocks):
                    for b in blocks:
                        if b.get('type')=='text' and b.get('text'): human.append(clean(b['text']))
                if kind=='assistant':
                    model=message.get('model')
                    if isinstance(model,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,150}',model) and model not in ['<synthetic>','synthetic','unknown']:
                        evidence=models.setdefault(model,{'model_id':model,'source_field':'message.model','first_event':None,'last_event':None,'record_count':0})
                        evidence['record_count']+=1
                        timestamp=row.get('timestamp')
                        if isinstance(timestamp,str):
                            evidence['first_event']=min(evidence['first_event'],timestamp) if evidence['first_event'] else timestamp
                            evidence['last_event']=max(evidence['last_event'],timestamp) if evidence['last_event'] else timestamp
                    for b in blocks:
                        if b.get('type')=='text' and b.get('text'): assistant.append(clean(b['text']))
                        if b.get('type')=='tool_use': tools[b.get('name','unknown')]+=1
                errors+=sum(bool(b.get('is_error')) for b in blocks if b.get('type')=='tool_result')
        if not human or not timestamps: continue
        # A bounded sample is evidence, not a full task history or a claim of success.
        sample=lambda seq: seq if len(seq)<=20 else seq[:6]+seq[-14:]
        identity=sorted(identifiers) or [path.stem]
        items.append({'key':hashlib.sha256('|'.join(identity).encode()).hexdigest()[:24],
            'first_event':min(timestamps), 'last_event':max(timestamps),
            'project_key':hashlib.sha256(path.parent.name.encode()).hexdigest()[:16],
            'source_digest':hashlib.sha256(json.dumps([human,assistant,dict(tools)],sort_keys=True).encode()).hexdigest(),
            'user_text_candidates':sample(human), 'assistant_text':sample(assistant),
            'ai_system':'Claude', 'client_context':'Claude local session records',
            'model_evidence':list(models.values()),
            'model_attribution_limit':'Modelos registrados a nivel de sesión. Una historia puede abarcar varios; no asignar un modelo a una decisión sin evidencia específica. Otros agentes citados en el texto son participación reportada, no verificada en sus propios registros.',
            'tool_counts':dict(tools),'tool_error_records':errors,
            'limits':'Muestra acotada; user puede contener texto automático. Sin resultados de pruebas: no inferir éxito. Sin razonamiento interno ni inputs de herramientas.'})
    return {'sessions':sorted(items,key=lambda x:x['last_event'],reverse=True)}

if __name__=='__main__':
    print(json.dumps(collect(),ensure_ascii=False))
