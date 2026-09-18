"""Native DOCX regressions. Run with the approved document runtime.

CI installs optional document dependencies. The ordinary stdlib-only environment
may skip this module; skipped cases are never counted as document proof.
"""
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

AVAILABLE = all(importlib.util.find_spec(m) is not None for m in ('docx', 'PIL'))
SOURCE = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py'
SPEC = importlib.util.spec_from_file_location('export_docx_under_test', SOURCE)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


@unittest.skipUnless(AVAILABLE, 'requires approved python-docx and Pillow runtime')
class DocxRegressions(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.temp = tempfile.TemporaryDirectory(prefix='shaping-docx-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bundle = self.root/'bundle'; self.bundle.mkdir()
        self.images = self.root/'images'; self.images.mkdir()
        (self.bundle/'pitch.md').write_text('# Test pitch\n\n```sh\n> output.txt\necho `whoami`\n```\n')
        for name in ('contracts.md','security-owners.md'):
            (self.bundle/name).write_text('| ID | Meaning |\n| --- | --- |\n| A | preserved |\n')
        for name in export.DIAGRAMS:
            (self.bundle/name).write_text('flowchart LR\n A-->B\n')
        self.data = export.bundle(self.bundle)
        manifest = {}
        for d in self.data['diagrams']:
            filename = d['id'].replace('.mmd','.png')
            stream = io.BytesIO(); Image.new('RGB',(50,30),'red').save(stream,format='PNG')
            raw = stream.getvalue(); (self.images/filename).write_bytes(raw)
            manifest[d['id']] = {'source_sha256':d['sha256'],'png':filename,'png_sha256':export.digest(raw)}
        (self.images/'render-manifest.json').write_text(json.dumps(manifest))
        self.output = self.root/'pitch.docx'

    def test_fenced_code_preserves_literal_operators(self):
        from docx import Document
        export.docx_document(self.data,self.images,self.output)
        text = '\n'.join(p.text for p in Document(self.output).paragraphs)
        self.assertIn('> output.txt\necho `whoami`',text)

    def test_concurrent_creation_is_not_overwritten(self):
        from docx.document import Document
        real_save = Document.save
        def race(document, target):
            self.output.write_bytes(b'user replacement')
            return real_save(document,target)
        with patch.object(Document,'save',race):
            with self.assertRaises(export.ExportError):
                export.docx_document(self.data,self.images,self.output)
        self.assertEqual(self.output.read_bytes(),b'user replacement')

    def test_only_verified_image_bytes_are_embedded(self):
        import docx
        from PIL import Image
        original = (self.images/'component.png').read_bytes()
        real_document = docx.Document
        def mutate(*args,**kwargs):
            Image.new('RGB',(50,30),'blue').save(self.images/'component.png')
            return real_document(*args,**kwargs)
        with patch.object(docx,'Document',mutate):
            export.docx_document(self.data,self.images,self.output)
        saved = real_document(self.output)
        image = saved.inline_shapes[0]._inline.graphic.graphicData.pic.blipFill.blip.embed
        self.assertEqual(saved.part.related_parts[image].blob,original)


if __name__ == '__main__':
    unittest.main()
