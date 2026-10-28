#!/usr/bin/env python3
"""Add two editor notes without editing a single byte of normative legal prose.

The exact 9 October 2024 shutdown is independently documented; the statement
that the interruption continues is supplied by the editor as of 28 Oct 2026.
"""
from pathlib import Path
from hashlib import sha256
import re
import sys

LAW_ID = 'article_16c_subsection_c'
REG_ID = 'A_database_for_limiting_marketing_inquiries_article_3_subsection_a'
OLD_SHA = 'e046bc015b1e1a7c0fe471f821cdbc53ca0b120f343929418ac393d004a424d4'
NEW_SHA = 'de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9'
TEXT = 'מיום ז׳ בתשרי התשפ״ה (9 באוקטובר 2024) ועד עתה אין לעוסקים אפשרות לבצע בדיקות במאגר להגבלת פניות שיווקיות.'
IDS = ('article_16c_subsection_c_checks_unavailable_note', 'marketing_registry_reg_3a_checks_unavailable_note')

def note(note_id):
    return ('\r\n'
      f'<ul class="note_button" id="{note_id}" onclick="note_reveal(\'{note_id}\')">\r\n'
      '<li><span class="note_button_text">הערה</span></li>\r\n'
      f'<div class="note_div" onclick="note_reveal(\'{note_id}\')"><span class="note">{TEXT}</span></div>\r\n'
      '</ul>')

def inject(src, section_id, note_id):
    if note_id.encode() in src:
        raise ValueError(f'Duplicate note ID: {note_id}')
    pattern = (rb'(<tr[^>]+id="' + re.escape(section_id.encode()) + rb'"[^>]*>\s*'
               rb'<td class="numbering">.*?</td>\s*<td>)(.*?)'
               rb'(</td>\s*</tr>)')
    matches = list(re.finditer(pattern, src, re.S))
    if len(matches) != 1:
        raise ValueError(f'Wrong section match count: {section_id}: {len(matches)}')
    match = matches[0]
    cell = match.group(2)
    if b'<td' in cell or b'<ul class="note_button"' in cell:
        raise ValueError('Unexpected existing note or nested section')
    if section_id == LAW_ID and 'יוודא שמספר הטלפון' not in cell.decode('utf-8'):
        raise ValueError('Law section identity mismatch')
    if section_id == REG_ID and 'רישום עוסק למאגר יושלם' not in cell.decode('utf-8'):
        raise ValueError('Regulation section identity mismatch')
    return src[:match.end(2)] + note(note_id).encode('utf-8') + src[match.end(2):]

def remove_notes(data):
    for marker in IDS:
        blob = note(marker).encode('utf-8')
        if data.count(blob) != 1:
            raise ValueError('Missing or unexpected note: '+marker)
        data = data.replace(blob, b'', 1)
    return data

def transform(data):
    if sha256(data).hexdigest() != OLD_SHA:
        raise ValueError('Original source SHA mismatch; refusing edit')
    changed = inject(data, LAW_ID, IDS[0])
    changed = inject(changed, REG_ID, IDS[1])
    if sha256(changed).hexdigest() != NEW_SHA:
        raise ValueError('Unexpected resulting source SHA')
    if remove_notes(changed) != data:
        raise ValueError('Anything besides note markup changed')
    return changed

def verify(data):
    if sha256(data).hexdigest() != NEW_SHA:
        raise ValueError('Edited source SHA mismatch')
    restored = remove_notes(data)
    if sha256(restored).hexdigest() != OLD_SHA:
        raise ValueError('Statutory source changed beyond two editor notes')
    return True

def apply(path):
    raw=path.read_bytes()
    digest=sha256(raw).hexdigest()
    if digest == OLD_SHA:
        updated=transform(raw)
        path.write_bytes(updated)
        print('Inserted two editorial notes, SHA256:', NEW_SHA)
    elif digest == NEW_SHA:
        verify(raw)
        print('Notes already installed and verified')
    else:
        raise ValueError('Source changed unexpectedly; refusing edit')

if __name__ == '__main__':
    apply(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1] / 'original/Consumer_Protection_Law.html')
