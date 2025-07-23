"""
Smart Comment Formatter mit Template-System
Research-basierte professionelle Kommentar-Formatierung ohne redundante Prefixes
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import os


@dataclass
class CommentStyle:
    """Repräsentiert einen Kommentar-Stil"""
    color: str
    icon: str
    priority: str
    description: str


class SmartCommentFormatter:
    """
    Smart Comment Formatter mit Template-System
    
    Features:
    - Entfernung des redundanten "KI-Analysetool:" Prefix
    - Template-basierte einheitliche Formatierung
    - Kategorie-spezifische Icons und Styles
    - Integration mit vorhandenem StyleManager
    - Professionelle, benutzerfreundliche Kommentar-Struktur
    """
    
    # Template-Definitionen
    TEMPLATES = {
        'academic_detailed': {
            'name': 'Akademisch Detailliert',
            'format': '{icon} {category_name}:\n{suggested_text}\n\n📝 {reason}\n\n📊 Konfidenz: {confidence:.1f}',
            'description': 'Ausführliche akademische Formatierung mit allen Details'
        },
        
        'simple': {
            'name': 'Einfach',
            'format': '{icon} {suggested_text}\n\n{reason}',
            'description': 'Einfache, kompakte Formatierung'
        },
        
        'detailed': {
            'name': 'Detailliert',
            'format': '{icon} {category_name}: {suggested_text}\n\n💡 Begründung: {reason}\n\n🎯 Kategorie: {category_display}\n📊 Konfidenz: {confidence:.1f}',
            'description': 'Detaillierte Formatierung mit Kategorieinfo'
        },
        
        'professional': {
            'name': 'Professionell',
            'format': '{suggested_text}\n\n{reason}',
            'description': 'Professionelle, minimalistische Formatierung'
        },
        
        'compact': {
            'name': 'Kompakt',
            'format': '{icon} {suggested_text} — {reason}',
            'description': 'Sehr kompakte einzeilige Formatierung'
        }
    }
    
    # Kategorie-Konfiguration
    CATEGORY_CONFIG = {
        'grammar': {
            'name': 'Grammatik & Rechtschreibung',
            'icon': '📝',
            'color': 'DC143C',
            'priority': 'high',
            'description': 'Satzzeichen, Grammatikfehler, Rechtschreibung'
        },
        'style': {
            'name': 'Stilistische Verbesserung',
            'icon': '✨',
            'color': '4B0082',
            'priority': 'medium',
            'description': 'Formulierungen, Redundanzen, Wissenschaftlichkeit'
        },
        'clarity': {
            'name': 'Klarheit & Verständlichkeit',
            'icon': '💡',
            'color': 'FF8C00',
            'priority': 'medium',
            'description': 'Präzisere Ausdrücke, Mehrdeutigkeiten'
        },
        'academic': {
            'name': 'Wissenschaftlicher Ausdruck',
            'icon': '🎓',
            'color': '006400',
            'priority': 'high',
            'description': 'Terminologie, Abkürzungen, Objektivität'
        },
        'structure': {
            'name': 'Struktur & Gliederung',
            'icon': '🗂️',
            'color': '800080',
            'priority': 'high',
            'description': 'Logischer Aufbau, Übergänge, Roter Faden'
        },
        'references': {
            'name': 'Zitierweise & Quellen',
            'icon': '📚',
            'color': '008B8B',
            'priority': 'high',
            'description': 'Korrekte Zitatformate, Quellenangaben'
        },
        'methodology': {
            'name': 'Methodische Beschreibung',
            'icon': '🔬',
            'color': 'B22222',
            'priority': 'high',
            'description': 'Nachvollziehbare Methoden, Validität'
        },
        'formatting': {
            'name': 'Formatierung & Layout',
            'icon': '🎨',
            'color': '708090',
            'priority': 'low',
            'description': 'Tabellen, Abbildungen, einheitliche Formatierung'
        }
    }
    
    def __init__(self):
        self.current_template = 'academic_detailed'
        self.stats = {
            'formatted_comments': 0,
            'template_usage': {},
            'category_usage': {}
        }
        
        # Versuche StyleManager zu integrieren falls verfügbar
        self.style_manager = None
        try:
            from .style_manager import StyleManager
            self.style_manager = StyleManager()
            print("📎 StyleManager erfolgreich integriert")
        except ImportError:
            print("⚠️  StyleManager nicht verfügbar - verwende interne Styles")
    
    def format_comment(self, suggestion, template: str = None) -> str:
        """
        Formatiert einen Kommentar mit dem gewählten Template
        
        Args:
            suggestion: Suggestion-Objekt mit original_text, suggested_text, reason, etc.
            template: Template-Name (optional, verwendet current_template)
            
        Returns:
            Formatierter Kommentar-Text
        """
        template_name = template or self.current_template
        
        if template_name not in self.TEMPLATES:
            template_name = 'academic_detailed'  # Fallback
        
        template_config = self.TEMPLATES[template_name]
        
        # Hole Kategorie-Informationen
        category_info = self.CATEGORY_CONFIG.get(suggestion.category.lower(), {
            'name': 'Allgemein',
            'icon': '📄',
            'color': '000000',
            'priority': 'medium',
            'description': 'Allgemeine Verbesserung'
        })
        
        # Bereite Formatierungs-Parameter vor
        format_params = {
            'icon': category_info['icon'],
            'category_name': category_info['name'],
            'category_display': suggestion.category.title(),
            'suggested_text': suggestion.suggested_text.strip(),
            'reason': suggestion.reason.strip(),
            'confidence': getattr(suggestion, 'confidence', 0.8),
            'original_text': suggestion.original_text[:50] + '...' if len(suggestion.original_text) > 50 else suggestion.original_text
        }
        
        # Formatiere Kommentar
        try:
            formatted_comment = template_config['format'].format(**format_params)
            
            # Statistiken aktualisieren
            self.stats['formatted_comments'] += 1
            self.stats['template_usage'][template_name] = self.stats['template_usage'].get(template_name, 0) + 1
            self.stats['category_usage'][suggestion.category] = self.stats['category_usage'].get(suggestion.category, 0) + 1
            
            return formatted_comment
            
        except Exception as e:
            print(f"⚠️  Formatierungsfehler: {e}")
            # Fallback zu einfacher Formatierung
            return f"{category_info['icon']} {suggestion.suggested_text}\n\n{suggestion.reason}"
    
    def format_multiple_comments(self, suggestions: List, template: str = None) -> List[str]:
        """Formatiert mehrere Kommentare gleichzeitig"""
        
        formatted_comments = []
        
        print(f"📝 Formatiere {len(suggestions)} Kommentare mit Template: {template or self.current_template}")
        
        for suggestion in suggestions:
            formatted_comment = self.format_comment(suggestion, template)
            formatted_comments.append(formatted_comment)
        
        return formatted_comments
    
    def set_template(self, template_name: str) -> bool:
        """Setzt das aktuelle Template"""
        
        if template_name in self.TEMPLATES:
            self.current_template = template_name
            print(f"✅ Template geändert zu: {template_name}")
            return True
        else:
            print(f"❌ Unbekanntes Template: {template_name}")
            return False
    
    def get_available_templates(self) -> Dict[str, str]:
        """Gibt verfügbare Templates mit Beschreibungen zurück"""
        
        return {
            name: config['description'] 
            for name, config in self.TEMPLATES.items()
        }
    
    def get_template_preview(self, template_name: str) -> str:
        """Erstellt Preview eines Templates mit Beispiel-Daten"""
        
        if template_name not in self.TEMPLATES:
            return "Template nicht gefunden"
        
        # Mock-Suggestion für Preview
        class MockSuggestion:
            def __init__(self):
                self.original_text = "Das ist gut zu bewerten"
                self.suggested_text = "Das ist positiv zu bewerten"
                self.reason = "\"Gut\" ist zu umgangssprachlich für wissenschaftliche Texte"
                self.category = "style"
                self.confidence = 0.85
        
        mock_suggestion = MockSuggestion()
        return self.format_comment(mock_suggestion, template_name)
    
    def get_category_info(self, category: str) -> Dict:
        """Gibt Informationen über eine Kategorie zurück"""
        
        return self.CATEGORY_CONFIG.get(category.lower(), {
            'name': 'Unbekannte Kategorie',
            'icon': '❓',
            'color': '000000',
            'priority': 'medium',
            'description': 'Keine Beschreibung verfügbar'
        })
    
    def create_custom_template(self, name: str, format_string: str, description: str) -> bool:
        """Erstellt ein benutzerdefiniertes Template"""
        
        try:
            # Teste Template mit Mock-Daten
            test_params = {
                'icon': '🧪',
                'category_name': 'Test',
                'category_display': 'Test',
                'suggested_text': 'Test-Vorschlag',
                'reason': 'Test-Begründung',
                'confidence': 0.8,
                'original_text': 'Test-Original'
            }
            
            # Teste Formatierung
            test_result = format_string.format(**test_params)
            
            # Füge Template hinzu
            self.TEMPLATES[name] = {
                'name': name.title(),
                'format': format_string,
                'description': description
            }
            
            print(f"✅ Custom Template '{name}' erstellt")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Templates: {e}")
            return False
    
    def export_formatted_comments(self, formatted_comments: List[str], 
                                 output_file: str = None) -> str:
        """Exportiert formatierte Kommentare in verschiedene Formate"""
        
        if output_file is None:
            output_file = f"/tmp/formatted_comments_{len(formatted_comments)}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Formatierte Kommentare\n\n")
                f.write(f"Template verwendet: {self.current_template}\n")
                f.write(f"Anzahl Kommentare: {len(formatted_comments)}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, comment in enumerate(formatted_comments, 1):
                    f.write(f"## Kommentar {i}\n\n")
                    f.write(comment)
                    f.write("\n\n" + "-" * 30 + "\n\n")
            
            print(f"📤 Kommentare exportiert nach: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Export-Fehler: {e}")
            return ""
    
    def get_formatting_stats(self) -> Dict:
        """Gibt Formatierungs-Statistiken zurück"""
        
        return {
            'total_formatted': self.stats['formatted_comments'],
            'template_usage': dict(self.stats['template_usage']),
            'category_usage': dict(self.stats['category_usage']),
            'current_template': self.current_template,
            'available_templates': len(self.TEMPLATES)
        }
    
    def reset_stats(self):
        """Setzt Statistiken zurück"""
        self.stats = {
            'formatted_comments': 0,
            'template_usage': {},
            'category_usage': {}
        }


def main():
    """Test-Funktion für Smart Comment Formatter"""
    try:
        formatter = SmartCommentFormatter()
        
        # Mock-Suggestions für Test
        class MockSuggestion:
            def __init__(self, original, suggested, reason, category, confidence=0.8):
                self.original_text = original
                self.suggested_text = suggested
                self.reason = reason
                self.category = category
                self.confidence = confidence
        
        test_suggestions = [
            MockSuggestion(
                "Das ist gut zu bewerten",
                "Das ist positiv zu bewerten", 
                "\"Gut\" ist zu umgangssprachlich für wissenschaftliche Texte",
                "style",
                0.9
            ),
            MockSuggestion(
                "Die Studenten haben",
                "Die Probanden haben",
                "\"Studenten\" ist unspezifisch; \"Probanden\" ist präziser",
                "academic",
                0.85
            ),
            MockSuggestion(
                "Es ist zu bemerken, dass",
                "Daraus folgt, dass",
                "Umständliche Formulierung vereinfachen",
                "clarity",
                0.8
            )
        ]
        
        print("🧪 Teste Smart Comment Formatter...")
        print(f"📝 Test-Suggestions: {len(test_suggestions)}")
        
        # Teste verfügbare Templates
        print(f"\n📋 VERFÜGBARE TEMPLATES:")
        templates = formatter.get_available_templates()
        for name, desc in templates.items():
            print(f"   {name}: {desc}")
        
        # Teste verschiedene Templates
        print(f"\n🎨 TEMPLATE-TESTS:")
        for template_name in ['academic_detailed', 'simple', 'professional']:
            print(f"\n--- Template: {template_name} ---")
            
            # Preview
            preview = formatter.get_template_preview(template_name)
            print(f"📄 Preview:\n{preview}")
            
            # Formatiere alle Test-Suggestions
            formatted = formatter.format_multiple_comments(test_suggestions, template_name)
            print(f"✅ {len(formatted)} Kommentare formatiert")
        
        # Teste Kategorie-Informationen
        print(f"\n🏷️  KATEGORIE-INFORMATIONEN:")
        for category in ['grammar', 'style', 'clarity', 'academic']:
            info = formatter.get_category_info(category)
            print(f"   {info['icon']} {info['name']}: {info['description']}")
        
        # Teste Custom Template
        print(f"\n🛠️  CUSTOM TEMPLATE TEST:")
        success = formatter.create_custom_template(
            'minimal',
            '{suggested_text} ({reason})',
            'Minimalistische einzeilige Formatierung'
        )
        
        if success:
            minimal_preview = formatter.get_template_preview('minimal')
            print(f"📄 Custom Template Preview:\n{minimal_preview}")
        
        # Export-Test
        print(f"\n📤 EXPORT-TEST:")
        final_formatted = formatter.format_multiple_comments(test_suggestions, 'academic_detailed')
        export_file = formatter.export_formatted_comments(final_formatted)
        
        # Statistiken
        print(f"\n📊 FORMATIERUNGS-STATISTIKEN:")
        stats = formatter.get_formatting_stats()
        print(f"   Formatierte Kommentare: {stats['total_formatted']}")
        print(f"   Template-Nutzung: {stats['template_usage']}")
        print(f"   Kategorie-Nutzung: {stats['category_usage']}")
        
        print(f"\n✅ Smart Comment Formatter erfolgreich getestet!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()