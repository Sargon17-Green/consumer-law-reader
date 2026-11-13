#!/usr/bin/env python3
"""Add the mobile reader to an existing Pages tree without changing other files."""
from pathlib import Path
import argparse,hashlib,json,shutil,os
MARKER='.consumer-law-reader-owner.json'
def manifest(root,exclude_reader=False):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts and
            (not exclude_reader or p.relative_to(root).parts[0]!='reader')}
def prepare(bundle,site,commit):
    bundle,site=Path(bundle),Path(site)
    if not (bundle/'index.html').is_file() or not site.is_dir():raise ValueError('Missing built reader or existing public site')
    before=manifest(site,True);target=site/'reader'
    if target.exists():
        marker=target/MARKER
        if not marker.is_file() or json.loads(marker.read_text()).get('owner')!='Sargon17-Green/consumer-law-reader':
            raise ValueError('Refusing to replace an unowned reader directory')
        shutil.rmtree(target)
    shutil.copytree(bundle,target)
    assets=manifest(bundle)
    (target/MARKER).write_text(json.dumps({'owner':'Sargon17-Green/consumer-law-reader','schema':1,'sourceCommit':commit,'assets':assets},indent=2))
    after=manifest(site,True)
    if before!=after:raise AssertionError('Existing public site changed outside /reader/')
    for name,digest in assets.items():
        if hashlib.sha256((target/name).read_bytes()).hexdigest()!=digest:raise AssertionError(name)
    return {'sourceCommit':commit,'existingFilesPreserved':len(before),'readerAssets':len(assets),'outsideReaderChanged':False}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',default='dist');parser.add_argument('--site',required=True);parser.add_argument('--commit',required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.bundle,args.site,args.commit)))
