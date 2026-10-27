"""Synthetic engineering checks; fixture text is never shipped as legal content."""
from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical_vendor.canonical_snapshot import SCHEMA,SOURCE_SCHEMA_SHA256,validate_snapshot,CanonicalSnapshotError,load_snapshot
from canonical_vendor.canonical_search import build_search_index
from prepare_typed_sources import prepare

def node(typ,**fields):return {'$type':typ,'fields':fields}
def snapshot(entries):return {'format':'canonical-legislative-sources','format_version':1,'source_schema_sha256':SOURCE_SCHEMA_SHA256,'source_archive_sha256':None,'entries':entries}
def entry(kind='bill',sid='TEST_BILL'):
    metadata_type={'bill':'BillMetadata','committee_protocol':'CommitteeProtocolMetadata','plenary_protocol':'PlenaryProtocolMetadata'}[kind]
    meta=node(metadata_type,**{k:[] if v.startswith('[') else None for k,v in SCHEMA[metadata_type].items()})
    content=[node('PageMarker',id='page',source_page=2,printed_page='א'),node('Paragraph',id='p',text='דוגמה סינתטית: ביטול עסקה <script>alert(1)</script>')]
    url='https://fs.knesset.gov.il/20/Committees/20_ptv_315530.doc'
    fields={'source_url':url,'source_filename':'fixture.doc','metadata':meta}
    if kind=='bill':fields.update(title='הצעת בדיקה סינתטית',content=content);root='BillDocument'
    elif kind=='committee_protocol':fields.update(participants=[],agenda=[node('AgendaItem',id='agenda',title='נושא בדיקה',content=[node('SpeakerTurn',id='speaker',speaker='דובר בדיקה',role=None,content=content)])],closing=[]);root='CommitteeProtocol'
    else:fields.update(table_of_contents=[],agenda=[node('PlenaryAgendaItem',id='agenda',title='נושא בדיקה',content=content)],closing=[]);root='PlenaryProtocol'
    return {'source_id':sid,'document_id':'doc_'+sid,'kind':kind,'document':node(root,**fields),'associations':[{'document_id':'doc_'+sid,'phase':None,'date':None,'location':None,'law_name':'חוק בדיקה בלבד','relevant_parts':['p']}],'provenance':{'synthetic':True},'verification':None}

