"""
Advanced Gemini AI-Analyzer mit Multi-Pass-Analyse und Research-basierten Optimierungen
Implementiert kategoriespezifische Prompts und intelligentes Context-Management
"""

import google.generativeai as genai
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import time
import json
import re
from rapidfuzz import fuzz

# Lade Umgebungsvariablen
load_dotenv()

@dataclass
class Suggestion:
    """Repräsentiert einen Verbesserungsvorschlag"""
    original_text: str
    suggested_text: str
    reason: str
    category: str  # grammar, style, clarity, academic, structure, references, methodology, formatting
    confidence: float
    position: Tuple[int, int]  # start, end position im Text


class AdvancedGeminiAnalyzer:
    """
    Advanced Gemini AI-Analyzer mit Multi-Pass-Analyse
    
    Research-basierte Implementierung mit:
    - Kategorie-spezifischen Prompts für bessere Analyse-Tiefe
    - Multi-Pass-Analyse für 60-100 Kommentare pro Dokument
    - Context-bewusstes Chunking mit Überlappung
    - Optimierte Prompt-Engineering (5-8 Suggestions pro Pass)
    """
    
    # Kategorie-spezifische Prompts basierend auf Google AI Research
    CATEGORY_PROMPTS = {
        'grammar': {
            'focus': 'Grammatik und Rechtschreibung',
            'instruction': """Analysiere den Text auf grammatikalische und orthographische Fehler:
- Kommafehler und Satzzeichen
- Rechtschreibfehler
- Verb-Subjekt-Kongruenz
- Falsche Wortformen
- Syntaktische Probleme""",
            'examples': 'Beispiel: "Der Studenten haben" → "Die Studenten haben"'
        },
        
        'style': {
            'focus': 'Wissenschaftlicher Schreibstil',
            'instruction': """Verbessere den wissenschaftlichen Schreibstil:
- Nominalstil vs. Verbalstil
- Redundanzen eliminieren
- Präzisere Formulierungen
- Wissenschaftliche Objektivität
- Flüssigere Übergänge""",
            'examples': 'Beispiel: "Es ist zu bemerken, dass" → "Daraus folgt, dass"'
        },
        
        'clarity': {
            'focus': 'Klarheit und Verständlichkeit',
            'instruction': """Erhöhe die Klarheit und Verständlichkeit:
- Unklare Formulierungen präzisieren
- Lange Schachtelsätze aufteilen
- Mehrdeutigkeiten beseitigen
- Konkrete statt abstrakte Begriffe
- Logische Argumentationsfolge""",
            'examples': 'Beispiel: "Das Ding" → "Das untersuchte Phänomen"'
        },
        
        'academic': {
            'focus': 'Wissenschaftliche Terminologie',
            'instruction': """Prüfe wissenschaftliche Ausdrucksweise:
- Fachterminologie korrekt verwenden
- Wissenschaftliche Präzision
- Abkürzungen definieren
- Objektive Formulierungen
- Methodenbeschreibung verbessern""",
            'examples': 'Beispiel: "Die Sache zeigt" → "Die Untersuchung belegt"'
        },
        
        'structure': {
            'focus': 'Struktur und Gliederung',
            'instruction': """Verbessere Struktur und logischen Aufbau:
- Absatzübergänge optimieren
- Logische Reihenfolge
- Überschriften-Hierarchie
- Argumentationsstruktur
- Roter Faden stärken""",
            'examples': 'Beispiel: Fehlende Überleitung → "Darauf aufbauend wird untersucht..."'
        },
        
        'references': {
            'focus': 'Zitierweise und Quellen',
            'instruction': """Optimiere Zitierweise und Quellenangaben:
- Korrekte Zitatformate
- Vollständige Quellenangaben
- Plagiatsvermeidung
- Literaturverzeichnis-Konsistenz
- Primär- vs. Sekundärquellen""",
            'examples': 'Beispiel: Unvollständiges Zitat → (Autor, Jahr, S. XX)'
        },
        
        'methodology': {
            'focus': 'Methodische Beschreibung',
            'instruction': """Verbessere methodische Darstellung:
- Nachvollziehbare Methodenbeschreibung
- Validität und Reliabilität
- Limitationen benennen
- Forschungsdesign präzisieren
- Datenauswertung erklären""",
            'examples': 'Beispiel: "Es wurde untersucht" → "Mittels quantitativer Befragung wurde analysiert"'
        },
        
        'formatting': {
            'focus': 'Formatierung und Darstellung',
            'instruction': """Optimiere Formatierung und Darstellung:
- Tabellen und Abbildungen beschriften
- Konsistente Formatierung
- Nummerierung prüfen
- Layout-Verbesserungen
- Einheitliche Schreibweise""",
            'examples': 'Beispiel: "Abb. 1" → "Abbildung 1: Titel der Abbildung"'
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API Key nicht gefunden. Bitte GOOGLE_API_KEY in .env setzen.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Performance-Tracking
        self.total_api_calls = 0
        self.total_suggestions = 0
        
    def analyze_text_multipass(self, text: str, context: str = "", 
                             categories: Optional[List[str]] = None) -> List[Suggestion]:
        """
        Multi-Pass-Analyse mit kategoriespezifischen Prompts
        
        Args:
            text: Zu analysierender Text
            context: Zusätzlicher Kontext für bessere Analyse
            categories: Liste der zu analysierenden Kategorien (default: alle)
            
        Returns:
            Liste aller Verbesserungsvorschläge aus allen Pässen
        """
        if categories is None:
            categories = ['grammar', 'style', 'clarity', 'academic']  # Hauptkategorien
            
        all_suggestions = []
        seen_suggestions = set()  # Deduplizierung
        
        print(f"🔄 Starte Multi-Pass-Analyse für {len(categories)} Kategorien...")
        
        for category in categories:
            print(f"   📝 Analysiere Kategorie: {category}")
            
            try:
                # Kategorie-spezifischer Prompt
                prompt = self._create_category_prompt(text, category, context)
                
                # API-Call mit Retry-Logic
                suggestions = self._query_gemini_with_retry(prompt, category)
                
                # Deduplizierung basierend auf ähnlichem Text
                unique_suggestions = self._deduplicate_suggestions(suggestions, seen_suggestions)
                
                all_suggestions.extend(unique_suggestions)
                self.total_suggestions += len(unique_suggestions)
                
                print(f"   ✅ {len(unique_suggestions)} neue Verbesserungen gefunden")
                
                # Rate Limiting für Gemini API
                time.sleep(1.0)
                
            except Exception as e:
                print(f"   ⚠️  Fehler bei Kategorie {category}: {e}")
                continue
        
        print(f"🎯 Multi-Pass-Analyse abgeschlossen: {len(all_suggestions)} Verbesserungen total")
        return all_suggestions
    
    def _create_category_prompt(self, text: str, category: str, context: str = "") -> str:
        """Erstellt kategorie-spezifischen Prompt basierend auf Research"""
        
        if category not in self.CATEGORY_PROMPTS:
            category = 'style'  # Fallback
            
        category_config = self.CATEGORY_PROMPTS[category]
        
        prompt = f"""Sie sind ein Experte für wissenschaftliches Schreiben und spezialisiert auf {category_config['focus']}.

IHRE AUFGABE:
{category_config['instruction']}

WICHTIGE REGELN:
- Analysieren Sie PRÄZISE und finden Sie 5-8 konkrete Verbesserungen
- Nur echte Probleme identifizieren, keine bereits korrekten Texte
- Kurze, prägnante Textausschnitte verwenden (max 50 Zeichen)
- Spezifische, umsetzbare Verbesserungsvorschläge

{category_config['examples']}

ANALYSIEREN SIE DIESEN TEXT:
{text}"""

        if context:
            prompt += f"\n\nKONTEXT:\n{context}"

        prompt += f"""

ANTWORTEN SIE AUSSCHLIESSLICH IM JSON-FORMAT:

{{
  "suggestions": [
    {{
      "original": "kurzer ursprünglicher Text (max 50 Zeichen)",
      "suggested": "konkrete Verbesserung",
      "reason": "spezifische Begründung für {category_config['focus']}",
      "category": "{category}",
      "confidence": 0.85
    }}
  ]
}}

ZIEL: 5-8 hochwertige Verbesserungsvorschläge für {category_config['focus']}"""

        return prompt
    
    def _query_gemini_with_retry(self, prompt: str, category: str, max_retries: int = 2) -> List[Suggestion]:
        """Gemini API-Call mit Retry-Logic und verbesserter Fehlerbehandlung"""
        
        for attempt in range(max_retries + 1):
            try:
                self.total_api_calls += 1
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,  # Niedriger für konsistentere Ergebnisse
                        max_output_tokens=2500,  # Mehr Token für 5-8 Suggestions
                        top_p=0.8,
                        top_k=40
                    )
                )
                
                # Verbesserte Response-Parsing
                suggestions = self._parse_gemini_response(response.text, category)
                return suggestions
                
            except Exception as e:
                if attempt < max_retries:
                    print(f"   🔄 Retry {attempt + 1}/{max_retries} für {category}: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"   ❌ Finaler Fehler bei {category}: {e}")
                    return []
    
    def _parse_gemini_response(self, response_text: str, category: str) -> List[Suggestion]:
        """Verbesserte Parsing mit besserer Fehlerbehandlung"""
        suggestions = []
        
        try:
            # Bereinigung der Antwort
            clean_text = self._clean_json_response(response_text)
            
            # JSON-Parsing mit Fallback
            try:
                response_data = json.loads(clean_text)
            except json.JSONDecodeError:
                # Erweiterte JSON-Reparatur
                clean_text = self._repair_json_advanced(clean_text)
                response_data = json.loads(clean_text)
            
            # Verarbeite Suggestions
            for item in response_data.get('suggestions', []):
                suggestion = self._create_suggestion_from_item(item, category)
                if suggestion and self._validate_suggestion_advanced(suggestion):
                    suggestions.append(suggestion)
                    
        except Exception as e:
            print(f"   🐛 JSON-Parsing-Fehler bei {category}: {e}")
            print(f"   📄 Response war: {response_text[:200]}...")
            
        return suggestions
    
    def _clean_json_response(self, response_text: str) -> str:
        """Erweiterte JSON-Bereinigung"""
        clean_text = response_text.strip()
        
        # Entferne Code-Block-Marker
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]
        if clean_text.startswith('```'):
            clean_text = clean_text[3:]
        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]
            
        clean_text = clean_text.strip()
        
        # Suche JSON-Block
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            return json_match.group()
        else:
            raise ValueError("Kein gültiges JSON in Gemini-Antwort gefunden")
    
    def _repair_json_advanced(self, json_text: str) -> str:
        """Erweiterte JSON-Reparatur"""
        # Entferne unvollständige Einträge
        lines = json_text.split('\n')
        clean_lines = []
        brace_count = 0
        in_suggestions = False
        
        for line in lines:
            clean_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            if '"suggestions"' in line:
                in_suggestions = True
                
            # Stoppe bei vollständig geschlossenem JSON mit Suggestions
            if brace_count == 0 and in_suggestions and len(clean_lines) > 3:
                break
        
        return '\n'.join(clean_lines)
    
    def _create_suggestion_from_item(self, item: Dict, category: str) -> Optional[Suggestion]:
        """Erstellt Suggestion-Objekt aus JSON-Item"""
        try:
            return Suggestion(
                original_text=item.get('original', '').strip(),
                suggested_text=item.get('suggested', '').strip(),
                reason=item.get('reason', '').strip(),
                category=category,  # Verwende die Pass-Kategorie
                confidence=float(item.get('confidence', 0.8)),
                position=(0, 0)  # Wird später durch Text-Matching gesetzt
            )
        except Exception as e:
            print(f"   ⚠️  Fehler beim Erstellen der Suggestion: {e}")
            return None
    
    def _validate_suggestion_advanced(self, suggestion: Suggestion) -> bool:
        """Erweiterte Suggestion-Validierung"""
        # Basis-Validierung
        if not suggestion.original_text or not suggestion.suggested_text:
            return False
            
        if not suggestion.reason:
            return False
            
        # Text-Längen-Validierung
        if len(suggestion.original_text) > 200 or len(suggestion.original_text) < 2:
            return False
            
        # Ähnlichkeits-Check (nicht identisch)
        similarity = fuzz.ratio(suggestion.original_text, suggestion.suggested_text)
        if similarity > 95:  # Zu ähnlich = keine echte Verbesserung
            return False
            
        # Konfidenz-Validierung
        if suggestion.confidence < 0.3 or suggestion.confidence > 1.0:
            return False
            
        return True
    
    def _deduplicate_suggestions(self, suggestions: List[Suggestion], 
                               seen_suggestions: Set[str]) -> List[Suggestion]:
        """Entfernt Duplikate basierend auf ähnlichem Original-Text"""
        unique_suggestions = []
        
        for suggestion in suggestions:
            # Erstelle Signature für Duplikat-Check
            signature = f"{suggestion.original_text.lower()[:30]}_{suggestion.category}"
            
            # Prüfe auf sehr ähnliche bereits gesehene Suggestions
            is_duplicate = False
            for seen in seen_suggestions:
                if fuzz.token_sort_ratio(signature, seen) > 85:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_suggestions.append(suggestion)
                seen_suggestions.add(signature)
                
        return unique_suggestions
    
    def get_analysis_stats(self) -> Dict[str, int]:
        """Gibt Analyse-Statistiken zurück"""
        return {
            'total_api_calls': self.total_api_calls,
            'total_suggestions': self.total_suggestions,
            'avg_suggestions_per_call': self.total_suggestions / max(self.total_api_calls, 1)
        }
    
    def count_tokens(self, text: str) -> int:
        """Schätzt Token-Anzahl für Gemini (ca. 4 Zeichen pro Token)"""
        return len(text) // 4
    
    def get_cost_estimate(self, text: str, num_categories: int = 4) -> float:
        """Schätzt die Kosten für Multi-Pass-Analyse"""
        tokens_per_call = self.count_tokens(text) + 500  # Prompt overhead
        total_calls = num_categories
        
        # Gemini-1.5-flash Kosten
        input_cost = (tokens_per_call * total_calls) * 0.000075 / 1000
        output_cost = (2500 * total_calls) * 0.0003 / 1000  # Max output tokens
        
        return input_cost + output_cost


