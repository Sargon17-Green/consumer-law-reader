#!/usr/bin/env python3
"""Check stable requirement IDs, local references, publication proof and generated docs."""
from pathlib import Path
import hashlib,json,re,sys
from render_project_requirements import render
ROOT=Path(__file__).resolve().parents[1]
def validate(root=ROOT):
    required=['README.md','PRODUCT_REQUIREMENTS.md','ARCHITECTURE.md','IMPLEMENTATION_STATUS.md','BACKLOG.md','TESTING.md','RELEASE_PROCESS.md','RELEASE_HISTORY.md','KNOWN_ISSUES.md','DECISIONS.md','EXTERNAL_ACTIONS.md','PROJECT_HANDOFF.md']
    for name in required:
        if not (root/name).is_file() or (root/name).stat().st_size<200:raise ValueError('Missing project document: '+name)
    data=json.loads((root/'docs/requirements.json').read_text())
    if data['schema']!=1 or data['project']!='Sargon17-Green/consumer-law-reader':raise ValueError('Wrong project/catalog')
    allowed={'טרם התחיל','בפיתוח','מומש','אומת','פורסם','חסום','נדחה'}
    ids=set()
    for row in data['requirements']:
        ident=row['id']
        if not re.fullmatch(r'[A-Z][A-Z0-9]+-[0-9]{3}',ident) or ident in ids:raise ValueError('Invalid/duplicate ID: '+ident)
        ids.add(ident)
        if not row['acceptance'] or any(not isinstance(c,str) or len(c)<15 for c in row['acceptance']):raise ValueError('Missing measurable acceptance: '+ident)
        platforms=set(row['platforms'])
        if not platforms<= {'Android','iOS','Web'} or set(row['status'])!=platforms or set(row['published'])!=platforms:raise ValueError('Platform mismatch: '+ident)
        for path in row['implementation']+row['tests']:
            target=(root/path).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():raise ValueError('Broken implementation/test reference: '+ident+' '+path)
        for p,state in row['status'].items():
            if state not in allowed:raise ValueError('Unknown state: '+ident)
            if state in ('חסום','נדחה') and not row['dependencies']:raise ValueError('Undocumented dependency/defer: '+ident)
            published=row['published'][p]
            if (state=='פורסם') != bool(published):raise ValueError('Publication/state mismatch: '+ident+' '+p)
            if published:
                if not published.get('version') or not published.get('url','').startswith('https://') or not re.fullmatch('[0-9a-f]{40}',published.get('sourceCommit','')) or not published.get('evidence'):raise ValueError('Missing actual publication proof: '+ident)
                proof=published['evidence']
                if not proof.startswith('https://'):
                    checked=json.loads((root/proof).read_text())
                    if checked.get('passed') is not True or checked.get('sourceCommit')!=published['sourceCommit']:raise ValueError('Publication evidence does not pass or match source: '+ident)
        for evidence in row['evidence']:
            if not re.fullmatch('[0-9a-f]{40}',evidence['commit']) or not evidence['url'].startswith('https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/') or not isinstance(evidence['run'],int):raise ValueError('Invalid CI evidence: '+ident)
    if (root/'PRODUCT_REQUIREMENTS.md').read_text()!=render(data):raise ValueError('Requirements Markdown is stale; run render_project_requirements.py')
    for name in required:
        for href in re.findall(r'\]\(([^)]+)\)',(root/name).read_text()):
            if re.match(r'^[a-z]+:',href) or href.startswith('#'):continue
            target=(root/href.split('#')[0]).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():raise ValueError('Broken document link: '+name+' '+href)
    source=root/'original/Consumer_Protection_Law.html'
    if hashlib.sha256(source.read_bytes()).hexdigest()!='de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9':raise ValueError('Legal source changed')
    return {'schema':1,'documents':len(required),'requirements':len(ids),'result':'PASS','scope':'Catalog consistency, local references and exact source SHA; no CI or publication result is inferred from this validator'}
if __name__=='__main__':
    print(json.dumps(validate(),ensure_ascii=False))
