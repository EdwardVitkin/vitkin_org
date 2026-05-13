import zipfile
import xml.etree.ElementTree as ET
import sys
import io

# Ensure stdout uses utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_text(docx_path):
    try:
        doc = zipfile.ZipFile(docx_path)
        xml_content = doc.read('word/document.xml')
        tree = ET.XML(xml_content)
        
        # XML namespace for Word
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        text = []
        for paragraph in tree.findall('.//w:p', namespace):
            para_text = []
            for run in paragraph.findall('.//w:r', namespace):
                t = run.find('w:t', namespace)
                if t is not None and t.text:
                    para_text.append(t.text)
            if para_text:
                text.append(''.join(para_text))
        return '\n'.join(text)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    text = extract_text('16.04.2026-בקשת-השקעה-במסלול-תנופהVitkin.docx')
    with open('proposal_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Extracted text written to proposal_text.txt")
