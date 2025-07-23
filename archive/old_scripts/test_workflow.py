#!/usr/bin/env python3
"""
Test-Skript für den vollständigen Workflow ohne API-Abhängigkeit
"""

import os
from pathlib import Path
from src.parsers.docx_parser import DocxParser
from src.utils.chunking import IntelligentChunker
from src.integrators.comment_integrator import CommentIntegrator
from dataclasses import dataclass
from typing import Tuple


@dataclass
class MockSuggestion:
    """Mock-Suggestion für Tests ohne API"""
    original_text: str
    suggested_text: str
    reason: str
    category: str
    confidence: float
    position: Tuple[int, int]


def create_mock_suggestions() -> list:
    """Erstellt Mock-Verbesserungsvorschläge für Tests"""
    return [
        MockSuggestion(
            original_text="Dies ist ein Testdokument",
            suggested_text="Dies ist ein umfassendes Testdokument", 
            reason="Präzisere Beschreibung durch Adjektiv",
            category="style",
            confidence=0.8,
            position=(45, 69)
        ),
        MockSuggestion(
            original_text="verschiedene Textelemente",
            suggested_text="diverse Textelemente",
            reason="Variationsreicherer Wortschatz",
            category="style", 
            confidence=0.7,
            position=(100, 125)
        ),
        MockSuggestion(
            original_text="können auftreten",
            suggested_text="können entstehen",
            reason="Präzisere Verbwahl im wissenschaftlichen Kontext",
            category="academic",
            confidence=0.9,
            position=(400, 415)
        )
    ]


def test_complete_workflow():
    """Testet den kompletten Workflow mit Mock-Daten"""
    print("=== VOLLSTÄNDIGER WORKFLOW-TEST ===\n")
    
    document_path = "data/test_document.docx"
    
    if not Path(document_path).exists():
        print(f"❌ Test-Dokument nicht gefunden: {document_path}")
        return False
    
    try:
        # 1. Dokument parsen
        print("1️⃣  Dokument-Parsing...")
        parser = DocxParser(document_path)
        chunks = parser.parse()
        print(f"   ✓ {len(chunks)} Abschnitte geparst")
        print(f"   ✓ {len(parser.full_text)} Zeichen extrahiert")
        
        # 2. Chunking
        print("\n2️⃣  Intelligente Chunking...")
        chunker = IntelligentChunker()
        chunked_groups = chunker.chunk_by_paragraphs(parser.full_text)
        stats = chunker.get_chunk_statistics(chunked_groups)
        print(f"   ✓ {stats['total_chunks']} Chunks erstellt")
        print(f"   ✓ Durchschnitt: {stats['avg_tokens_per_chunk']:.1f} Tokens pro Chunk")
        
        # 3. Mock-KI-Analyse
        print("\n3️⃣  Mock-KI-Analyse...")
        mock_suggestions = create_mock_suggestions()
        print(f"   ✓ {len(mock_suggestions)} Mock-Verbesserungen erstellt")
        
        # Zeige Beispiel-Suggestions
        for i, suggestion in enumerate(mock_suggestions):
            print(f"     {i+1}. {suggestion.category}: {suggestion.reason}")
        
        # 4. Kommentar-Integration
        print("\n4️⃣  Kommentar-Integration...")
        integrator = CommentIntegrator(document_path)
        
        # Backup erstellen
        backup_path = integrator.create_backup()
        
        # Kommentare hinzufügen
        comments_added = integrator.add_bracket_comments(mock_suggestions)
        print(f"   ✓ {comments_added} Kommentare hinzugefügt")
        
        # 5. Speichern
        print("\n5️⃣  Dokument speichern...")
        output_path = document_path.replace('.docx', '_test_output.docx')
        success = integrator.save_commented_document(output_path)
        
        if success:
            print(f"   ✓ Ausgabedokument gespeichert: {output_path}")
            
            # Statistiken
            stats = integrator.get_document_stats()
            print(f"\n📊 Dokument-Statistiken:")
            print(f"   • Absätze: {stats['paragraphs']}")
            print(f"   • Wörter: {stats['words']}")
            print(f"   • Zeichen: {stats['characters']}")
            
            print(f"\n🎉 WORKFLOW-TEST ERFOLGREICH!")
            print(f"   📄 Original: {document_path}")
            print(f"   💾 Backup: {backup_path}")
            print(f"   📝 Output: {output_path}")
            return True
        else:
            print("   ❌ Fehler beim Speichern")
            return False
            
    except Exception as e:
        print(f"❌ Workflow-Test fehlgeschlagen: {e}")
        return False


def test_individual_components():
    """Testet einzelne Komponenten"""
    print("=== KOMPONENTEN-TESTS ===\n")
    
    # Test 1: Parser
    print("🔍 Test: DOCX Parser")
    try:
        parser = DocxParser("data/test_document.docx")
        chunks = parser.parse()
        print(f"   ✓ Parser funktioniert ({len(chunks)} Chunks)")
    except Exception as e:
        print(f"   ❌ Parser-Fehler: {e}")
        return False
    
    # Test 2: Chunker
    print("\n📝 Test: Intelligent Chunker")
    try:
        chunker = IntelligentChunker(max_tokens=500)
        test_text = "Dies ist ein Test. " * 100  # Langer Test-Text
        chunks = chunker.chunk_by_paragraphs(test_text)
        print(f"   ✓ Chunker funktioniert ({len(chunks)} Chunks)")
    except Exception as e:
        print(f"   ❌ Chunker-Fehler: {e}")
        return False
    
    # Test 3: Comment Integrator
    print("\n💬 Test: Comment Integrator")
    try:
        integrator = CommentIntegrator("data/test_document.docx")
        stats = integrator.get_document_stats()
        print(f"   ✓ Integrator funktioniert ({stats['paragraphs']} Absätze)")
    except Exception as e:
        print(f"   ❌ Integrator-Fehler: {e}")
        return False
    
    print("\n✅ Alle Komponenten-Tests bestanden!")
    return True


if __name__ == "__main__":
    print("🧪 STARTE TESTS FÜR BACHELORARBEIT KORREKTURTOOL\n")
    
    # Komponenten-Tests
    components_ok = test_individual_components()
    
    print("\n" + "="*60 + "\n")
    
    # Workflow-Test
    if components_ok:
        workflow_ok = test_complete_workflow()
        
        if workflow_ok:
            print(f"\n🎯 ALLE TESTS BESTANDEN!")
            print("Das Tool ist bereit für den produktiven Einsatz mit OpenAI API Key.")
        else:
            print(f"\n❌ Workflow-Test fehlgeschlagen!")
    else:
        print(f"\n❌ Komponenten-Tests fehlgeschlagen!")
    
    print("\n" + "="*60)