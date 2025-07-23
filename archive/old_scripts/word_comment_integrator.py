"""
Word-Markup-Kommentar Integration
Erstellt echte Word-Kommentare (wie die Überprüfungs-/Markup-Funktion)
"""

from docx import Document
from docx.oxml import OxmlElement, ns
from docx.oxml.ns import qn, nsdecls
from docx.shared import RGBColor
from typing import List, Dict, Tuple, Optional
import re
import os
import uuid
from pathlib import Path


class WordCommentIntegrator:
    """Erstellt echte Word-Kommentare für Verbesserungsvorschläge"""
    
    def __init__(self, document_path: str):
        self.document_path = document_path
        self.document = Document(document_path)
        self.comment_counter = 0
        self.comments_part = None
        self._init_comments_structure()
    
    def _init_comments_structure(self):
        """Initialisiert die Kommentar-Struktur in Word"""
        try:
            # Füge Comments-Part zur Word-Datei hinzu wenn nicht vorhanden
            package = self.document.part.package
            comments_part = None
            
            # Suche nach vorhandenen Comments
            for rel in package.part_rels.values():
                if 'comments' in rel.target_ref:
                    comments_part = rel.target_part
                    break
            
            if not comments_part:
                # Erstelle neue Comments-Part
                comments_xml = self._create_comments_xml()
                comments_part = package.create_part('/word/comments.xml', 
                                                   'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml', 
                                                   comments_xml)
                
                # Füge Beziehung hinzu
                self.document.part.relate_to(comments_part, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
            
            self.comments_part = comments_part
            
        except Exception as e:
            print(f"Fehler bei Comments-Initialisierung: {e}")
            self.comments_part = None
    
    def _create_comments_xml(self) -> bytes:
        """Erstellt die XML-Struktur für Kommentare"""
        xml_content = f'''<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:comments {nsdecls('w')}>
</w:comments>'''
        return xml_content.encode('utf-8')
    
    def add_word_comments(self, suggestions: List) -> int:
        """Fügt Word-Kommentare für alle Suggestions hinzu"""
        if not self.comments_part:
            print("Kommentar-System konnte nicht initialisiert werden")
            return 0
        
        comments_added = 0
        
        for suggestion in suggestions:
            if self._add_single_word_comment(suggestion):
                comments_added += 1
        
        return comments_added
    
    def _add_single_word_comment(self, suggestion) -> bool:
        """Fügt einen einzelnen Word-Kommentar hinzu"""
        try:
            # Finde den passenden Absatz und Text
            target_paragraph, text_range = self._find_text_location(suggestion)
            
            if not target_paragraph or not text_range:
                print(f"Text nicht gefunden für: {suggestion.original_text[:30]}...")
                return False
            
            start_pos, end_pos = text_range
            self.comment_counter += 1
            comment_id = str(self.comment_counter)
            
            # Erstelle Kommentar-Content
            comment_text = self._format_comment_text(suggestion)
            
            # Füge Kommentar zur Comments-XML hinzu
            self._add_comment_to_xml(comment_id, comment_text, suggestion.category)
            
            # Füge Kommentar-Referenzen zum Paragraph hinzu
            self._add_comment_references_to_paragraph(target_paragraph, comment_id, start_pos, end_pos)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Hinzufügen des Word-Kommentars: {e}")
            return False
    
    def _find_text_location(self, suggestion) -> Tuple[Optional[object], Optional[Tuple[int, int]]]:
        """Findet die Position des zu kommentierenden Textes"""
        search_text = suggestion.original_text.strip()
        
        # Verkürze Suchtext wenn zu lang
        if len(search_text) > 50:
            words = search_text.split()[:8]  # Erste 8 Wörter
            search_text = ' '.join(words)
        
        # Suche in allen Absätzen
        for paragraph in self.document.paragraphs:
            paragraph_text = paragraph.text
            
            # Finde Text-Position
            pos = paragraph_text.lower().find(search_text.lower())
            if pos != -1:
                return paragraph, (pos, pos + len(search_text))
        
        return None, None
    
    def _format_comment_text(self, suggestion) -> str:
        """Formatiert den Kommentar-Text"""
        category_icons = {
            'grammar': '🔴 GRAMMATIK',
            'style': '🟡 STIL', 
            'clarity': '🟢 KLARHEIT',
            'academic': '🔵 WISSENSCHAFT'
        }
        
        icon = category_icons.get(suggestion.category.lower(), '⚪ ALLGEMEIN')
        
        comment = f"{icon}\n\n"
        comment += f"💡 VORSCHLAG: {suggestion.suggested_text}\n\n"
        comment += f"📝 BEGRÜNDUNG: {suggestion.reason}\n\n"
        comment += f"🎯 KONFIDENZ: {suggestion.confidence:.1f}"
        
        return comment
    
    def _add_comment_to_xml(self, comment_id: str, comment_text: str, category: str):
        """Fügt Kommentar zur Comments-XML hinzu"""
        try:
            # Parse vorhandene Comments-XML
            from xml.etree import ElementTree as ET
            
            comments_xml = self.comments_part.blob
            root = ET.fromstring(comments_xml)
            
            # Erstelle neuen Kommentar-Element
            comment_elem = ET.SubElement(root, qn('w:comment'))
            comment_elem.set(qn('w:id'), comment_id)
            comment_elem.set(qn('w:author'), 'KI-Korrekturtool')
            comment_elem.set(qn('w:date'), '2025-01-22T00:00:00Z')
            comment_elem.set(qn('w:initials'), 'KI')
            
            # Füge Paragraph mit Text hinzu
            p_elem = ET.SubElement(comment_elem, qn('w:p'))
            
            # Paragraph Properties mit Farbe je nach Kategorie
            pPr = ET.SubElement(p_elem, qn('w:pPr'))
            
            # Run mit Text
            r_elem = ET.SubElement(p_elem, qn('w:r'))
            
            # Run Properties
            rPr = ET.SubElement(r_elem, qn('w:rPr'))
            color = ET.SubElement(rPr, qn('w:color'))
            
            # Farbe nach Kategorie
            color_map = {
                'grammar': 'D50000',    # Rot
                'style': 'FF8F00',      # Orange
                'clarity': '388E3C',    # Grün  
                'academic': '1976D2'    # Blau
            }
            color.set(qn('w:val'), color_map.get(category.lower(), '424242'))
            
            # Text-Inhalt
            t_elem = ET.SubElement(r_elem, qn('w:t'))
            t_elem.text = comment_text
            
            # Speichere aktualisierte XML
            updated_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            self.comments_part._blob = updated_xml
            
        except Exception as e:
            print(f"Fehler beim XML-Update: {e}")
    
    def _add_comment_references_to_paragraph(self, paragraph, comment_id: str, start_pos: int, end_pos: int):
        """Fügt Kommentar-Referenzen zum Absatz hinzu"""
        try:
            # Hole Paragraph-XML
            p_elem = paragraph._element
            
            # Finde den Text-Run, der den zu kommentierenden Text enthält
            current_pos = 0
            target_run = None
            
            for run in paragraph.runs:
                run_text = run.text
                run_end = current_pos + len(run_text)
                
                if current_pos <= start_pos < run_end:
                    target_run = run
                    break
                current_pos = run_end
            
            if not target_run:
                return
            
            # Teile den Run an der Start-Position
            run_elem = target_run._element
            run_text = target_run.text
            
            # Text vor Kommentar-Bereich
            before_text = run_text[:start_pos - current_pos]
            # Kommentierter Text  
            comment_text = run_text[start_pos - current_pos:end_pos - current_pos]
            # Text nach Kommentar-Bereich
            after_text = run_text[end_pos - current_pos:]
            
            # Leere ursprünglichen Run
            run_elem.clear()
            
            # Füge Runs hinzu
            if before_text:
                self._add_text_run(run_elem, before_text)
            
            # Kommentar-Start
            self._add_comment_range_start(run_elem, comment_id)
            
            # Kommentierter Text
            if comment_text:
                self._add_text_run(run_elem, comment_text)
            
            # Kommentar-Ende
            self._add_comment_range_end(run_elem, comment_id)
            
            if after_text:
                self._add_text_run(run_elem, after_text)
                
        except Exception as e:
            print(f"Fehler bei Paragraph-Update: {e}")
    
    def _add_text_run(self, parent_elem, text: str):
        """Fügt Text-Run hinzu"""
        r_elem = OxmlElement('w:r')
        t_elem = OxmlElement('w:t')
        t_elem.text = text
        r_elem.append(t_elem)
        parent_elem.append(r_elem)
    
    def _add_comment_range_start(self, parent_elem, comment_id: str):
        """Fügt Kommentar-Start hinzu"""
        start_elem = OxmlElement('w:commentRangeStart')
        start_elem.set(qn('w:id'), comment_id)
        parent_elem.append(start_elem)
    
    def _add_comment_range_end(self, parent_elem, comment_id: str):
        """Fügt Kommentar-Ende hinzu"""
        end_elem = OxmlElement('w:commentRangeEnd')
        end_elem.set(qn('w:id'), comment_id)
        parent_elem.append(end_elem)
        
        # Kommentar-Referenz
        ref_run = OxmlElement('w:r')
        ref_elem = OxmlElement('w:commentReference')
        ref_elem.set(qn('w:id'), comment_id)
        ref_run.append(ref_elem)
        parent_elem.append(ref_run)
    
    def save_document(self, output_path: str) -> bool:
        """Speichert das Dokument mit Kommentaren"""
        try:
            self.document.save(output_path)
            print(f"✅ Dokument mit Word-Kommentaren gespeichert: {output_path}")
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
            print(f"❌ Fehler beim Backup: {e}")
            return ""


def main():
    """Test-Funktion"""
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
    
    integrator = WordCommentIntegrator(document_path)
    
    # Test-Suggestions
    test_suggestions = [
        MockSuggestion(
            original_text="Large Language Models",
            suggested_text="Large Language Models (LLMs)", 
            reason="Abkürzung beim ersten Gebrauch ausschreiben",
            category="academic",
            confidence=0.9,
            position=(100, 120)
        )
    ]
    
    # Backup erstellen
    backup_path = integrator.create_backup()
    
    # Word-Kommentare hinzufügen  
    comments_added = integrator.add_word_comments(test_suggestions)
    
    # Speichern
    output_path = document_path.replace('.docx', '_word_comments.docx')
    success = integrator.save_document(output_path)
    
    if success:
        print(f"🎉 Test erfolgreich: {comments_added} Word-Kommentare hinzugefügt")
        print(f"   Öffnen Sie {output_path} in Word um die Kommentare zu sehen!")


if __name__ == "__main__":
    main()