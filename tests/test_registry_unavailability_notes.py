"""Verify exactly two non-normative editorial notes and identical legal prose bytes."""
import hashlib
from pathlib import Path
import sys
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from add_registry_unavailability_notes import (
    LAW_ID, REG_ID, OLD_SHA, NEW_SHA, TEXT, IDS,
    note, remove_notes, verify
)

class RegistryNotesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'original/Consumer_Protection_Law.html').read_bytes()
        cls.doc=BeautifulSoup(cls.source,'lxml')

    def test_source_only_two_note_additions(self):
        self.assertEqual(hashlib.sha256(self.source).hexdigest(),NEW_SHA)
        self.assertTrue(verify(self.source))
        stripped=remove_notes(self.source)
        self.assertEqual(hashlib.sha256(stripped).hexdigest(),OLD_SHA)
        self.assertEqual(len(self.source)-len(stripped),sum(len(note(x).encode('utf-8')) for x in IDS))

    def test_exact_locations_and_text(self):
        for section_id,note_id in zip((LAW_ID,REG_ID),IDS):
            section=self.doc.find(id=section_id)
            self.assertIsNotNone(section)
            notes=section.select('ul.note_button')
            self.assertEqual(len(notes),1)
            self.assertEqual(notes[0]['id'],note_id)
            self.assertEqual(notes[0].select_one('.note_button_text').get_text(strip=True),'הערה')
            self.assertEqual(notes[0].select_one('.note_div > .note').get_text(strip=True),TEXT)
            self.assertIn("note_reveal",notes[0].get('onclick',''))
        self.assertEqual(self.source.count(TEXT.encode('utf-8')),2)

    def test_no_duplicate_ids_and_no_unrelated_legacy_changes(self):
        for note_id in IDS:
            self.assertEqual(len(self.doc.find_all(id=note_id)),1)
        self.assertIsNotNone(self.doc.find(id='article_16c_subsection_d'))
        self.assertIsNotNone(self.doc.find(id='A_database_for_limiting_marketing_inquiries_article_3_subsection_c'))

if __name__ == '__main__':
    unittest.main()
