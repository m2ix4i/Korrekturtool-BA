#!/usr/bin/env python3
"""
Verbessertes Bachelorarbeit Korrekturtool mit deutlich sichtbaren Kommentaren
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Lade Module
from src.parsers.docx_parser import DocxParser
from src.analyzers.gemini_analyzer import GeminiAnalyzer
from src.utils.chunking import IntelligentChunker
from src.integrators.enhanced_comment_integrator import EnhancedCommentIntegrator

# Initialisiere Colorama für farbige Ausgabe
colorama.init()
load_dotenv()


class EnhancedBachelorarbeitKorrekturtool:
    """Verbesserte Hauptklasse mit sichtbaren Kommentaren"""
    
    def __init__(self):
        self.parser = None
        self.analyzer = None
        self.chunker = None
        self.integrator = None
        
    def process_document(self, document_path: str, output_path: str = None) -> bool:
        """Verarbeitet ein Word-Dokument mit verbesserter Kommentar-Integration"""
        try:
            print(f"{Fore.BLUE}🔍 Lade Dokument: {document_path}{Style.RESET_ALL}")
            
            # 1. Dokument parsen
            self.parser = DocxParser(document_path)
            chunks = self.parser.parse()
            
            print(f"{Fore.GREEN}✓ Dokument geparst: {len(chunks)} Abschnitte{Style.RESET_ALL}")
            
            # 2. Intelligente Chunking für große Dokumente
            self.chunker = IntelligentChunker()
            chunked_groups = self.chunker.chunk_by_paragraphs(self.parser.full_text)
            
            print(f"{Fore.GREEN}✓ Text aufgeteilt: {len(chunked_groups)} Analyse-Chunks{Style.RESET_ALL}")
            
            # 3. KI-Analyse
            print(f"{Fore.YELLOW}🤖 Starte KI-Analyse...{Style.RESET_ALL}")
            
            if not os.getenv('GOOGLE_API_KEY'):
                print(f"{Fore.RED}❌ Fehler: GOOGLE_API_KEY nicht gesetzt. Bitte .env-Datei erstellen.{Style.RESET_ALL}")
                return False
            
            self.analyzer = GeminiAnalyzer()
            all_suggestions = []
            
            # Schätze Kosten
            total_tokens = sum(chunk.token_count for chunk in chunked_groups)
            estimated_cost = self.analyzer.get_cost_estimate("x" * total_tokens)
            print(f"{Fore.CYAN}💰 Geschätzte Kosten: ${estimated_cost:.4f}{Style.RESET_ALL}")
            
            # Analysiere jeden Chunk
            for i, chunk in enumerate(tqdm(chunked_groups, desc="Analysiere")):
                try:
                    suggestions = self.analyzer.analyze_text(chunk.text)
                    
                    # Korrigiere Positionen basierend auf Chunk-Offset
                    for suggestion in suggestions:
                        start, end = suggestion.position
                        suggestion.position = (
                            start + chunk.start_pos,
                            end + chunk.start_pos
                        )
                    
                    all_suggestions.extend(suggestions)
                    
                except Exception as e:
                    print(f"{Fore.RED}⚠️  Fehler bei Chunk {i+1}: {e}{Style.RESET_ALL}")
                    continue
            
            print(f"{Fore.GREEN}✓ KI-Analyse abgeschlossen: {len(all_suggestions)} Verbesserungsvorschläge{Style.RESET_ALL}")
            
            if not all_suggestions:
                print(f"{Fore.YELLOW}ℹ️  Keine Verbesserungsvorschläge gefunden.{Style.RESET_ALL}")
                return True
            
            # 4. Verbesserte Kommentar-Integration
            print(f"{Fore.BLUE}📝 Integriere sichtbare Kommentare...{Style.RESET_ALL}")
            
            self.integrator = EnhancedCommentIntegrator(document_path)
            
            # Erstelle Backup
            backup_path = self.integrator.create_backup()
            
            # Füge farbige Kommentare hinzu
            comments_added = self.integrator.add_highlighted_comments(all_suggestions)
            
            # Füge Zusammenfassung hinzu
            self.integrator.add_summary_at_end(len(all_suggestions))
            
            # 5. Speichern
            if not output_path:
                output_path = document_path.replace('.docx', '_KORRIGIERT.docx')
            
            success = self.integrator.save_document(output_path)
            
            if success:
                print(f"{Fore.GREEN}🎉 Erfolgreich abgeschlossen!{Style.RESET_ALL}")
                print(f"   📄 Ausgabedatei: {output_path}")
                print(f"   📋 Sichtbare Kommentare hinzugefügt: {comments_added}")
                print(f"   🔒 Backup erstellt: {backup_path}")
                print(f"   📊 Zusätzliche Zusammenfassung am Dokumentenende")
                
                # Zeige Beispiel-Verbesserungen
                self._show_sample_suggestions(all_suggestions[:5])
                
                return True
            else:
                print(f"{Fore.RED}❌ Fehler beim Speichern{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Kritischer Fehler: {e}{Style.RESET_ALL}")
            return False
    
    def _show_sample_suggestions(self, suggestions):
        """Zeigt Beispiel-Verbesserungen mit Kategorien an"""
        if not suggestions:
            return
            
        print(f"\n{Fore.CYAN}📝 Beispiel-Verbesserungen:{Style.RESET_ALL}")
        
        categories = {'grammar': '🔴', 'style': '🟡', 'clarity': '🟢', 'academic': '🔵'}
        
        for i, suggestion in enumerate(suggestions):
            icon = categories.get(suggestion.category.lower(), '⚪')
            print(f"\n{i+1}. {icon} {suggestion.category.upper()}")
            print(f"   Original: '{suggestion.original_text[:60]}...'")
            print(f"   Vorschlag: '{suggestion.suggested_text[:60]}...'")
            print(f"   Grund: {suggestion.reason}")


def main():
    parser = argparse.ArgumentParser(
        description='Verbessertes Bachelorarbeit-Korrekturtool mit sichtbaren Kommentaren',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main_enhanced.py meine_arbeit.docx
  python main_enhanced.py meine_arbeit.docx --output korrigierte_arbeit.docx
  
Verbesserungen in dieser Version:
  - 🎨 Farbige, deutlich sichtbare Kommentare
  - 📊 Zusammenfassung am Dokumentenende  
  - 🏷️ Kategorien-Icons für bessere Übersicht
  - 🔍 Verbesserte Positionserkennung
        """
    )
    
    parser.add_argument('document', help='Pfad zum Word-Dokument (.docx)')
    parser.add_argument('--output', help='Ausgabepfad (optional)')
    
    args = parser.parse_args()
    
    # Validierungen
    if not Path(args.document).exists():
        print(f"{Fore.RED}❌ Fehler: Dokument '{args.document}' nicht gefunden.{Style.RESET_ALL}")
        sys.exit(1)
    
    if not args.document.lower().endswith('.docx'):
        print(f"{Fore.RED}❌ Fehler: Nur .docx Dateien werden unterstützt.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Banner
    print(f"{Fore.CYAN}")
    print("=" * 70)
    print("  🎓 BACHELORARBEIT KORREKTURTOOL - ENHANCED VERSION")
    print("  KI-basierte Textkorrektur mit sichtbaren Kommentaren")
    print("=" * 70)
    print(f"{Style.RESET_ALL}")
    
    # Hauptverarbeitung
    tool = EnhancedBachelorarbeitKorrekturtool()
    success = tool.process_document(args.document, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()