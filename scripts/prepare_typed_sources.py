#!/usr/bin/env python3
"""Build the mobile source-first index from the existing canonical v1 contract.

Only code-free JSON snapshots are accepted. Source Python is never imported.
The original snapshots stay untouched; an empty directory produces an empty index.
"""
from pathlib import Path
import argparse,hashlib,json,re
from canonical_vendor.canonical_snapshot import load_snapshot,SOURCE_SCHEMA_SHA256,CanonicalSnapshotError
from canonical_vendor.canonical_search import build_search_index,INDEX_FORMAT,INDEX_VERSION

MAX_FILE=64*1024*1024
MAX_TOTAL=128*1024*1024

def prepare(input_dir:Path,output_dir:Path,evidence_dir:Path):
    input_dir,output_dir,evidence_dir=map(Path,(input_dir,output_dir,evidence_dir))
    output_dir.mkdir(parents=True,exist_ok=True);evidence_dir.mkdir(parents=True,exist_ok=True)
    paths=sorted(input_dir.glob('*.json')) if input_dir.exists() else []
    if sum(p.stat().st_size for p in paths)>MAX_TOTAL:raise ValueError('Typed-source inputs exceed 128 MiB')
    index={'format':INDEX_FORMAT,'format_version':INDEX_VERSION,'source_schema_sha256':SOURCE_SCHEMA_SHA256,
           'source_archive_sha256':None,'sources':[],'segments':[],'associations':[],'votes':[],'publication_authorized':False}
    seen_sources=set();seen_documents=set();files=[];diagnostics=[]
    for p in paths:
        if p.is_symlink() or not p.is_file() or p.stat().st_size>MAX_FILE:raise ValueError('Invalid or oversized input: '+p.name)
        raw=p.read_bytes();snapshot=load_snapshot(p)
        for entry in snapshot['entries']:
            sid,did=entry['source_id'],entry['document_id']
            if sid in seen_sources or did in seen_documents:raise ValueError('Duplicate source/document across snapshots: '+sid)
            seen_sources.add(sid);seen_documents.add(did)
            url=entry['document']['fields']['source_url']
            if re.search(r'[\x00-\x20\\]',url):raise ValueError('Control/space/backslash in source URL: '+sid)
        part=build_search_index(snapshot)
        offset=len(index['segments'])
        for segment in part['segments']:segment['order']+=offset
        for key in ['sources','segments','associations','votes']:index[key].extend(part[key])
        for source in part['sources']:
            diagnostics.append({'source_id':source['source_id'],'original_document_url':source['original_document_url'],
                'link_validation':source['link_validation'],'network_checked':False})
        files.append({'file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                      'source_archive_sha256':snapshot['source_archive_sha256'],'sources':len(snapshot['entries'])})
    hashes={f['source_archive_sha256'] for f in files}
    if len(hashes)==1:index['source_archive_sha256']=next(iter(hashes))
    # A lazy-loaded script also works under file://; only generated, escaped JSON
    # is written here. Canonical strings never enter innerHTML at runtime.
    encoded=json.dumps(index,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    encoded=encoded.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    payload=('window.LawTypedIndex='+encoded+';\n').encode('utf-8')
    (output_dir/'typed-index.js').write_bytes(payload)
    report={'contract':'canonical-legislative-sources v1 → legal-legislative-source-search-index v1',
            'source_schema_sha256':SOURCE_SCHEMA_SHA256,'input_files':files,'sources':len(index['sources']),
            'segments':len(index['segments']),'associations':len(index['associations']),'votes':len(index['votes']),
            'index_sha256':hashlib.sha256(payload).hexdigest(),'diagnostics':diagnostics,
            'source_code_execution':False,'source_text_fidelity':'NOT_ASSESSED','publication_authorized':False}
    (evidence_dir/'typed-source-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return index,report

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,default=root/'typed-sources')
    parser.add_argument('--output-dir',type=Path,default=root/'dist')
    parser.add_argument('--evidence-dir',type=Path,default=root/'evidence')
    args=parser.parse_args();_,report=prepare(args.input_dir,args.output_dir,args.evidence_dir)
    print(json.dumps({'sources':report['sources'],'segments':report['segments'],'index_sha256':report['index_sha256']}))
