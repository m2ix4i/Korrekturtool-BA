#!/usr/bin/env python3
"""
Style Manager für konfigurierbare Kommentar-Farben und -Stile
Ermöglicht flexible Anpassung der Kommentar-Darstellung
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CommentStyle:
    """Repräsentiert einen Kommentar-Stil"""
    color: str
    font_size: str = "18"
    style: str = "normal"  # normal, bold, italic
    icon: str = ""
    priority: str = "medium"
    border_style: str = "solid"
    border_width: str = "1px"
    highlight: bool = False


class StyleManager:
    """Verwaltet konfigurierbare Kommentar-Stile"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisiert den StyleManager
        
        Args:
            config_path (Optional[str]): Pfad zur Konfigurationsdatei
        """
        if config_path is None:
            # Standard-Pfad zur config/comment_styles.json
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "comment_styles.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_theme = "default"
    
    def _load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration aus JSON-Datei"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Konfigurationsdatei nicht gefunden: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            print(f"❌ Fehler beim Laden der Konfiguration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Gibt Standard-Konfiguration zurück"""
        return {
            "comment_styles": {
                "grammar": {"color": "DC143C", "font_size": "18", "style": "bold", "icon": "📝", "priority": "high"},
                "style": {"color": "FF8C00", "font_size": "18", "style": "italic", "icon": "✨", "priority": "medium"},
                "clarity": {"color": "228B22", "font_size": "18", "style": "normal", "icon": "💡", "priority": "medium"},
                "academic": {"color": "4169E1", "font_size": "18", "style": "bold", "icon": "🎓", "priority": "high"}
            },
            "author_settings": {
                "name": "KI Korrekturtool",
                "initials": "KI"
            },
            "global_settings": {
                "enable_icons": True,
                "enable_priority_colors": True
            }
        }
    
    def get_style_for_category(self, category: str) -> CommentStyle:
        """
        Gibt Stil für eine bestimmte Kategorie zurück
        
        Args:
            category (str): Kategorie-Name
            
        Returns:
            CommentStyle: Stil-Objekt für die Kategorie
        """
        styles = self.config.get("comment_styles", {})
        
        if category in styles:
            style_data = styles[category]
            
            # Ergänze Priority-Settings falls vorhanden
            priority = style_data.get("priority", "medium")
            priority_settings = self.config.get("priority_settings", {}).get(priority, {})
            
            # Merge Style-Daten mit Priority-Settings
            merged_data = {**style_data, **priority_settings}
            
            return CommentStyle(
                color=merged_data.get("color", "000000"),
                font_size=merged_data.get("font_size", "18"),
                style=merged_data.get("style", "normal"),
                icon=merged_data.get("icon", ""),
                priority=priority,
                border_style=merged_data.get("border_style", "solid"),
                border_width=merged_data.get("border_width", "1px"),
                highlight=merged_data.get("highlight", False)
            )
        else:
            # Standard-Stil für unbekannte Kategorien
            return CommentStyle(color="808080", icon="❓")
    
    def apply_theme(self, theme_name: str) -> bool:
        """
        Wendet ein vordefiniertes Theme an
        
        Args:
            theme_name (str): Name des Themes
            
        Returns:
            bool: True wenn Theme erfolgreich angewendet
        """
        themes = self.config.get("theme_presets", {})
        
        if theme_name not in themes:
            print(f"❌ Theme '{theme_name}' nicht gefunden")
            return False
        
        theme_data = themes[theme_name]
        theme_colors = theme_data.get("colors", {})
        
        # Aktualisiere Farben in den comment_styles
        for category, color in theme_colors.items():
            if category in self.config["comment_styles"]:
                self.config["comment_styles"][category]["color"] = color
        
        self.current_theme = theme_name
        print(f"✅ Theme '{theme_name}' angewendet")
        return True
    
    def get_available_themes(self) -> List[str]:
        """Gibt Liste verfügbarer Themes zurück"""
        return list(self.config.get("theme_presets", {}).keys())
    
    def get_theme_description(self, theme_name: str) -> str:
        """Gibt Beschreibung eines Themes zurück"""
        themes = self.config.get("theme_presets", {})
        if theme_name in themes:
            return themes[theme_name].get("description", "Keine Beschreibung verfügbar")
        return "Theme nicht gefunden"
    
    def format_comment_text(self, suggestion, template: str = "academic_detailed") -> str:
        """
        Formatiert Kommentar-Text nach Template
        
        Args:
            suggestion: Suggestion-Objekt mit Metadaten
            template (str): Template-Name
            
        Returns:
            str: Formatierter Kommentar-Text
        """
        templates = self.config.get("custom_templates", {})
        
        if template not in templates:
            # Fallback auf einfaches Format
            style = self.get_style_for_category(suggestion.category)
            icon = style.icon if self.config.get("global_settings", {}).get("enable_icons", True) else ""
            return f"{icon} {suggestion.suggested_text} -- Begründung: {suggestion.reason}"
        
        template_data = templates[template]
        style = self.get_style_for_category(suggestion.category)
        
        # Verfügbare Variablen für Template-Substitution
        variables = {
            'category_name': self._get_category_display_name(suggestion.category),
            'suggested_text': suggestion.suggested_text,
            'reason': suggestion.reason,
            'original_text': suggestion.original_text,
            'confidence': int(suggestion.confidence * 100),
            'priority': style.priority,
            'icon': style.icon if self.config.get("global_settings", {}).get("enable_icons", True) else ""
        }
        
        # Template-Formatierung
        try:
            prefix = template_data.get("prefix", "").format(**variables)
            content = template_data.get("format", "{suggested_text}").format(**variables)
            footer = template_data.get("footer", "").format(**variables)
            
            return f"{prefix}\n{content}{footer}".strip()
        except KeyError as e:
            print(f"⚠️  Template-Variable nicht gefunden: {e}")
            return f"{suggestion.suggested_text} -- {suggestion.reason}"
    
    def _get_category_display_name(self, category: str) -> str:
        """Gibt benutzerfreundlichen Kategorie-Namen zurück"""
        category_names = {
            'grammar': 'Grammatik & Rechtschreibung',
            'style': 'Stilistische Verbesserungen',
            'clarity': 'Klarheit & Verständlichkeit',
            'academic': 'Wissenschaftlicher Ausdruck',
            'structure': 'Struktur & Gliederung',
            'references': 'Literatur & Zitate',
            'methodology': 'Methodik & Argumentation',
            'formatting': 'Formatierung & Layout'
        }
        return category_names.get(category, category.title())
    
    def get_author_settings(self) -> Dict[str, str]:
        """Gibt Autor-Einstellungen zurück"""
        return self.config.get("author_settings", {
            "name": "KI Korrekturtool",
            "initials": "KI"
        })
    
    def get_color_for_category(self, category: str) -> str:
        """
        Gibt Hex-Farbcode für Kategorie zurück
        
        Args:
            category (str): Kategorie-Name
            
        Returns:
            str: Hex-Farbcode (ohne #)
        """
        style = self.get_style_for_category(category)
        return style.color
    
    def save_config(self) -> bool:
        """
        Speichert aktuelle Konfiguration in Datei
        
        Returns:
            bool: True wenn erfolgreich gespeichert
        """
        try:
            # Erstelle Verzeichnis falls nicht vorhanden
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Konfiguration gespeichert: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def customize_category_style(self, category: str, **kwargs) -> bool:
        """
        Passt Stil einer Kategorie an
        
        Args:
            category (str): Kategorie-Name
            **kwargs: Stil-Eigenschaften (color, font_size, style, etc.)
            
        Returns:
            bool: True wenn erfolgreich angepasst
        """
        if "comment_styles" not in self.config:
            self.config["comment_styles"] = {}
        
        if category not in self.config["comment_styles"]:
            self.config["comment_styles"][category] = {}
        
        # Aktualisiere nur übergebene Eigenschaften
        for key, value in kwargs.items():
            if key in ["color", "font_size", "style", "icon", "priority"]:
                self.config["comment_styles"][category][key] = value
        
        print(f"✅ Stil für '{category}' aktualisiert")
        return True
    
    def export_theme_as_json(self, theme_name: str, output_path: str) -> bool:
        """
        Exportiert aktuelles Theme als JSON-Datei
        
        Args:
            theme_name (str): Name für das neue Theme
            output_path (str): Ausgabe-Pfad
            
        Returns:
            bool: True wenn erfolgreich exportiert
        """
        try:
            export_data = {
                "theme_name": theme_name,
                "created_at": "2025-07-22",
                "comment_styles": self.config.get("comment_styles", {}),
                "author_settings": self.config.get("author_settings", {}),
                "global_settings": self.config.get("global_settings", {})
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Theme '{theme_name}' exportiert: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Export-Fehler: {e}")
            return False
    
    def print_style_overview(self):
        """Gibt Übersicht aller konfigurierten Stile aus"""
        print(f"\n🎨 STYLE MANAGER - ÜBERSICHT")
        print(f"{'=' * 50}")
        print(f"Aktives Theme: {self.current_theme}")
        print(f"Konfigurationsdatei: {self.config_path}")
        
        print(f"\n📋 Konfigurierte Kategorien:")
        styles = self.config.get("comment_styles", {})
        for category, style_data in styles.items():
            style = self.get_style_for_category(category)
            print(f"   {style.icon} {category:12} | #{style.color} | {style.priority:6} | {style.style}")
        
        print(f"\n🎭 Verfügbare Themes:")
        for theme in self.get_available_themes():
            desc = self.get_theme_description(theme)
            print(f"   - {theme}: {desc}")
        
        print(f"\n👤 Autor-Einstellungen:")
        author = self.get_author_settings()
        print(f"   Name: {author.get('name', 'N/A')}")
        print(f"   Initialen: {author.get('initials', 'N/A')}")


# Beispiel-Usage und Tests
if __name__ == '__main__':
    print("🎨 STYLE MANAGER TEST")
    print("=" * 40)
    
    # Initialisiere Style Manager
    style_manager = StyleManager()
    
    # Zeige Übersicht
    style_manager.print_style_overview()
    
    # Teste Style-Abruf
    print(f"\n🧪 STYLE-TESTS:")
    test_categories = ['grammar', 'style', 'academic', 'structure']
    
    for category in test_categories:
        style = style_manager.get_style_for_category(category)
        print(f"   {category}: #{style.color} | {style.icon} | {style.priority}")
    
    # Teste Theme-Wechsel
    print(f"\n🎭 THEME-TEST:")
    themes = style_manager.get_available_themes()
    if themes:
        first_theme = themes[0]
        print(f"Wechsle zu Theme: {first_theme}")
        style_manager.apply_theme(first_theme)
    
    print(f"\n✅ Style Manager Tests abgeschlossen!")