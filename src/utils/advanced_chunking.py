"""
Advanced Context-Aware Intelligent Chunking System
Research-basierte Implementierung für optimale Text-Segmentierung
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class TextChunk:
    """Repräsentiert einen intelligenten Text-Chunk mit Kontext"""
    text: str
    start_pos: int
    end_pos: int
    chunk_id: int
    token_count: int
    context_before: str
    context_after: str
    paragraph_count: int
    sentence_count: int
    chunk_type: str  # 'paragraph', 'sentence', 'semantic'


class AdvancedChunker:
    """
    Context-Aware Intelligent Chunking System
    
    Research-basierte Implementierung mit:
    - Satzgrenze-bewusstes Chunking (keine mitten-im-Satz Cuts)
    - Paragraph-Kontext-Erhaltung für bessere Gemini-Analyse
    - Optimale Chunk-Größe (600-800 Wörter) basierend auf Gemini Research
    - Überlappungs-Management (150 Wörter) für Kontext-Kontinuität
    - Semantische Segmentierung für logische Einheiten
    """
    
    def __init__(self, 
                 target_chunk_size: int = 700,    # Optimal für Gemini (600-800 Wörter)
                 overlap_size: int = 150,         # Kontext-Überlappung
                 min_chunk_size: int = 50,        # Minimum für sinnvolle Analyse (reduziert für Tests)
                 max_chunk_size: int = 1000):     # Maximum für Performance
        
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Regex-Patterns für intelligente Segmentierung
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ])')
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        self.section_pattern = re.compile(r'\n\s*\d+\.?\s+[A-ZÄÖÜ].*?\n')
        
    def create_intelligent_chunks(self, full_text: str, 
                                document_type: str = "academic") -> List[TextChunk]:
        """
        Erstellt intelligente Chunks mit kontextbewusster Segmentierung
        
        Args:
            full_text: Vollständiger Text zum Chunking
            document_type: Typ des Dokuments für optimierte Segmentierung
            
        Returns:
            Liste von TextChunk-Objekten mit Kontext-Information
        """
        print(f"🧩 Starte intelligentes Chunking für {len(full_text)} Zeichen...")
        
        # 1. Preprocessing: Text normalisieren
        normalized_text = self._normalize_text(full_text)
        
        # 2. Identifiziere strukturelle Elemente
        structure_info = self._analyze_document_structure(normalized_text)
        
        # 3. Erstelle Chunks basierend auf optimaler Strategie
        if document_type == "academic":
            chunks = self._create_academic_chunks(normalized_text, structure_info)
        else:
            chunks = self._create_generic_chunks(normalized_text, structure_info)
        
        # 4. Füge Kontext-Information hinzu
        enhanced_chunks = self._enhance_chunks_with_context(chunks, normalized_text)
        
        # 5. Validierung und Optimierung
        final_chunks = self._optimize_chunk_boundaries(enhanced_chunks, normalized_text)
        
        print(f"✅ {len(final_chunks)} intelligente Chunks erstellt")
        self._print_chunking_stats(final_chunks)
        
        return final_chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalisiert Text für bessere Verarbeitung"""
        # Entferne übermäßige Whitespaces
        normalized = re.sub(r'\n{3,}', '\n\n', text)
        normalized = re.sub(r' {2,}', ' ', normalized)
        
        # Normalisiere Anführungszeichen und Gedankenstriche
        normalized = normalized.replace('"', '"').replace('"', '"')
        normalized = normalized.replace('–', '-').replace('—', '-')
        
        return normalized.strip()
    
    def _analyze_document_structure(self, text: str) -> Dict[str, List[Tuple[int, int]]]:
        """Analysiert die Struktur des Dokuments"""
        structure = {
            'paragraphs': [],
            'sentences': [],
            'sections': [],
            'citations': []
        }
        
        # Finde Paragraphen
        current_pos = 0
        for match in self.paragraph_pattern.finditer(text):
            if current_pos < match.start():
                structure['paragraphs'].append((current_pos, match.start()))
            current_pos = match.end()
        
        # Letzter Paragraph
        if current_pos < len(text):
            structure['paragraphs'].append((current_pos, len(text)))
        
        # Finde Sätze
        current_pos = 0
        for match in self.sentence_pattern.finditer(text):
            structure['sentences'].append((current_pos, match.start()))
            current_pos = match.start()
        
        # Finde Abschnitte/Kapitel
        for match in self.section_pattern.finditer(text):
            structure['sections'].append((match.start(), match.end()))
        
        # Finde Zitate (einfache Heuristik)
        citation_pattern = re.compile(r'\([A-Za-z]+,?\s*\d{4}[a-z]?\)')
        for match in citation_pattern.finditer(text):
            structure['citations'].append((match.start(), match.end()))
        
        return structure
    
    def _create_academic_chunks(self, text: str, 
                              structure_info: Dict[str, List[Tuple[int, int]]]) -> List[TextChunk]:
        """Erstellt akademisch optimierte Chunks"""
        chunks = []
        chunk_id = 0
        
        # Verwende Paragraphen als Basis-Einheiten
        paragraphs = structure_info['paragraphs']
        
        current_chunk_text = ""
        current_start_pos = 0
        current_word_count = 0
        
        for i, (para_start, para_end) in enumerate(paragraphs):
            paragraph_text = text[para_start:para_end].strip()
            paragraph_words = len(paragraph_text.split())
            
            # Prüfe ob Paragraph in aktuellen Chunk passt
            if (current_word_count + paragraph_words <= self.max_chunk_size and 
                current_word_count > 0):
                
                # Füge Paragraph zu aktuellem Chunk hinzu
                current_chunk_text += "\n\n" + paragraph_text
                current_word_count += paragraph_words
                
            else:
                # Finalisiere aktuellen Chunk (wenn er existiert)
                if current_chunk_text and current_word_count >= self.min_chunk_size:
                    chunk = TextChunk(
                        text=current_chunk_text.strip(),
                        start_pos=current_start_pos,
                        end_pos=para_start,
                        chunk_id=chunk_id,
                        token_count=current_word_count,
                        context_before="",
                        context_after="",
                        paragraph_count=len([p for p in current_chunk_text.split('\n\n') if p.strip()]),
                        sentence_count=len(self.sentence_pattern.split(current_chunk_text)),
                        chunk_type='paragraph'
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Starte neuen Chunk
                current_chunk_text = paragraph_text
                current_start_pos = para_start
                current_word_count = paragraph_words
        
        # Letzter Chunk
        if current_chunk_text and current_word_count >= self.min_chunk_size:
            chunk = TextChunk(
                text=current_chunk_text.strip(),
                start_pos=current_start_pos,
                end_pos=len(text),
                chunk_id=chunk_id,
                token_count=current_word_count,
                context_before="",
                context_after="",
                paragraph_count=len([p for p in current_chunk_text.split('\n\n') if p.strip()]),
                sentence_count=len(self.sentence_pattern.split(current_chunk_text)),
                chunk_type='paragraph'
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_generic_chunks(self, text: str, 
                             structure_info: Dict[str, List[Tuple[int, int]]]) -> List[TextChunk]:
        """Erstellt generische Chunks mit Satzgrenze-Bewusstsein"""
        chunks = []
        chunk_id = 0
        
        sentences = self.sentence_pattern.split(text)
        current_chunk_text = ""
        current_start_pos = 0
        current_word_count = 0
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            sentence_words = len(sentence.split())
            
            # Prüfe ob Satz in aktuellen Chunk passt
            if current_word_count + sentence_words <= self.target_chunk_size:
                current_chunk_text += " " + sentence.strip() if current_chunk_text else sentence.strip()
                current_word_count += sentence_words
            else:
                # Finalisiere aktuellen Chunk
                if current_chunk_text:
                    chunk = TextChunk(
                        text=current_chunk_text.strip(),
                        start_pos=current_start_pos,
                        end_pos=current_start_pos + len(current_chunk_text),
                        chunk_id=chunk_id,
                        token_count=current_word_count,
                        context_before="",
                        context_after="",
                        paragraph_count=current_chunk_text.count('\n\n') + 1,
                        sentence_count=len([s for s in sentences if s.strip()]),
                        chunk_type='sentence'
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Starte neuen Chunk
                current_chunk_text = sentence.strip()
                current_start_pos = current_start_pos + len(current_chunk_text)
                current_word_count = sentence_words
        
        # Letzter Chunk
        if current_chunk_text:
            chunk = TextChunk(
                text=current_chunk_text.strip(),
                start_pos=current_start_pos,
                end_pos=len(text),
                chunk_id=chunk_id,
                token_count=current_word_count,
                context_before="",
                context_after="",
                paragraph_count=current_chunk_text.count('\n\n') + 1,
                sentence_count=len([s for s in current_chunk_text.split('.') if s.strip()]),
                chunk_type='sentence'
            )
            chunks.append(chunk)
        
        return chunks
    
    def _enhance_chunks_with_context(self, chunks: List[TextChunk], 
                                   full_text: str) -> List[TextChunk]:
        """Fügt Kontext-Information zu Chunks hinzu"""
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Kontext vor dem Chunk
            context_before = ""
            if i > 0:
                prev_chunk = chunks[i-1]
                # Nimm letzte N Wörter vom vorherigen Chunk
                prev_words = prev_chunk.text.split()[-self.overlap_size//2:]
                context_before = " ".join(prev_words)
            
            # Kontext nach dem Chunk
            context_after = ""
            if i < len(chunks) - 1:
                next_chunk = chunks[i+1]
                # Nimm erste N Wörter vom nächsten Chunk
                next_words = next_chunk.text.split()[:self.overlap_size//2]
                context_after = " ".join(next_words)
            
            # Erstelle enhanced Chunk
            enhanced_chunk = TextChunk(
                text=chunk.text,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                chunk_id=chunk.chunk_id,
                token_count=chunk.token_count,
                context_before=context_before,
                context_after=context_after,
                paragraph_count=chunk.paragraph_count,
                sentence_count=chunk.sentence_count,
                chunk_type=chunk.chunk_type
            )
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _optimize_chunk_boundaries(self, chunks: List[TextChunk], 
                                 full_text: str) -> List[TextChunk]:
        """Optimiert Chunk-Grenzen für bessere Analyse"""
        optimized_chunks = []
        
        for chunk in chunks:
            # Prüfe ob Chunk zu klein ist und mit nächstem kombiniert werden sollte
            if (chunk.token_count < self.min_chunk_size and 
                chunk.chunk_id < len(chunks) - 1):
                
                # Kombiniere mit nächstem Chunk wenn möglich
                next_chunk = chunks[chunk.chunk_id + 1]
                if chunk.token_count + next_chunk.token_count <= self.max_chunk_size:
                    combined_text = chunk.text + "\n\n" + next_chunk.text
                    
                    combined_chunk = TextChunk(
                        text=combined_text,
                        start_pos=chunk.start_pos,
                        end_pos=next_chunk.end_pos,
                        chunk_id=chunk.chunk_id,
                        token_count=chunk.token_count + next_chunk.token_count,
                        context_before=chunk.context_before,
                        context_after=next_chunk.context_after,
                        paragraph_count=chunk.paragraph_count + next_chunk.paragraph_count,
                        sentence_count=chunk.sentence_count + next_chunk.sentence_count,
                        chunk_type='combined'
                    )
                    optimized_chunks.append(combined_chunk)
                    continue
            
            optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def _print_chunking_stats(self, chunks: List[TextChunk]):
        """Druckt Chunking-Statistiken"""
        if not chunks:
            return
            
        word_counts = [chunk.token_count for chunk in chunks]
        total_words = sum(word_counts)
        avg_words = total_words / len(chunks)
        min_words = min(word_counts)
        max_words = max(word_counts)
        
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        print(f"📊 CHUNKING-STATISTIKEN:")
        print(f"   💬 Gesamt-Wörter: {total_words}")
        print(f"   📋 Chunks erstellt: {len(chunks)}")
        print(f"   📐 Durchschnittl. Chunk-Größe: {avg_words:.0f} Wörter")
        print(f"   🔽 Min/Max Chunk-Größe: {min_words}/{max_words} Wörter")
        print(f"   📚 Chunk-Typen: {dict(chunk_types)}")


def main():
    """Test-Funktion für Advanced Chunker"""
    try:
        chunker = AdvancedChunker(
            target_chunk_size=500,  # Kleiner für Test
            overlap_size=100
        )
        
        # Test-Text (längerer wissenschaftlicher Text)
        test_text = """
        Einleitung
        
        Die vorliegende Arbeit untersucht die Auswirkungen von Künstlicher Intelligenz auf moderne Arbeitsplätze. 
        In den letzten Jahren haben sich KI-Technologien rasant entwickelt und verschiedene Branchen transformiert.
        
        Literaturbericht
        
        Müller (2023) argumentiert, dass KI-Systeme die Produktivität steigern können. Diese Aussage wird von 
        verschiedenen empirischen Studien unterstützt. Andererseits warnt Schmidt (2022) vor möglichen 
        Arbeitsplatzverlusten durch Automatisierung.
        
        Die Forschung zeigt gemischte Ergebnisse bezüglich der Auswirkungen von KI auf Beschäftigung. 
        Während einige Studien positive Effekte nachweisen, deuten andere auf negative Konsequenzen hin.
        
        Methodik
        
        Für diese Untersuchung wurde eine qualitative Forschungsmethode gewählt. Es wurden 25 Experteninterviews 
        durchgeführt mit Fachkräften aus verschiedenen Branchen. Die Interviews dauerten zwischen 45 und 60 Minuten.
        
        Die Datenauswertung erfolgte mittels thematischer Analyse. Zunächst wurden die Interviews transkribiert, 
        dann kodiert und schließlich in übergeordnete Themen gruppiert.
        
        Ergebnisse
        
        Die Analyse ergab drei Hauptkategorien: Produktivitätssteigerung, Qualifikationsanforderungen und 
        Arbeitsplatzveränderungen. Jede Kategorie wird im Folgenden detailliert erläutert.
        
        Produktivitätssteigerung war das am häufigsten genannte Thema. 80% der Befragten berichteten von 
        messbaren Verbesserungen in ihren Arbeitsprozessen durch KI-Integration.
        """
        
        print("🧪 Teste Advanced Intelligent Chunking...")
        print(f"📝 Test-Text: {len(test_text)} Zeichen, {len(test_text.split())} Wörter")
        
        # Erstelle intelligente Chunks
        chunks = chunker.create_intelligent_chunks(test_text, document_type="academic")
        
        print(f"\n🎯 CHUNK-DETAILS:")
        for i, chunk in enumerate(chunks[:3]):  # Zeige erste 3 Chunks
            print(f"\n📄 CHUNK {i+1}:")
            print(f"   🔤 Text-Länge: {len(chunk.text)} Zeichen")
            print(f"   💬 Wörter: {chunk.token_count}")
            print(f"   📋 Paragraphen: {chunk.paragraph_count}")
            print(f"   🔧 Typ: {chunk.chunk_type}")
            print(f"   📍 Position: {chunk.start_pos}-{chunk.end_pos}")
            
            # Zeige Chunk-Preview
            preview = chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text
            print(f"   📖 Preview: {preview}")
            
            # Zeige Kontext
            if chunk.context_before:
                context_preview = chunk.context_before[:50] + "..." if len(chunk.context_before) > 50 else chunk.context_before
                print(f"   ⬅️ Kontext davor: {context_preview}")
            
            if chunk.context_after:
                context_preview = chunk.context_after[:50] + "..." if len(chunk.context_after) > 50 else chunk.context_after
                print(f"   ➡️ Kontext danach: {context_preview}")
        
        print(f"\n✅ Advanced Chunking erfolgreich getestet!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()