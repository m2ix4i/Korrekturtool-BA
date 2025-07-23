#!/usr/bin/env python3
"""
Vereinfachter Test für Word-Kommentare 
Verwendet direkten Zip-Zugriff auf DOCX-Struktur
"""

import zipfile
import xml.etree.ElementTree as ET
import shutil
import os
from pathlib import Path


def create_simple_word_comment():
    """Erstellt einen einfachen Word-Kommentar durch direkte DOCX-Manipulation"""
    
    source_path = '/Users/max/Korrekturtool BA/Volltext_BA_Max Thomsen Kopie.docx'
    test_path = '/Users/max/Korrekturtool BA/TEST_SIMPLE_COMMENT.docx'
    
    # Kopiere für Test
    shutil.copy2(source_path, test_path)
    
    print("=== SIMPLE WORD COMMENT TEST ===")
    print(f"Test-Dokument: {test_path}")
    
    # DOCX ist ein ZIP-File - arbeite direkt damit
    temp_dir = '/tmp/docx_temp'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # 1. Extrahiere DOCX
        with zipfile.ZipFile(test_path, 'r') as zip_file:
            zip_file.extractall(temp_dir)
        print("✓ DOCX extrahiert")
        
        # 2. Lese document.xml
        doc_xml_path = os.path.join(temp_dir, 'word', 'document.xml')
        if not os.path.exists(doc_xml_path):
            print("❌ document.xml nicht gefunden")
            return False
            
        # Parse document.xml
        tree = ET.parse(doc_xml_path)
        root = tree.getroot()
        
        # Namespace definieren
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # Finde den ersten Paragraph mit Text
        paragraphs = root.findall('.//w:p', ns)
        target_paragraph = None
        
        for para in paragraphs:
            text_elements = para.findall('.//w:t', ns)
            if text_elements and len(''.join(t.text or '' for t in text_elements).strip()) > 10:
                target_paragraph = para
                break
        
        if target_paragraph is None:
            print("❌ Kein geeigneter Paragraph gefunden")
            return False
            
        para_text = ''.join(t.text or '' for t in target_paragraph.findall('.//w:t', ns))
        print(f"✓ Ziel-Paragraph gefunden: {para_text[:50]}...")
        
        # 3. Füge Comment-Range-Elemente hinzu
        comment_id = "0"
        
        # CommentRangeStart am Anfang
        comment_start = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentRangeStart')
        comment_start.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
        target_paragraph.insert(0, comment_start)
        
        # CommentRangeEnd am Ende
        comment_end = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentRangeEnd')
        comment_end.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
        target_paragraph.append(comment_end)
        
        # CommentReference in eigenem Run
        comment_ref_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        comment_ref = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentReference')
        comment_ref.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
        comment_ref_run.append(comment_ref)
        target_paragraph.append(comment_ref_run)
        
        print("✓ Comment-Range-Elemente hinzugefügt")
        
        # Speichere modifizierte document.xml
        tree.write(doc_xml_path, encoding='utf-8', xml_declaration=True)
        
        # 4. Erstelle comments.xml
        comments_xml_path = os.path.join(temp_dir, 'word', 'comments.xml')
        
        comments_content = '''<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:comment w:id="0" w:author="Max Tester" w:date="2025-01-22T14:00:00Z" w:initials="MT">
        <w:p>
            <w:pPr>
                <w:pStyle w:val="CommentText"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>
                    <w:sz w:val="18"/>
                    <w:color w:val="E36C0A"/>
                </w:rPr>
                <w:t>TEST: Dies ist ein definierter Kommentar-Inhalt von Max Tester!</w:t>
            </w:r>
        </w:p>
    </w:comment>
</w:comments>'''
        
        with open(comments_xml_path, 'w', encoding='utf-8') as f:
            f.write(comments_content)
        print("✓ comments.xml erstellt")
        
        # 5. Aktualisiere [Content_Types].xml
        content_types_path = os.path.join(temp_dir, '[Content_Types].xml')
        if os.path.exists(content_types_path):
            ct_tree = ET.parse(content_types_path)
            ct_root = ct_tree.getroot()
            
            # Füge Comments-ContentType hinzu falls nicht vorhanden
            existing = ct_root.find(".//Default[@Extension='comments']")
            if existing is None:
                default = ET.Element('Default')
                default.set('Extension', 'comments') 
                default.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')
                ct_root.append(default)
                
                ct_tree.write(content_types_path, encoding='utf-8', xml_declaration=True)
                print("✓ [Content_Types].xml aktualisiert")
        
        # 6. Aktualisiere _rels/document.xml.rels
        rels_path = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path)
            rels_root = rels_tree.getroot()
            
            # Finde höchste rId
            max_id = 0
            for rel in rels_root.findall('Relationship'):
                rid = rel.get('Id', '')
                if rid.startswith('rId'):
                    try:
                        num = int(rid[3:])
                        max_id = max(max_id, num)
                    except:
                        pass
            
            # Füge Comments-Relationship hinzu
            new_rid = f"rId{max_id + 1}"
            relationship = ET.Element('Relationship')
            relationship.set('Id', new_rid)
            relationship.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
            relationship.set('Target', 'comments.xml')
            rels_root.append(relationship)
            
            rels_tree.write(rels_path, encoding='utf-8', xml_declaration=True)
            print("✓ document.xml.rels aktualisiert")
        
        # 7. Erstelle neue DOCX
        with zipfile.ZipFile(test_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root_dir, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arc_name)
        
        print(f"✅ Test-Dokument mit Kommentar erstellt: {test_path}")
        print("\n💡 Jetzt in Word öffnen und prüfen:")
        print("   1. Überprüfen > Kommentare anzeigen")
        print("   2. Kommentar sollte sichtbar sein")
        print("   3. Author: 'Max Tester'")
        print("   4. Text: 'TEST: Dies ist ein definierter Kommentar-Inhalt...'")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    create_simple_word_comment()