def main():
    """Test-Funktion für Advanced Gemini Analyzer"""
    try:
        analyzer = AdvancedGeminiAnalyzer()
        
        test_text = """Die Studenten haben ihre Arbeiten abgegeben. Das ist gut zu bewerten. 
        Die Ergebnisse sind okay und zeigen, dass die Methode funktioniert hat. 
        Es ist zu bemerken, dass weitere Forschung nötig ist."""
        
        print(f"🧪 Teste Advanced Multi-Pass-Analyse...")
        print(f"📊 Text-Tokens: {analyzer.count_tokens(test_text)}")
        print(f"💰 Geschätzte Kosten: ${analyzer.get_cost_estimate(test_text):.6f}")
        
        # Multi-Pass-Analyse
        suggestions = analyzer.analyze_text_multipass(
            test_text, 
            context="Bachelorarbeit über KI-Methoden",
            categories=['grammar', 'style', 'clarity', 'academic']
        )
        
        print(f"\n🎯 ERGEBNISSE:")
        print(f"   Gefundene Verbesserungen: {len(suggestions)}")
        
        # Zeige Suggestions gruppiert nach Kategorie
        by_category = {}
        for suggestion in suggestions:
            category = suggestion.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(suggestion)
        
        for category, cat_suggestions in by_category.items():
            print(f"\n📝 {category.upper()} ({len(cat_suggestions)} Verbesserungen):")
            for i, suggestion in enumerate(cat_suggestions[:3]):  # Zeige erste 3
                print(f"   {i+1}. '{suggestion.original_text}' → '{suggestion.suggested_text}'")
                print(f"      💡 {suggestion.reason}")
                print(f"      📊 Konfidenz: {suggestion.confidence:.1f}")
        
        # Statistiken
        stats = analyzer.get_analysis_stats()
        print(f"\n📈 STATISTIKEN:")
        print(f"   API-Calls: {stats['total_api_calls']}")
        print(f"   Suggestions total: {stats['total_suggestions']}")
        print(f"   Durchschnitt pro Call: {stats['avg_suggestions_per_call']:.1f}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()