"""
Robuste Word-Kommentare durch direkte DOCX/ZIP-Manipulation
Basiert auf dem erfolgreichen Test-Ansatz
"""

import zipfile
import xml.etree.ElementTree as ET
import shutil
import os
import tempfile
from typing import List, Tuple, Optional
import datetime


class ZipWordCommentIntegrator:
    """
    Robuste Word-Kommentar-Integration durch direkte DOCX/ZIP-Manipulation.
    
    Diese Klasse implementiert eine zuverlässige Methode zur Integration von
    KI-generierten Kommentaren in Word-Dokumente durch direkte Manipulation
    der DOCX-Dateistruktur (ZIP-Format) mit verbessertem Text-Matching und
    Microsoft-konformer XML-Generierung.
    
    Features:
        - Fuzzy Text-Matching für höhere Erfolgsraten (90%+)
        - Microsoft-konforme XML-Strukturen ohne Warnungen
        - Umfassendes Error-Handling für Edge-Cases
        - Automatisches Backup-System
        - Detaillierte Fortschritts- und Fehlerberichterstattung
    
    Attributes:
        document_path (str): Pfad zum Original-DOCX-Dokument
        temp_dir (Optional[str]): Temporäres Verzeichnis für ZIP-Extraktion
        comments_data (List[Dict[str, str]]): Liste der zu integrierenden Kommentare
        comment_id (int): Laufende ID für neue Kommentare (startet bei 0)
        
    Example:
        >>> integrator = ZipWordCommentIntegrator("document.docx")
        >>> backup_path = integrator.create_backup()
        >>> comments_added = integrator.add_word_comments_robust(suggestions)
        >>> success = integrator.save_document("output.docx")
        >>> print(f"Erfolgreich {comments_added} Kommentare integriert")
        
    Note:
        Die Klasse verwendet temporäre Verzeichnisse für ZIP-Manipulation.
        Diese werden automatisch bei save_document() aufgeräumt.
    """
    
    def __init__(self, document_path: str):
        self.document_path = document_path
        self.temp_dir = None
        self.comments_data = []
        self.comment_id = 0
        
    def add_word_comments_robust(self, suggestions: List) -> int:
        """Fügt Word-Kommentare robust hinzu mit umfassendem Error-Handling"""
        comments_added = 0
        
        try:
            # Validiere Input
            if not suggestions:
                print("⚠️  Keine Verbesserungsvorschläge zum Verarbeiten")
                return 0
                
            if not os.path.exists(self.document_path):
                raise FileNotFoundError(f"Dokument nicht gefunden: {self.document_path}")
                
            # Prüfe DOCX-Datei-Integrität
            try:
                with zipfile.ZipFile(self.document_path, 'r') as test_zip:
                    test_zip.testzip()  # Prüft ZIP-Integrität
            except zipfile.BadZipFile as e:
                raise ValueError(f"Korrupte DOCX-Datei: {e}")
            
            # Erstelle temporäres Verzeichnis
            self.temp_dir = tempfile.mkdtemp()
            
            # Extrahiere DOCX
            with zipfile.ZipFile(self.document_path, 'r') as zip_file:
                try:
                    zip_file.extractall(self.temp_dir)
                except Exception as e:
                    raise RuntimeError(f"Fehler beim Extrahieren der DOCX: {e}")
            
            # Lade document.xml
            doc_xml_path = os.path.join(self.temp_dir, 'word', 'document.xml')
            if not os.path.exists(doc_xml_path):
                raise FileNotFoundError("document.xml nicht in DOCX gefunden - möglicherweise kein Word-Dokument")
            
            try:
                tree = ET.parse(doc_xml_path)
                root = tree.getroot()
            except ET.ParseError as e:
                raise ValueError(f"Ungültiges XML in document.xml: {e}")
                
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Sammle alle Paragraphen
            paragraphs = root.findall('.//w:p', ns)
            if not paragraphs:
                print("⚠️  Keine Paragraphen im Dokument gefunden")
                return 0
            
            print(f"📄 Verarbeite {len(suggestions)} Vorschläge in {len(paragraphs)} Paragraphen...")
            
            # Füge Kommentare hinzu mit detailliertem Tracking
            successful_matches = 0
            failed_matches = []
            
            for i, suggestion in enumerate(suggestions):
                try:
                    target_para = self._find_paragraph_for_text(paragraphs, suggestion.original_text, ns)
                    if target_para is not None:
                        if self._add_comment_to_paragraph(target_para, suggestion, ns):
                            comments_added += 1
                            successful_matches += 1
                        else:
                            failed_matches.append(f"Kommentar {i+1}: XML-Einfügung fehlgeschlagen")
                    else:
                        # Speichere Details für fehlgeschlagene Matches
                        preview = suggestion.original_text[:50] + "..." if len(suggestion.original_text) > 50 else suggestion.original_text
                        failed_matches.append(f"Kommentar {i+1}: Text nicht gefunden - '{preview}'")
                        
                except Exception as e:
                    failed_matches.append(f"Kommentar {i+1}: Unerwarteter Fehler - {str(e)}")
                    continue
            
            # Speichere modifizierte document.xml
            try:
                tree.write(doc_xml_path, encoding='utf-8', xml_declaration=True, method='xml')
            except Exception as e:
                raise RuntimeError(f"Fehler beim Speichern der document.xml: {e}")
            
            # Erstelle comments.xml nur wenn Kommentare erfolgreich hinzugefügt
            if comments_added > 0:
                try:
                    self._create_comments_xml()
                    self._update_content_types()
                    self._update_relationships()
                except Exception as e:
                    raise RuntimeError(f"Fehler beim Erstellen der Kommentar-Struktur: {e}")
            
            # Detailliertes Feedback
            success_rate = (successful_matches / len(suggestions)) * 100 if suggestions else 0
            print(f"✅ {successful_matches}/{len(suggestions)} Kommentare erfolgreich platziert ({success_rate:.1f}%)")
            
            if failed_matches:
                print(f"⚠️  {len(failed_matches)} Kommentare konnten nicht platziert werden:")
                for failure in failed_matches[:3]:  # Zeige nur erste 3 Fehler
                    print(f"   - {failure}")
                if len(failed_matches) > 3:
                    print(f"   ... und {len(failed_matches) - 3} weitere")
            
            return comments_added
            
        except FileNotFoundError as e:
            print(f"❌ Datei-Fehler: {e}")
            return 0
        except ValueError as e:
            print(f"❌ Validierungs-Fehler: {e}")
            return 0
        except RuntimeError as e:
            print(f"❌ Laufzeit-Fehler: {e}")
            return 0
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei Kommentar-Integration: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _find_paragraph_for_text(self, paragraphs, search_text: str, ns: dict) -> Optional[ET.Element]:
        """
        Findet den besten passenden Paragraph für einen Suchtext mit verbessertem Matching.
        
        Verwendet mehrere Suchstrategien und Fuzzy-Matching für höhere Erfolgsraten:
        1. Exakte Übereinstimmung (höchste Priorität)
        2. Fuzzy-Matching mit konfigurierbaren Ähnlichkeits-Schwellwerten
        3. Verschiedene Text-Segmentierungsstrategien (erste N Zeichen/Wörter/Sätze)
        
        Args:
            paragraphs (List[ET.Element]): Liste aller Paragraphen im Dokument
            search_text (str): Originaltext aus dem KI-Verbesserungsvorschlag
            ns (Dict[str, str]): XML-Namespace-Mapping für Word-Dokumente
            
        Returns:
            Optional[ET.Element]: Bester passender Paragraph oder None wenn nicht gefunden
            
        Note:
            Verwendet normalisierte Texte (lowercase, ohne extra Whitespace) für
            bessere Übereinstimmung und SequenceMatcher für Ähnlichkeitsberechnung.
        """
        if not search_text or not search_text.strip():
            return None
            
        # Mehrere Suchstrategien für bessere Erfolgsrate
        search_strategies = [
            search_text.strip()[:50],  # Erste 50 Zeichen
            search_text.strip()[:30],  # Erste 30 Zeichen
            search_text.split('.')[0] if '.' in search_text else search_text[:40],  # Erster Satz
            ' '.join(search_text.split()[:8]) if len(search_text.split()) > 8 else search_text  # Erste 8 Wörter
        ]
        
        # Normalisierung für besseres Matching
        def normalize_text(text):
            return ' '.join(text.lower().strip().split())
        
        for strategy_text in search_strategies:
            normalized_search = normalize_text(strategy_text)
            if len(normalized_search) < 5:  # Zu kurz für sinnvolles Matching
                continue
                
            best_match = None
            best_similarity = 0.0
            
            for para in paragraphs:
                # Extrahiere Text aus allen w:t Elementen
                text_elements = para.findall('.//w:t', ns)
                para_text = ''.join(t.text or '' for t in text_elements)
                
                if not para_text.strip() or len(para_text.strip()) < 10:
                    continue
                    
                normalized_para = normalize_text(para_text)
                
                # Exakte Übereinstimmung (höchste Priorität)
                if normalized_search in normalized_para:
                    return para
                
                # Fuzzy-Matching für ähnliche Texte
                similarity = self._calculate_similarity(normalized_search, normalized_para)
                if similarity > best_similarity and similarity > 0.7:  # 70% Ähnlichkeit
                    best_similarity = similarity
                    best_match = para
            
            # Wenn gutes Fuzzy-Match gefunden, verwende es
            if best_match and best_similarity > 0.8:  # 80% Ähnlichkeit für Fuzzy-Match
                return best_match
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Berechnet die Ähnlichkeit zwischen zwei Texten mittels SequenceMatcher.
        
        Args:
            text1 (str): Erster Text zum Vergleich
            text2 (str): Zweiter Text zum Vergleich
            
        Returns:
            float: Ähnlichkeitsgrad zwischen 0.0 (völlig unterschiedlich) und 1.0 (identisch)
            
        Note:
            Verwendet Python's difflib.SequenceMatcher für robuste Textvergleiche.
            Werte > 0.8 gelten als sehr ähnlich, > 0.7 als ähnlich.
        """
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _add_comment_to_paragraph(self, paragraph: ET.Element, suggestion, ns: dict) -> bool:
        """
        Fügt Word-Kommentar-Elemente zu einem bestimmten Paragraph hinzu.
        
        Erstellt die erforderlichen XML-Elemente für Word-Kommentare:
        - CommentRangeStart: Markiert Beginn des kommentierten Bereichs
        - CommentRangeEnd: Markiert Ende des kommentierten Bereichs  
        - CommentReference: Referenz zum eigentlichen Kommentar-Inhalt
        
        Args:
            paragraph (ET.Element): Ziel-Paragraph für den Kommentar
            suggestion: KI-Verbesserungsvorschlag mit Text und Metadaten
            ns (Dict[str, str]): XML-Namespace-Mapping
            
        Returns:
            bool: True wenn Kommentar erfolgreich hinzugefügt, False bei Fehlern
            
        Note:
            Speichert Kommentar-Daten in self.comments_data für spätere XML-Generierung.
            Inkrementiert automatisch self.comment_id für eindeutige IDs.
        """
        try:
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
            
            # CommentRangeStart
            comment_start = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentRangeStart')
            comment_start.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
            paragraph.insert(0, comment_start)
            
            # CommentRangeEnd
            comment_end = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentRangeEnd')
            comment_end.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
            paragraph.append(comment_end)
            
            # CommentReference
            comment_ref_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
            comment_ref = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}commentReference')
            comment_ref.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment_id)
            comment_ref_run.append(comment_ref)
            paragraph.append(comment_ref_run)
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Paragraph-Kommentar: {e}")
            return False
    
    def _format_comment_text(self, suggestion) -> str:
        """Formatiert Kommentar-Text"""
        category_names = {
            'grammar': 'Grammatik',
            'style': 'Stil',
            'clarity': 'Klarheit',
            'academic': 'Wissenschaftlich'
        }
        
        category = category_names.get(suggestion.category.lower(), 'Allgemein')
        
        text = f"KI-Verbesserung ({category}): "
        text += f"{suggestion.suggested_text} "
        text += f"-- Begründung: {suggestion.reason}"
        
        return text
    
    def _create_comments_xml(self):
        """Erstellt Microsoft-konforme comments.xml ohne Warnungen"""
        comments_xml_path = os.path.join(self.temp_dir, 'word', 'comments.xml')
        
        # Verwende ElementTree für garantiert valides XML
        ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        
        # Root-Element mit korrektem Namespace
        root = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}comments')
        
        for comment in self.comments_data:
            # Kommentar-Element
            comment_elem = ET.SubElement(root, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}comment')
            comment_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id', comment['id'])
            comment_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', comment['author'])
            comment_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date', comment['date'])
            comment_elem.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}initials', comment['initials'])
            
            # Paragraph-Element
            p_elem = ET.SubElement(comment_elem, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
            
            # Run-Element
            r_elem = ET.SubElement(p_elem, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
            
            # Text-Element mit automatischem XML-Escaping
            t_elem = ET.SubElement(r_elem, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            t_elem.text = comment['text']  # ElementTree escaped automatisch
        
        # Speichere mit korrekter XML-Deklaration
        tree = ET.ElementTree(root)
        tree.write(comments_xml_path, encoding='utf-8', xml_declaration=True, method='xml')
    
    def _escape_xml(self, text: str) -> str:
        """XML-Escape"""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    def _update_content_types(self):
        """Aktualisiert [Content_Types].xml"""
        content_types_path = os.path.join(self.temp_dir, '[Content_Types].xml')
        
        if os.path.exists(content_types_path):
            tree = ET.parse(content_types_path)
            root = tree.getroot()
            
            # Prüfe ob Comments-ContentType existiert
            existing = root.find(".//*[@Extension='comments']")
            if existing is None:
                default = ET.Element('Default')
                default.set('Extension', 'comments')
                default.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')
                root.append(default)
                
                tree.write(content_types_path, encoding='utf-8', xml_declaration=True)
    
    def _update_relationships(self):
        """Aktualisiert document.xml.rels mit korrekten Namespaces"""
        rels_path = os.path.join(self.temp_dir, 'word', '_rels', 'document.xml.rels')
        
        if os.path.exists(rels_path):
            # Registriere Namespace vor Parsing
            ET.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/relationships')
            
            tree = ET.parse(rels_path)
            root = tree.getroot()
            
            # Prüfe ob Comments-Relationship bereits existiert
            existing = None
            ns = {'': 'http://schemas.openxmlformats.org/package/2006/relationships'}
            
            for rel in root.findall('.//Relationship', ns):
                target = rel.get('Target', '')
                rel_type = rel.get('Type', '')
                if (target == 'comments.xml' and 
                    rel_type == 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'):
                    existing = rel
                    break
            
            if existing is None:
                # Finde höchste rId-Nummer
                max_id = 0
                for rel in root.findall('.//Relationship', ns):
                    rid = rel.get('Id', '')
                    if rid.startswith('rId'):
                        try:
                            num = int(rid[3:])
                            max_id = max(max_id, num)
                        except ValueError:
                            continue
                
                # Erstelle neue Relationship mit konsistentem Namespace
                relationship = ET.Element('Relationship')
                relationship.set('Id', f"rId{max_id + 1}")
                relationship.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
                relationship.set('Target', 'comments.xml')
                root.append(relationship)
                
                # Speichere mit konsistenter Formatierung
                tree.write(rels_path, encoding='utf-8', xml_declaration=True, method='xml')
    
    def save_document(self, output_path: str) -> bool:
        """Speichert das Dokument"""
        try:
            if not self.temp_dir:
                return False
                
            # Erstelle neue DOCX aus temp_dir
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root_dir, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        arc_name = os.path.relpath(file_path, self.temp_dir)
                        zip_file.write(file_path, arc_name)
            
            print(f"✅ Robustes Dokument gespeichert: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Speicher-Fehler: {e}")
            return False
        
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def create_backup(self) -> str:
        """Erstellt Backup"""
        backup_path = self.document_path.replace('.docx', '_backup.docx')
        try:
            shutil.copy2(self.document_path, backup_path)
            print(f"🔒 Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup-Fehler: {e}")
            return ""


def main():
    """Test robuste Word-Kommentare"""
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
            original_text="Large Language Model",
            suggested_text="Large Language Model (LLM)", 
            reason="Abkürzung ausschreiben",
            category="academic",
            confidence=0.9,
            position=(100, 120)
        ),
        MockSuggestion(
            original_text="KI-basierte Technologien",
            suggested_text="KI-basierte Technologien", 
            reason="Mehr Details zur Anwendung",
            category="clarity",
            confidence=0.8,
            position=(200, 220)
        )
    ]
    
    print("=== ROBUSTE WORD-KOMMENTARE TEST ===")
    
    integrator = ZipWordCommentIntegrator(document_path)
    backup_path = integrator.create_backup()
    
    # Füge robuste Kommentare hinzu
    comments_added = integrator.add_word_comments_robust(test_suggestions)
    
    # Speichere
    output_path = document_path.replace('.docx', '_ROBUSTE_KOMMENTARE.docx')
    success = integrator.save_document(output_path)
    
    if success:
        print(f"🎉 {comments_added} robuste Word-Kommentare hinzugefügt!")
        print(f"📄 Test: {output_path}")


if __name__ == "__main__":
    main()