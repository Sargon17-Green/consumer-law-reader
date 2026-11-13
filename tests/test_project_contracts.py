from pathlib import Path
from unittest.mock import patch
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import validate_project_docs as docs

class ProjectContractTests(unittest.TestCase):
    def test_complete_catalog_and_documents_validate(self):
        self.assertGreaterEqual(docs.validate()['requirements'],50)
    def reject(self,mutate,message):
        path=ROOT/'docs/requirements.json';data=json.loads(path.read_text());mutate(data)
        read=Path.read_text
        def fixture(p,*args,**kwargs):
            return json.dumps(data,ensure_ascii=False) if p==path else read(p,*args,**kwargs)
        with patch.object(Path,'read_text',fixture):
            with self.assertRaisesRegex(ValueError,message):docs.validate()
    def test_duplicate_requirement_is_rejected(self):
        self.reject(lambda d:d['requirements'].append(copy.deepcopy(d['requirements'][0])),'duplicate ID')
    def test_publication_requires_real_metadata(self):
        self.reject(lambda d:d['requirements'][0]['published'].__setitem__('Web',None),'Publication/state mismatch')
    def test_broken_implementation_link_is_rejected(self):
        self.reject(lambda d:d['requirements'][0]['implementation'].append('nonexistent-contract-file'),'Broken implementation')
    def test_unknown_status_is_rejected(self):
        self.reject(lambda d:d['requirements'][0]['status'].__setitem__('Web','PASS assumed'),'Unknown state')
    def test_generated_document_cannot_drift(self):
        target=ROOT/'PRODUCT_REQUIREMENTS.md';read=Path.read_text
        def fixture(p,*args,**kwargs):
            value=read(p,*args,**kwargs);return value+'\n' if p==target else value
        with patch.object(Path,'read_text',fixture):
            with self.assertRaisesRegex(ValueError,'Markdown is stale'):docs.validate()

if __name__=='__main__':unittest.main()
