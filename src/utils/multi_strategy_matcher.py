"""
Multi-Strategy Text Matching mit RapidFuzz
Research-basierte Implementierung für präzise Text-Positionierung in DOCX
"""

from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass
import re
from rapidfuzz import fuzz, process, utils
from xml.etree import ElementTree as ET


@dataclass
class MatchResult:
    """Repräsentiert ein Text-Matching-Ergebnis"""
    target_text: str
    matched_text: str
    match_score: float
    strategy_used: str
    paragraph_index: int
    char_start: int
    char_end: int
    confidence: float
    run_indices: List[int]  # XML-Run-Indices für präzise Positionierung


class MultiStrategyMatcher:
    """
    Multi-Strategy Text Matching System mit RapidFuzz
    
    Research-basierte Implementierung mit 4 Strategien:
    1. Exact Match: 100% exakte Übereinstimmung (höchste Priorität)
    2. Partial Ratio: Optimale Substring-Alignment (90% threshold)
    3. Token Sort Ratio: Wort-Reihenfolge-unabhängig (85% threshold) 
    4. Token Set Ratio: Wort-basierte Ähnlichkeit (80% threshold)
    
    Performance-optimiert durch:
    - Score-Cutoff für frühe Terminierung
    - Cascade-Matching mit Priority-System
    - Caching für wiederholte Anfragen
    """
    
    def __init__(self):
        # Matching-Strategien in Prioritätsreihenfolge
        self.strategies = [
            {
                'name': 'exact',
                'function': self._exact_match,
                'threshold': 100.0,
                'priority': 1,
                'description': 'Exakte Textübereinstimmung'
            },
            {
                'name': 'partial_ratio',
                'function': fuzz.partial_ratio,
                'threshold': 90.0,
                'priority': 2,
                'description': 'Optimale Substring-Alignment'
            },
            {
                'name': 'token_sort_ratio',
                'function': fuzz.token_sort_ratio,
                'threshold': 85.0,
                'priority': 3,
                'description': 'Wort-Reihenfolge-unabhängig'
            },
            {
                'name': 'token_set_ratio',
                'function': fuzz.token_set_ratio,
                'threshold': 80.0,
                'priority': 4,
                'description': 'Wort-basierte Ähnlichkeit'
            },
            {
                'name': 'wratio',
                'function': fuzz.WRatio,
                'threshold': 75.0,
                'priority': 5,
                'description': 'Gewichteter Multi-Algorithmus'
            }
        ]
        
        # Performance-Cache
        self._match_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Statistiken
        self.match_stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'strategy_usage': {},
            'average_scores': {}
        }
        
    def find_best_match(self, target_text: str, 
                       paragraph_texts: List[str],
                       min_score: float = 75.0) -> Optional[MatchResult]:
        """
        Findet die beste Übereinstimmung mit Multi-Strategy-Approach
        
        Args:
            target_text: Zu suchender Text
            paragraph_texts: Liste der Paragraph-Texte zum Durchsuchen
            min_score: Minimaler Score für gültiges Match
            
        Returns:
            MatchResult mit bester Übereinstimmung oder None
        """
        if not target_text.strip() or not paragraph_texts:
            return None
            
        # Cache-Check
        cache_key = f"{target_text[:50]}_{len(paragraph_texts)}"
        if cache_key in self._match_cache:
            self._cache_hits += 1
            return self._match_cache[cache_key]
        
        self._cache_misses += 1
        self.match_stats['total_matches'] += 1
        
        # Normalisiere Target-Text
        normalized_target = self._normalize_text(target_text)
        
        best_match = None
        best_score = 0.0
        
        # Durchsuche alle Paragraphen
        for para_idx, paragraph_text in enumerate(paragraph_texts):
            if not paragraph_text.strip():
                continue
                
            normalized_para = self._normalize_text(paragraph_text)
            
            # Teste alle Strategien in Prioritätsreihenfolge
            for strategy in self.strategies:
                match_result = self._apply_strategy(
                    normalized_target, 
                    normalized_para, 
                    paragraph_text,
                    para_idx,
                    strategy
                )
                
                if match_result and match_result.match_score >= strategy['threshold']:
                    # Aktualisiere Statistiken
                    strategy_name = strategy['name']
                    self.match_stats['strategy_usage'][strategy_name] = \
                        self.match_stats['strategy_usage'].get(strategy_name, 0) + 1
                    
                    # Prüfe ob dies das beste Match ist
                    if match_result.match_score > best_score:
                        best_match = match_result
                        best_score = match_result.match_score
                        
                        # Bei exakter Übereinstimmung: sofort zurückgeben
                        if match_result.match_score >= 99.5:
                            break
            
            # Early exit bei sehr gutem Match
            if best_score >= 95.0:
                break
        
        # Cache-Eintrag
        self._match_cache[cache_key] = best_match
        
        # Statistiken aktualisieren
        if best_match and best_match.match_score >= min_score:
            self.match_stats['successful_matches'] += 1
            
            # Durchschnitts-Score aktualisieren
            strategy_name = best_match.strategy_used
            current_avg = self.match_stats['average_scores'].get(strategy_name, [])
            current_avg.append(best_match.match_score)
            self.match_stats['average_scores'][strategy_name] = current_avg
        
        return best_match if best_match and best_match.match_score >= min_score else None
    
    def _apply_strategy(self, target_text: str, paragraph_text: str, 
                       original_para: str, para_idx: int, 
                       strategy: Dict) -> Optional[MatchResult]:
        """Wendet eine spezifische Matching-Strategie an"""
        
        try:
            # Berechne Score mit der Strategie
            if strategy['name'] == 'exact':
                score = strategy['function'](target_text, paragraph_text)
            else:
                score = strategy['function'](target_text, paragraph_text)
            
            if score < strategy['threshold']:
                return None
            
            # Finde char-Position im Original-Text
            char_positions = self._find_char_position(target_text, original_para)
            if not char_positions:
                return None
                
            char_start, char_end = char_positions
            
            # Erstelle MatchResult
            match_result = MatchResult(
                target_text=target_text,
                matched_text=original_para[char_start:char_end],
                match_score=score,
                strategy_used=strategy['name'],
                paragraph_index=para_idx,
                char_start=char_start,
                char_end=char_end,
                confidence=self._calculate_confidence(score, strategy['name']),
                run_indices=[]  # Wird später gesetzt bei XML-Verarbeitung
            )
            
            return match_result
            
        except Exception as e:
            print(f"   ⚠️  Fehler bei {strategy['name']}: {e}")
            return None
    
    def _exact_match(self, text1: str, text2: str) -> float:
        """Custom exact match function"""
        if text1 == text2:
            return 100.0
        elif text1 in text2 or text2 in text1:
            return 99.0  # Teilstring-Match
        else:
            return 0.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalisiert Text für besseres Matching"""
        if not text:
            return ""
            
        # Basis-Normalisierung
        normalized = text.strip()
        
        # Entferne übermäßige Whitespaces
        normalized = re.sub(r'\\s+', ' ', normalized)
        
        # Normalisiere Anführungszeichen
        normalized = normalized.replace('"', '"').replace('"', '"')
        normalized = normalized.replace(''', "'").replace(''', "'")
        
        # Normalisiere Gedankenstriche
        normalized = normalized.replace('–', '-').replace('—', '-')
        
        return normalized
    
    def _find_char_position(self, target_text: str, paragraph_text: str) -> Optional[Tuple[int, int]]:
        """Findet Zeichen-Position von target_text in paragraph_text"""
        
        # 1. Direkte Suche
        pos = paragraph_text.find(target_text)
        if pos != -1:
            return (pos, pos + len(target_text))
        
        # 2. Case-insensitive Suche
        pos = paragraph_text.lower().find(target_text.lower())
        if pos != -1:
            return (pos, pos + len(target_text))
        
        # 3. Suche nach Teilstring (erste 30 Zeichen)
        if len(target_text) > 30:
            short_target = target_text[:30]
            pos = paragraph_text.find(short_target)
            if pos != -1:
                end_pos = min(pos + len(target_text), len(paragraph_text))
                return (pos, end_pos)
        
        # 4. Wort-basierte Suche (erste 5 Wörter)
        target_words = target_text.split()[:5]
        if target_words:
            search_phrase = ' '.join(target_words)
            pos = paragraph_text.find(search_phrase)
            if pos != -1:
                end_pos = min(pos + len(search_phrase) + 20, len(paragraph_text))
                return (pos, end_pos)
        
        # 5. Fallback: Fuzzy-Position-Suche
        return self._fuzzy_position_search(target_text, paragraph_text)
    
    def _fuzzy_position_search(self, target_text: str, paragraph_text: str) -> Optional[Tuple[int, int]]:
        """Fuzzy-Suche für ungefähre Position"""
        
        # Teile Paragraph in Sliding-Windows
        target_len = len(target_text)
        window_size = max(target_len, 50)
        
        best_pos = None
        best_score = 0.0
        
        for i in range(0, len(paragraph_text) - window_size + 1, 10):
            window = paragraph_text[i:i + window_size]
            score = fuzz.partial_ratio(target_text, window)
            
            if score > best_score and score >= 70:
                best_score = score
                best_pos = (i, min(i + target_len, len(paragraph_text)))
        
        return best_pos
    
    def _calculate_confidence(self, score: float, strategy: str) -> float:
        """Berechnet Konfidenz basierend auf Score und Strategie"""
        
        # Strategie-spezifische Konfidenz-Faktoren
        confidence_factors = {
            'exact': 1.0,
            'partial_ratio': 0.9,
            'token_sort_ratio': 0.8,
            'token_set_ratio': 0.75,
            'wratio': 0.85
        }
        
        base_confidence = score / 100.0
        strategy_factor = confidence_factors.get(strategy, 0.7)
        
        return min(base_confidence * strategy_factor, 1.0)
    
    def find_multiple_matches(self, target_texts: List[str], 
                            paragraph_texts: List[str],
                            min_score: float = 75.0) -> List[MatchResult]:
        """Findet Matches für mehrere Target-Texte gleichzeitig"""
        
        results = []
        
        print(f"🎯 Suche Matches für {len(target_texts)} Texte in {len(paragraph_texts)} Paragraphen...")
        
        for i, target_text in enumerate(target_texts):
            match_result = self.find_best_match(target_text, paragraph_texts, min_score)
            
            if match_result:
                results.append(match_result)
                print(f"   ✅ Match {i+1}: {match_result.strategy_used} ({match_result.match_score:.1f}%)")
            else:
                print(f"   ❌ Kein Match {i+1}: '{target_text[:30]}...'")
        
        return results
    
    def get_performance_stats(self) -> Dict:
        """Gibt Performance-Statistiken zurück"""
        
        # Berechne Durchschnitts-Scores
        avg_scores = {}
        for strategy, scores in self.match_stats['average_scores'].items():
            if scores:
                avg_scores[strategy] = sum(scores) / len(scores)
        
        return {
            'cache_stats': {
                'hits': self._cache_hits,
                'misses': self._cache_misses,
                'hit_rate': self._cache_hits / max(self._cache_hits + self._cache_misses, 1)
            },
            'match_stats': {
                'total_matches': self.match_stats['total_matches'],
                'successful_matches': self.match_stats['successful_matches'],
                'success_rate': self.match_stats['successful_matches'] / max(self.match_stats['total_matches'], 1)
            },
            'strategy_usage': self.match_stats['strategy_usage'],
            'average_scores': avg_scores
        }
    
    def clear_cache(self):
        """Leert den Performance-Cache"""
        self._match_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


def main():
    """Test-Funktion für Multi-Strategy Matcher"""
    try:
        matcher = MultiStrategyMatcher()
        
        # Test-Daten
        target_texts = [
            "Die Studenten haben ihre Arbeiten abgegeben",
            "KI-basierte Technologien",
            "wissenschaftliche Arbeit",
            "Large Language Model",
            "nicht existierender Text"
        ]
        
        paragraph_texts = [
            "Die Studenten haben gestern ihre finalen Arbeiten abgegeben und warten nun auf die Bewertung.",
            "KI-basierte Technologien revolutionieren viele Bereiche der modernen Wissenschaft.",
            "Eine gute wissenschaftliche Arbeit erfordert methodisches Vorgehen und präzise Argumentation.",
            "Large Language Models wie GPT und Gemini haben die NLP-Forschung transformiert.",
            "Dies ist ein Paragraph ohne relevante Inhalte für die Suche."
        ]
        
        print("🧪 Teste Multi-Strategy Text Matching...")
        print(f"🎯 Target-Texte: {len(target_texts)}")
        print(f"📄 Paragraph-Texte: {len(paragraph_texts)}")
        
        # Einzelne Matches testen
        print(f"\n🔍 EINZELNE MATCHES:")
        for i, target in enumerate(target_texts):
            print(f"\n📝 Target {i+1}: '{target}'")
            
            match = matcher.find_best_match(target, paragraph_texts)
            
            if match:
                print(f"   ✅ Match gefunden!")
                print(f"   📊 Score: {match.match_score:.1f}%")
                print(f"   🔧 Strategie: {match.strategy_used}")
                print(f"   📍 Position: Paragraph {match.paragraph_index}, Char {match.char_start}-{match.char_end}")
                print(f"   💡 Konfidenz: {match.confidence:.1f}")
                print(f"   📖 Gefundener Text: '{match.matched_text[:50]}...'")
            else:
                print(f"   ❌ Kein Match gefunden")
        
        # Batch-Matching testen
        print(f"\n🚀 BATCH-MATCHING:")
        batch_results = matcher.find_multiple_matches(target_texts, paragraph_texts)
        
        print(f"\n📊 ERGEBNISSE:")
        print(f"   🎯 Successful Matches: {len(batch_results)}/{len(target_texts)}")
        
        # Performance-Statistiken
        stats = matcher.get_performance_stats()
        print(f"\n📈 PERFORMANCE-STATISTIKEN:")
        print(f"   🗄️  Cache Hit Rate: {stats['cache_stats']['hit_rate']:.1%}")
        print(f"   ✅ Match Success Rate: {stats['match_stats']['success_rate']:.1%}")
        print(f"   🔧 Strategy Usage: {dict(stats['strategy_usage'])}")
        print(f"   📊 Average Scores: {dict(stats['average_scores'])}")
        
        print(f"\n✅ Multi-Strategy Matching erfolgreich getestet!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()