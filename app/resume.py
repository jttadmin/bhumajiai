from pathlib import Path

def read_resume(filename):
    p = Path(filename)
    ext = p.suffix.lower()
    if ext in ('.txt', '.md'):
        text = p.read_text(encoding='utf-8-sig')
    elif ext == '.pdf':
        from pypdf import PdfReader
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(str(p)).pages)
    elif ext == '.docx':
        from docx import Document
        text = '\n'.join(x.text for x in Document(str(p)).paragraphs)
    else:
        raise ValueError('Use .txt, .md, .pdf or .docx')
    return text.strip()[:16000]
