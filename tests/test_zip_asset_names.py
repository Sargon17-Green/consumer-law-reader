from io import BytesIO
import struct
import unittest
from zipfile import ZipFile
from scripts.bundled_assets import zip_members


def clear_utf8_flag(body,entries=None):
    data=bytearray(body)
    for signature,offset in ((b'PK\x03\x04',6),(b'PK\x01\x02',8)):
        cursor=0
        index=0
        while (cursor:=data.find(signature,cursor))>=0:
            if entries is None or index in entries:
                flags=struct.unpack_from('<H',data,cursor+offset)[0]
                struct.pack_into('<H',data,cursor+offset,flags&~0x800)
            cursor+=4
            index+=1
    return bytes(data)


class ZipAssetNameTests(unittest.TestCase):
    def test_real_utf8_bytes_with_missing_flag_are_read_without_rewriting(self):
        stream=BytesIO()
        with ZipFile(stream,'w') as archive:archive.writestr('assets/www/מסמך.doc',b'exact fixture bytes')
        body=clear_utf8_flag(stream.getvalue())
        with ZipFile(BytesIO(body)) as archive:
            self.assertNotIn('assets/www/מסמך.doc',archive.namelist())
            members=zip_members(archive)
            self.assertEqual(archive.read(members['assets/www/מסמך.doc']),b'exact fixture bytes')

    def test_duplicate_canonical_member_cannot_hide_behind_zip_flags(self):
        stream=BytesIO()
        with ZipFile(stream,'w') as archive:
            archive.writestr('assets/www/מסמך.doc',b'first')
            with self.assertWarns(UserWarning):archive.writestr('assets/www/מסמך.doc',b'hostile duplicate')
        with ZipFile(BytesIO(clear_utf8_flag(stream.getvalue(),entries={0}))) as archive:
            self.assertEqual(len(set(archive.namelist())),2)
            with self.assertRaisesRegex(ValueError,'Duplicate canonical ZIP member'):zip_members(archive)