class TypedSourceTests(unittest.TestCase):
    def test_three_document_kinds_and_exact_urls(self):
        data=snapshot([entry('bill','TEST_B'),entry('committee_protocol','TEST_C'),entry('plenary_protocol','TEST_P')]);before=copy.deepcopy(data)
        idx=build_search_index(data);self.assertEqual(data,before);self.assertEqual(len(idx['sources']),3)
        for src,e in zip(idx['sources'],data['entries']):
            self.assertEqual(src['original_document_url'],e['document']['fields']['source_url']);self.assertIsNone(src['official_page_url'])
        segment=next(s for s in idx['segments'] if s['source_id']=='TEST_C' and s['node_id']=='p')
        self.assertEqual(segment['speaker'],'דובר בדיקה');self.assertEqual(segment['source_page'],2);self.assertEqual(segment['printed_page'],'א')
    def test_vote_event_preserves_zero_and_null_without_duplicate_text(self):
        e=entry();e['document']['fields']['content']=[node('Paragraph',id='p',text='טקסט ההצבעה'),node('Vote',id='v',subject=None,vote_number=None,for_count=0,against_count=None,abstain_count=None,result='לא נמסר',raw_text='טקסט ההצבעה')]
        idx=build_search_index(snapshot([e]));self.assertEqual(sum(s['text']=='טקסט ההצבעה' for s in idx['segments']),1)
        self.assertEqual(idx['votes'][0]['for_count'],0);self.assertIsNone(idx['votes'][0]['against_count']);self.assertFalse(idx['votes'][0]['raw_text_indexed'])
    def test_multiple_associations_do_not_duplicate_document(self):
        e=entry();a=copy.deepcopy(e['associations'][0]);a['phase']='שלב אחר';e['associations'].append(a)
        idx=build_search_index(snapshot([e]));self.assertEqual(len(idx['sources']),1);self.assertEqual(len(idx['associations']),2)
    def test_rejects_unknown_type_field_and_broken_references(self):
        for mutation in ['type','extra','ref','schema','duplicate','unsafe_url']:
            with self.subTest(mutation=mutation):
                d=snapshot([entry()]);e=d['entries'][0]
                if mutation=='type':e['document']['fields']['content'][1]['$type']='Executable'
                elif mutation=='extra':e['document']['fields']['content'][1]['fields']['extra']='x'
                elif mutation=='ref':e['associations'][0]['relevant_parts']=['missing']
                elif mutation=='schema':d['source_schema_sha256']='0'*64
                elif mutation=='duplicate':e['document']['fields']['content'].append(copy.deepcopy(e['document']['fields']['content'][1]))
                else:e['document']['fields']['source_url']='javascript:alert(1)'
                with self.assertRaises(CanonicalSnapshotError):validate_snapshot(d)
    def test_json_duplicate_properties_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json';p.write_text('{"format":1,"format":2}')
            with self.assertRaises(CanonicalSnapshotError):load_snapshot(p)
    def test_empty_index_and_deterministic_safe_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inp=root/'inputs';inp.mkdir();out=root/'out';ev=root/'evidence'
            empty,_=prepare(inp,out,ev);self.assertEqual(empty['sources'],[])
            source=inp/'fixture.json';source.write_text(json.dumps(snapshot([entry()]),ensure_ascii=False));before=source.read_bytes()
            _,report=prepare(inp,out,ev);payload=(out/'typed-index.js').read_bytes();prepare(inp,out,ev)
            self.assertEqual((out/'typed-index.js').read_bytes(),payload);self.assertEqual(source.read_bytes(),before)
            self.assertNotIn(b'<script>',payload);self.assertEqual(report['sources'],1)
            parsed=json.loads(payload.decode().removeprefix('window.LawTypedIndex=').removesuffix(';\n'))
            self.assertIn('<script>',parsed['segments'][0]['text'])
    def test_cross_file_duplicate_identity_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inp=root/'in';inp.mkdir()
            for n in ['a','b']:(inp/(n+'.json')).write_text(json.dumps(snapshot([entry()])))
            with self.assertRaisesRegex(ValueError,'Duplicate'):prepare(inp,root/'out',root/'evidence')
    def test_external_link_not_mislabeled_as_knesset(self):
        e=entry();e['document']['fields']['source_url']='https://example.org/source.docx'
        src=build_search_index(snapshot([e]))['sources'][0]
        self.assertEqual(src['link_validation'],'EXTERNAL_HOST_UNVERIFIED');self.assertFalse(src['primary_link_allowed'])
    def test_all_41_types_are_validated_without_schema_extension(self):
        counter=0
        def make(typ):
            nonlocal counter
            counter+=1;n=counter;fields={}
            for key,t in SCHEMA[typ].items():
                if key=='id':value=typ+'_'+str(n)
                elif t.endswith('?'):value=None
                elif t.startswith('['):value=[]
                elif t.startswith('@'):value=make(t[1:])
                elif t=='s':value='סינתטי'
                elif t=='i':value=0
                elif t=='*':value=None
                else:raise AssertionError(t)
                fields[key]=value
            if 'source_url' in fields:fields['source_url']='https://example.org/synthetic.pdf'
            if typ=='FootnoteRef':fields['footnote_id']='foot'
            if typ=='Continuation':fields['target_id']='p'
            return node(typ,**fields)
        e=entry();content=e['document']['fields']['content'];content.append(node('Footnote',id='foot',marker='*',content=['הערת בדיקה']))
        content.extend(make(t) for t in SCHEMA)
        d=snapshot([e]);validate_snapshot(d);idx=build_search_index(d)
        self.assertEqual(len(SCHEMA),41);self.assertEqual(len(idx['sources']),1)

if __name__=='__main__':unittest.main()
