#!/usr/bin/env python3
"""
Bachelorarbeit Korrekturtool mit ECHTEN Word-Kommentaren
Erstellt echte Word-Markup-Kommentare nach OpenXML-Spezifikation
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
from src.integrators.real_word_comments import RealWordCommentIntegrator

# Initialisiere Colorama für farbige Ausgabe
colorama.init()
load_dotenv()


class RealWordCommentKorrekturtool:
    """Korrekturtool mit echten Word-Kommentaren"""
    
    def __init__(self):
        self.parser = None
        self.analyzer = None
        self.chunker = None
        self.integrator = None
        
    def process_document(self, document_path: str, output_path: str = None) -> bool:
        """Verarbeitet ein Word-Dokument mit echten Word-Kommentaren"""
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
            
            # 4. Echte Word-Kommentar-Integration
            print(f"{Fore.BLUE}💬 Erstelle echte Word-Kommentare...{Style.RESET_ALL}")
            
            self.integrator = RealWordCommentIntegrator(document_path)
            
            # Erstelle Backup
            backup_path = self.integrator.create_backup()
            
            # Füge echte Word-Kommentare hinzu
            comments_added = self.integrator.add_real_word_comments(all_suggestions)
            
            # 5. Speichern
            if not output_path:
                output_path = document_path.replace('.docx', '_MIT_WORD_KOMMENTAREN.docx')
            
            success = self.integrator.save_document(output_path)
            
            if success:
                print(f"{Fore.GREEN}🎉 Erfolgreich abgeschlossen!{Style.RESET_ALL}")
                print(f"   📄 Ausgabedatei: {output_path}")
                print(f"   💬 Echte Word-Kommentare hinzugefügt: {comments_added}")
                print(f"   🔒 Backup erstellt: {backup_path}")
                print(f"")
                print(f"   {Fore.CYAN}💡 So sehen Sie die Kommentare in Microsoft Word:{Style.RESET_ALL}")
                print(f"      1. Öffnen Sie die Datei in Microsoft Word")
                print(f"      2. Gehen Sie zum Menü 'Überprüfen'")
                print(f"      3. Klicken Sie auf 'Kommentare anzeigen'")
                print(f"      4. Die KI-Kommentare erscheinen als Sprechblasen am Rand")
                
                # Zeige Statistik nach Kategorien
                self._show_comment_statistics(all_suggestions)
                
                return True
            else:
                print(f"{Fore.RED}❌ Fehler beim Speichern{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Kritischer Fehler: {e}{Style.RESET_ALL}")
            return False
    
    def _show_comment_statistics(self, suggestions):
        """Zeigt Kommentar-Statistiken nach Kategorien"""
        if not suggestions:
            return
            
        print(f"\n{Fore.CYAN}📊 Kommentar-Statistiken:{Style.RESET_ALL}")
        
        # Zähle nach Kategorien
        categories = {}
        for suggestion in suggestions:
            cat = suggestion.category.lower()
            categories[cat] = categories.get(cat, 0) + 1
        
        category_icons = {
            'grammar': '📝 Grammatik',
            'style': '✨ Stil',
            'clarity': '💡 Klarheit', 
            'academic': '🎓 Wissenschaft'
        }
        
        for category, count in categories.items():
            icon = category_icons.get(category, f'📋 {category.title()}')
            print(f"   {icon}: {count} Kommentare")
        
        print(f"\n{Fore.YELLOW}⚡ Tipps für die Nutzung:{Style.RESET_ALL}")
        print(f"   • Kommentare können einzeln bearbeitet oder gelöscht werden")
        print(f"   • Rechtsklick auf Kommentar für weitere Optionen")
        print(f"   • 'Alle Kommentare anzeigen/ausblenden' im Überprüfen-Menü")


def main():
    parser = argparse.ArgumentParser(
        description='Bachelorarbeit-Korrekturtool mit ECHTEN Word-Kommentaren',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main_real_word_comments.py meine_arbeit.docx
  python main_real_word_comments.py meine_arbeit.docx --output final_arbeit.docx
  
Funktionen:
  ✅ Erstellt echte Word-Kommentare (Markup-Funktion)
  ✅ Kommentare erscheinen als Sprechblasen am Rand
  ✅ Vollständig kompatibel mit Microsoft Word
  ✅ Professioneller Workflow wie bei Lektorat
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
    print("=" * 75)
    print("  🎓 BACHELORARBEIT KORREKTURTOOL - ECHTE WORD-KOMMENTARE")
    print("  KI-basierte Textkorrektur mit professionellen Word-Kommentaren")
    print("=" * 75)
    print(f"{Style.RESET_ALL}")
    
    # Hauptverarbeitung
    tool = RealWordCommentKorrekturtool()
    success = tool.process_document(args.document, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()