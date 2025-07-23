"""
KI-Analyzer für Textkorrektur
Verwendet OpenAI API um Texte zu analysieren und Verbesserungsvorschläge zu generieren
"""

import openai
import tiktoken
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import time
import json

# Lade Umgebungsvariablen
load_dotenv()

@dataclass
class Suggestion:
    """Repräsentiert einen Verbesserungsvorschlag"""
    original_text: str
    suggested_text: str
    reason: str
    category: str  # grammar, style, clarity, academic
    confidence: float
    position: Tuple[int, int]  # start, end position im Text


class AIAnalyzer:
    """KI-Analyzer für Textkorrektur und -verbesserung"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"  # Kostengünstiges Modell für Textanalyse
        self.encoding = tiktoken.encoding_for_model(self.model)
        
    def count_tokens(self, text: str) -> int:
        """Zählt Tokens für den gegebenen Text"""
        return len(self.encoding.encode(text))
        
    def analyze_text(self, text: str, context: str = "") -> List[Suggestion]:
        """Analysiert einen Textabschnitt und gibt Verbesserungsvorschläge zurück"""
        
        # Erstelle Prompt für wissenschaftliche Textanalyse
        system_prompt = self._get_system_prompt()
        user_prompt = self._create_analysis_prompt(text, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse die Antwort
            suggestions = self._parse_ai_response(response.choices[0].message.content, text)
            return suggestions
            
        except Exception as e:
            print(f"Fehler bei KI-Analyse: {e}")
            return []
    
    def _get_system_prompt(self) -> str:
        """Erstellt den System-Prompt für die KI"""
        return """Du bist ein Experte für wissenschaftliches Schreiben und hilfst bei der Korrektur von Bachelorarbeiten. 

Deine Aufgaben:
1. Finde grammatikalische Fehler
2. Verbessere den wissenschaftlichen Schreibstil
3. Erhöhe die Klarheit und Präzision
4. Achte auf korrekte Terminologie

Antworte ausschließlich im JSON-Format:
{
  "suggestions": [
    {
      "original": "ursprünglicher Text",
      "suggested": "verbesserter Text", 
      "reason": "Begründung der Änderung",
      "category": "grammar|style|clarity|academic",
      "confidence": 0.8,
      "start_pos": 10,
      "end_pos": 25
    }
  ]
}

Gib nur Vorschläge für tatsächliche Verbesserungen. Keine Änderungen bei bereits korrektem Text."""

    def _create_analysis_prompt(self, text: str, context: str = "") -> str:
        """Erstellt den Analyse-Prompt für einen spezifischen Text"""
        prompt = f"Analysiere diesen Text aus einer Bachelorarbeit:\n\n{text}"
        
        if context:
            prompt += f"\n\nKontext:\n{context}"
            
        prompt += "\n\nFinde Verbesserungsmöglichkeiten und gib sie im JSON-Format zurück."
        return prompt
    
    def _parse_ai_response(self, response_text: str, original_text: str) -> List[Suggestion]:
        """Parst die KI-Antwort und erstellt Suggestion-Objekte"""
        suggestions = []
        
        try:
            # Versuche JSON zu parsen
            response_data = json.loads(response_text)
            
            for item in response_data.get('suggestions', []):
                suggestion = Suggestion(
                    original_text=item.get('original', ''),
                    suggested_text=item.get('suggested', ''),
                    reason=item.get('reason', ''),
                    category=item.get('category', 'general'),
                    confidence=float(item.get('confidence', 0.5)),
                    position=(
                        int(item.get('start_pos', 0)),
                        int(item.get('end_pos', 0))
                    )
                )
                
                # Validiere die Suggestion
                if self._validate_suggestion(suggestion, original_text):
                    suggestions.append(suggestion)
                    
        except json.JSONDecodeError:
            print(f"Fehler beim Parsen der KI-Antwort: {response_text[:200]}...")
        except Exception as e:
            print(f"Fehler bei der Suggestion-Erstellung: {e}")
            
        return suggestions
    
    def _validate_suggestion(self, suggestion: Suggestion, original_text: str) -> bool:
        """Validiert eine Suggestion auf Plausibilität"""
        # Prüfe ob die Original-Position im Text existiert
        start, end = suggestion.position
        if start < 0 or end > len(original_text):
            return False
            
        # Prüfe ob der Original-Text tatsächlich an der Position steht
        text_at_position = original_text[start:end]
        if suggestion.original_text.strip() not in text_at_position:
            return False
            
        # Prüfe minimale Qualitätskriterien
        if not suggestion.suggested_text.strip() or not suggestion.reason.strip():
            return False
            
        return True
    
    def analyze_batch(self, texts: List[str], max_concurrent: int = 3) -> List[List[Suggestion]]:
        """Analysiert mehrere Texte in Batches"""
        all_suggestions = []
        
        for i, text in enumerate(texts):
            print(f"Analysiere Chunk {i+1}/{len(texts)}...")
            suggestions = self.analyze_text(text)
            all_suggestions.append(suggestions)
            
            # Rate limiting
            time.sleep(1)
            
        return all_suggestions
    
    def get_cost_estimate(self, text: str) -> float:
        """Schätzt die Kosten für die Analyse eines Texts"""
        tokens = self.count_tokens(text)
        # Geschätzte Kosten für gpt-4o-mini (Input + Output)
        input_cost = tokens * 0.00015 / 1000  # $0.15 per 1K tokens
        output_cost = 500 * 0.0006 / 1000     # ~500 tokens output, $0.60 per 1K tokens
        return input_cost + output_cost


def main():
    """Test-Funktion"""
    analyzer = AIAnalyzer()
    
    test_text = """Dies ist ein Testtext der analysiert werden soll. Der Text enthält möglicherweise 
    grammatikalische Fehler und kann stilistisch verbessert werden. Die Analyse sollte konkrete 
    Vorschläge zur Verbesserung liefern."""
    
    print(f"Analysiere Text mit {analyzer.count_tokens(test_text)} Tokens...")
    print(f"Geschätzte Kosten: ${analyzer.get_cost_estimate(test_text):.4f}")
    
    suggestions = analyzer.analyze_text(test_text)
    
    print(f"\nGefundene Verbesserungen: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions):
        print(f"\n{i+1}. {suggestion.category.upper()}")
        print(f"   Original: '{suggestion.original_text}'")
        print(f"   Vorschlag: '{suggestion.suggested_text}'")
        print(f"   Grund: {suggestion.reason}")
        print(f"   Konfidenz: {suggestion.confidence:.1f}")


if __name__ == "__main__":
    main()