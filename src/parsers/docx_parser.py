"""
Word-Dokument Parser
Extrahiert Text aus DOCX-Dateien unter Beibehaltung der Struktur und Positionsinformationen
"""

from docx import Document
from docx.shared import Inches
from docx.oxml.ns import qn
from typing import List, Dict, Tuple, Optional
import xml.etree.ElementTree as ET


class DocumentChunk:
    """Repräsentiert einen Textabschnitt mit Positionsinformationen"""
    def __init__(self, text: str, start_pos: int, end_pos: int, paragraph_idx: int, element_type: str = "paragraph"):
        self.text = text
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.paragraph_idx = paragraph_idx
        self.element_type = element_type
        self.suggestions = []


class DocxParser:
    """Parser für Word-Dokumente mit Struktur-Erhaltung"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = Document(file_path)
        self.chunks = []
        self.full_text = ""
        self.paragraph_mapping = {}
    
    def parse(self) -> List[DocumentChunk]:
        """Parst das Dokument und erstellt Chunks"""
        chunks = []
        current_pos = 0
        
        for para_idx, paragraph in enumerate(self.document.paragraphs):
            text = paragraph.text.strip()
            
            if not text:
                continue
            
            # Erkenne verschiedene Elementtypen
            element_type = self._identify_element_type(paragraph)
            
            # Erstelle Chunk
            chunk = DocumentChunk(
                text=text,
                start_pos=current_pos,
                end_pos=current_pos + len(text),
                paragraph_idx=para_idx,
                element_type=element_type
            )
            
            chunks.append(chunk)
            self.paragraph_mapping[para_idx] = chunk
            
            current_pos += len(text) + 1  # +1 für Zeilenumbruch
            self.full_text += text + "\n"
        
        self.chunks = chunks
        return chunks
    
    def _identify_element_type(self, paragraph) -> str:
        """Identifiziert den Typ eines Paragraph-Elements"""
        if paragraph.style.name.startswith('Heading'):
            return "heading"
        elif paragraph.style.name.startswith('Caption'):
            return "caption"
        elif self._contains_footnote_reference(paragraph):
            return "footnote"
        else:
            return "paragraph"
    
    def _contains_footnote_reference(self, paragraph) -> bool:
        """Prüft ob Paragraph Fußnoten-Referenzen enthält"""
        try:
            # Vereinfachte Prüfung auf Fußnoten
            for run in paragraph.runs:
                if run.element.xpath('.//w:footnoteReference', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                    return True
        except:
            pass
        return False
    
    def get_chunks_by_size(self, max_tokens: int = 3000) -> List[List[DocumentChunk]]:
        """Gruppiert Chunks nach Token-Größe"""
        grouped_chunks = []
        current_group = []
        current_size = 0
        
        for chunk in self.chunks:
            # Einfache Token-Schätzung (ca. 4 Zeichen pro Token)
            chunk_tokens = len(chunk.text) // 4
            
            if current_size + chunk_tokens > max_tokens and current_group:
                grouped_chunks.append(current_group)
                current_group = [chunk]
                current_size = chunk_tokens
            else:
                current_group.append(chunk)
                current_size += chunk_tokens
        
        if current_group:
            grouped_chunks.append(current_group)
        
        return grouped_chunks
    
    def get_context_for_chunk(self, chunk: DocumentChunk, context_size: int = 200) -> str:
        """Gibt Kontext um einen Chunk zurück"""
        start = max(0, chunk.start_pos - context_size)
        end = min(len(self.full_text), chunk.end_pos + context_size)
        return self.full_text[start:end]
    
    def save_backup(self, backup_path: str) -> None:
        """Erstellt eine Backup-Kopie des Dokuments"""
        self.document.save(backup_path)
        print(f"Backup erstellt: {backup_path}")


def main():
    """Test-Funktion"""
    import sys
    if len(sys.argv) != 2:
        print("Usage: python docx_parser.py <document.docx>")
        return
    
    parser = DocxParser(sys.argv[1])
    chunks = parser.parse()
    
    print(f"Dokument geladen: {len(chunks)} Abschnitte")
    print(f"Gesamttext-Länge: {len(parser.full_text)} Zeichen")
    
    # Zeige erste paar Chunks
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1} ({chunk.element_type}):")
        print(f"Position: {chunk.start_pos}-{chunk.end_pos}")
        print(f"Text: {chunk.text[:100]}...")


if __name__ == "__main__":
    main()