"""
Echte Word-Kommentare mit OpenXML
Implementiert korrekte Word-Markup-Kommentare nach Microsoft-Spezifikation
"""

from docx import Document
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.package import Package
from docx.parts.document import DocumentPart
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from typing import List, Dict, Tuple, Optional
import xml.etree.ElementTree as ET
import re
import os
import datetime
from pathlib import Path


class RealWordCommentIntegrator:
    """Erstellt echte Word-Kommentare nach OpenXML-Spezifikation"""
    
    def __init__(self, document_path: str):
        self.document_path = document_path
        self.document = Document(document_path)
        self.comment_id = 0
        self.comments_data = []
        
    def add_real_word_comments(self, suggestions: List) -> int:
        """Fügt echte Word-Kommentare hinzu"""
        comments_added = 0
        
        for suggestion in suggestions:
            if self._add_single_real_comment(suggestion):
                comments_added += 1
                
        # Erstelle comments.xml nach dem Hinzufügen aller Kommentare
        if comments_added > 0:
            self._create_comments_xml_part()
            
        return comments_added
    
    def _add_single_real_comment(self, suggestion) -> bool:
        """Fügt einen einzelnen echten Word-Kommentar hinzu"""
        try:
            # Finde den Ziel-Paragraph
            target_paragraph, text_position = self._find_target_paragraph(suggestion)
            
            if not target_paragraph:
                print(f"Text nicht gefunden für Kommentar: {suggestion.original_text[:30]}...")
                return False
            
            # Generiere eindeutige Kommentar-ID
            self.comment_id += 1
            comment_id = str(self.comment_id)
            
            # Speichere Kommentar-Daten
            comment_data = {
                'id': comment_id,
                'author': 'KI Korrekturtool',
                'date': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'initials': 'KI',
                'text': self._format_comment_text(suggestion),
                'category': suggestion.category
            }
            self.comments_data.append(comment_data)
            
            # Füge Comment-Range-Elemente zum Paragraph hinzu
            self._add_comment_range_to_paragraph(target_paragraph, comment_id, suggestion)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Hinzufügen des echten Kommentars: {e}")
            return False
    
    def _find_target_paragraph(self, suggestion) -> Tuple[Optional[object], Optional[int]]:
        """Findet den Ziel-Paragraph für den Kommentar"""
        search_text = suggestion.original_text.strip()
        
        # Verkürze zu langen Text
        if len(search_text) > 40:
            words = search_text.split()[:6]
            search_text = ' '.join(words)
        
        search_lower = search_text.lower()
        
        for paragraph in self.document.paragraphs:
            para_text = paragraph.text.lower()
            if search_lower in para_text:
                position = para_text.find(search_lower)
                return paragraph, position
                
        return None, None
    
    def _format_comment_text(self, suggestion) -> str:
        """Formatiert den Kommentar-Text"""
        category_names = {
            'grammar': 'Grammatik',
            'style': 'Stil',
            'clarity': 'Klarheit',
            'academic': 'Wissenschaftlicher Ausdruck'
        }
        
        category = category_names.get(suggestion.category.lower(), 'Allgemein')
        
        # Ohne Zeilenwechsel in XML - wird später behandelt
        comment_text = f"KI-Verbesserung: {category} - "
        comment_text += f"Vorschlag: {suggestion.suggested_text} - "
        comment_text += f"Begründung: {suggestion.reason} - "
        comment_text += f"Vertrauen: {suggestion.confidence:.0%}"
        
        return comment_text
    
    def _add_comment_range_to_paragraph(self, paragraph, comment_id: str, suggestion):
        """Fügt CommentRange-Elemente zum Paragraph hinzu"""
        try:
            p_elem = paragraph._element
            
            # Finde die Position des zu kommentierenden Textes
            para_text = paragraph.text
            search_text = suggestion.original_text.strip()[:40]
            
            # Vereinfachte Implementierung: Kommentiere den gesamten Paragraph
            # In einer vollständigen Implementierung würde man den exakten Text-Range finden
            
            # 1. CommentRangeStart am Anfang des Paragraphs
            comment_range_start = OxmlElement('w:commentRangeStart')
            comment_range_start.set(qn('w:id'), comment_id)
            
            # Füge am Anfang des Paragraphs ein (vor dem ersten Run)
            if len(p_elem) > 0:
                p_elem.insert(0, comment_range_start)
            else:
                p_elem.append(comment_range_start)
            
            # 2. CommentRangeEnd am Ende des Paragraphs
            comment_range_end = OxmlElement('w:commentRangeEnd')
            comment_range_end.set(qn('w:id'), comment_id)
            p_elem.append(comment_range_end)
            
            # 3. CommentReference als eigener Run
            comment_ref_run = OxmlElement('w:r')
            comment_reference = OxmlElement('w:commentReference')
            comment_reference.set(qn('w:id'), comment_id)
            comment_ref_run.append(comment_reference)
            p_elem.append(comment_ref_run)
            
            print(f"✓ Comment-Range für ID {comment_id} hinzugefügt")
            
        except Exception as e:
            print(f"Fehler beim Comment-Range: {e}")
    
    def _create_comments_xml_part(self):
        """Erstellt die comments.xml Part im Word-Dokument"""
        try:
            # Erstelle Comments-XML-Inhalt
            comments_xml_content = self._generate_comments_xml()
            
            # Zugriff auf das Package
            package = self.document.part.package
            
            # Prüfe ob comments.xml bereits existiert
            comments_part = None
            for rel in self.document.part.rels:
                rel_obj = self.document.part.rels[rel]
                if 'comments' in rel_obj.target_ref:
                    comments_part = rel_obj.target_part
                    break
            
            if comments_part:
                # Aktualisiere existierende Comments
                comments_part._blob = comments_xml_content.encode('utf-8')
                print(f"✓ Existierende comments.xml aktualisiert")
            else:
                # Erstelle neue Comments-Part
                from docx.opc.part import Part
                from docx.opc.packuri import PackURI
                
                # Erstelle Part-URI
                comments_uri = PackURI('/word/comments.xml')
                
                # Erstelle neue Part
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml'
                comments_part = Part(
                    partname=comments_uri,
                    content_type=content_type,
                    blob=comments_xml_content.encode('utf-8'),
                    package=package
                )
                
                # Füge Part zum Package hinzu
                package._parts[comments_uri] = comments_part
                
                # Erstelle Relationship vom Document zur Comments-Part
                rel_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
                self.document.part.relate_to(comments_part, rel_type)
                
                print(f"✓ Neue comments.xml Part erstellt mit {len(self.comments_data)} Kommentaren")
                
        except Exception as e:
            print(f"Fehler beim Erstellen der comments.xml: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_comments_xml(self) -> str:
        """Generiert den XML-Inhalt für comments.xml"""
        xml_lines = []
        
        # XML Header
        xml_lines.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        
        # Root Element mit Namespaces
        xml_lines.append('<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">')
        
        # Kommentare
        for comment in self.comments_data:
            category_colors = {
                'grammar': 'DC143C',    # Crimson
                'style': 'FF8C00',      # Dark Orange  
                'clarity': '228B22',    # Forest Green
                'academic': '4169E1'    # Royal Blue
            }
            
            color = category_colors.get(comment['category'], '808080')
            
            # Escape den Text richtig
            escaped_text = self._escape_xml(comment["text"])
            escaped_author = self._escape_xml(comment["author"])
            
            xml_lines.append(f'    <w:comment w:id="{comment["id"]}" w:author="{escaped_author}" w:date="{comment["date"]}" w:initials="{comment["initials"]}">')
            xml_lines.append('        <w:p>')
            xml_lines.append('            <w:pPr>')
            xml_lines.append('                <w:pStyle w:val="CommentText"/>')
            xml_lines.append('            </w:pPr>')
            xml_lines.append('            <w:r>')
            xml_lines.append('                <w:rPr>')
            xml_lines.append(f'                    <w:color w:val="{color}"/>')
            xml_lines.append('                    <w:sz w:val="20"/>')
            xml_lines.append('                </w:rPr>')
            xml_lines.append(f'                <w:t xml:space="preserve">{escaped_text}</w:t>')
            xml_lines.append('            </w:r>')
            xml_lines.append('        </w:p>')
            xml_lines.append('    </w:comment>')
        
        # Root schließen
        xml_lines.append('</w:comments>')
        
        return '\n'.join(xml_lines)
    
    def _escape_xml(self, text: str) -> str:
        """Escaped XML-Sonderzeichen"""
        if not text:
            return ""
        # Reihenfolge ist wichtig! & muss zuerst escaped werden
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;')
                   .replace('\n', ' ')
                   .replace('\r', ' ')
                   .replace('\t', ' '))
    
    def save_document(self, output_path: str) -> bool:
        """Speichert das Dokument mit echten Kommentaren"""
        try:
            self.document.save(output_path)
            print(f"✅ Dokument mit echten Word-Kommentaren gespeichert: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def create_backup(self) -> str:
        """Erstellt Backup des Originaldokuments"""
        backup_path = self.document_path.replace('.docx', '_backup.docx')
        try:
            import shutil
            shutil.copy2(self.document_path, backup_path)
            print(f"🔒 Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup-Fehler: {e}")
            return ""


def main():
    """Test echte Word-Kommentare"""
    from dataclasses import dataclass
    
    @dataclass 
    class MockSuggestion:
        original_text: str
        suggested_text: str
        reason: str
        category: str
        confidence: float
        position: Tuple[int, int]
    
    document_path = '/Users/max/Korrekturtool BA/Volltext_BA_Max Thomsen Kopie.docx'
    
    # Test-Suggestions
    test_suggestions = [
        MockSuggestion(
            original_text="Large Language Models",
            suggested_text="Large Language Models (LLMs)", 
            reason="Abkürzung beim ersten Gebrauch ausschreiben",
            category="academic",
            confidence=0.9,
            position=(100, 120)
        ),
        MockSuggestion(
            original_text="Relevanz von KI",
            suggested_text="Relevanz künstlicher Intelligenz", 
            reason="Abkürzung ausschreiben für bessere Verständlichkeit",
            category="clarity",
            confidence=0.8,
            position=(200, 220)
        )
    ]
    
    print("=== Teste ECHTE Word-Kommentare ===")
    
    integrator = RealWordCommentIntegrator(document_path)
    backup_path = integrator.create_backup()
    
    # Füge echte Word-Kommentare hinzu
    comments_added = integrator.add_real_word_comments(test_suggestions)
    
    # Speichere mit echten Kommentaren
    output_path = document_path.replace('.docx', '_ECHTE_WORD_KOMMENTARE.docx')
    success = integrator.save_document(output_path)
    
    if success:
        print(f"🎉 {comments_added} echte Word-Kommentare erfolgreich hinzugefügt!")
        print(f"📄 Öffnen Sie {output_path} in Microsoft Word")
        print(f"💡 Gehen Sie zu 'Überprüfen' > 'Kommentare anzeigen' um die Kommentare zu sehen")
    else:
        print("❌ Fehler beim Erstellen der echten Word-Kommentare")


if __name__ == "__main__":
    main()