#!/usr/bin/env python3
"""
Advanced Caching System für wiederkehrende KI-Analysen
Implementiert intelligente Cache-Strategien mit Persistierung
"""

import os
import hashlib
import pickle
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import logging


@dataclass
class CacheEntry:
    """Cache-Eintrag mit Metadaten"""
    key: str
    value: Any
    timestamp: float
    access_count: int
    text_hash: str
    category: str
    size_bytes: int


@dataclass
class CacheStats:
    """Cache-Statistiken"""
    total_entries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size_mb: float
    oldest_entry: float
    newest_entry: float


class AdvancedCachingSystem:
    """
    Advanced Caching System für KI-Analysen
    
    Features:
    - Memory + Disk Persistierung
    - LRU + TTL Cache-Strategien
    - Intelligent Key-Generation
    - Performance-Monitoring
    - Cache-Warming und Cleanup
    """
    
    def __init__(self, cache_dir: str = None, max_memory_entries: int = 1000,
                 max_disk_size_mb: int = 100, ttl_hours: int = 24):
        
        # Konfiguration
        self.cache_dir = Path(cache_dir or os.path.join(os.getcwd(), '.cache'))
        self.max_memory_entries = max_memory_entries
        self.max_disk_size_mb = max_disk_size_mb
        self.ttl_seconds = ttl_hours * 3600
        
        # Memory-Cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # Statistiken
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_reads': 0,
            'disk_writes': 0
        }
        
        # Threading-Lock
        self.lock = threading.RLock()
        
        # Setup
        self._setup_cache_directory()
        self._load_persistent_cache()
        
        # Logging
        self.logger = logging.getLogger('CachingSystem')
        self.logger.info(f"💾 Cache initialisiert: {self.cache_dir}")
    
    def _setup_cache_directory(self):
        """Erstellt Cache-Verzeichnis"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Unterverzeichnisse
        (self.cache_dir / 'suggestions').mkdir(exist_ok=True)
        (self.cache_dir / 'analysis').mkdir(exist_ok=True)
        (self.cache_dir / 'metadata').mkdir(exist_ok=True)
    
    def _generate_cache_key(self, text: str, category: str, 
                          additional_params: Dict = None) -> str:
        """Generiert eindeutigen Cache-Key"""
        
        # Basis-Hash aus Text
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
        # Parameter-Hash
        params_str = f"{category}"
        if additional_params:
            params_str += json.dumps(additional_params, sort_keys=True)
        
        params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]
        
        return f"{category}_{text_hash}_{params_hash}"
    
    def get(self, text: str, category: str, 
            additional_params: Dict = None) -> Optional[Any]:
        """Holt Wert aus Cache"""
        
        cache_key = self._generate_cache_key(text, category, additional_params)
        
        with self.lock:
            # 1. Memory-Cache prüfen
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # TTL prüfen
                if self._is_entry_valid(entry):
                    entry.access_count += 1
                    self.stats['hits'] += 1
                    
                    self.logger.debug(f"💾 Memory-Cache Hit: {cache_key[:20]}...")
                    return entry.value
                else:
                    # Expired - entfernen
                    del self.memory_cache[cache_key]
            
            # 2. Disk-Cache prüfen
            disk_entry = self._load_from_disk(cache_key, category)
            if disk_entry and self._is_entry_valid(disk_entry):
                # In Memory-Cache laden
                self._add_to_memory_cache(disk_entry)
                
                self.stats['hits'] += 1
                self.stats['disk_reads'] += 1
                
                self.logger.debug(f"💿 Disk-Cache Hit: {cache_key[:20]}...")
                return disk_entry.value
            
            # Cache Miss
            self.stats['misses'] += 1
            self.logger.debug(f"❌ Cache Miss: {cache_key[:20]}...")
            return None
    
    def put(self, text: str, category: str, value: Any,
            additional_params: Dict = None):
        """Speichert Wert in Cache"""
        
        cache_key = self._generate_cache_key(text, category, additional_params)
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
        # Erstelle Cache-Entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            timestamp=time.time(),
            access_count=1,
            text_hash=text_hash,
            category=category,
            size_bytes=len(pickle.dumps(value))
        )
        
        with self.lock:
            # In Memory-Cache speichern
            self._add_to_memory_cache(entry)
            
            # Auf Disk persistieren
            self._save_to_disk(entry)
            
            self.logger.debug(f"💾 Cache Put: {cache_key[:20]}... ({entry.size_bytes} bytes)")
    
    def _add_to_memory_cache(self, entry: CacheEntry):
        """Fügt Entry zum Memory-Cache hinzu mit LRU-Eviction"""
        
        # Prüfe Memory-Limit
        if len(self.memory_cache) >= self.max_memory_entries:
            self._evict_lru_entry()
        
        self.memory_cache[entry.key] = entry
    
    def _evict_lru_entry(self):
        """Entfernt LRU-Entry aus Memory-Cache"""
        
        if not self.memory_cache:
            return
        
        # Finde Entry mit niedrigstem access_count und ältestem timestamp
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: (
                self.memory_cache[k].access_count,
                self.memory_cache[k].timestamp
            )
        )
        
        del self.memory_cache[lru_key]
        self.stats['evictions'] += 1
        
        self.logger.debug(f"🗑️  LRU Eviction: {lru_key[:20]}...")
    
    def _is_entry_valid(self, entry: CacheEntry) -> bool:
        """Prüft ob Cache-Entry noch gültig ist"""
        
        age_seconds = time.time() - entry.timestamp
        return age_seconds < self.ttl_seconds
    
    def _save_to_disk(self, entry: CacheEntry):
        """Speichert Entry auf Disk"""
        
        try:
            category_dir = self.cache_dir / entry.category
            category_dir.mkdir(exist_ok=True)
            
            file_path = category_dir / f"{entry.key}.pkl"
            
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
            
            self.stats['disk_writes'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Disk-Write Fehler: {e}")
    
    def _load_from_disk(self, cache_key: str, category: str) -> Optional[CacheEntry]:
        """Lädt Entry von Disk"""
        
        try:
            file_path = self.cache_dir / category / f"{cache_key}.pkl"
            
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    entry = pickle.load(f)
                    return entry
            
        except Exception as e:
            self.logger.error(f"❌ Disk-Read Fehler: {e}")
        
        return None
    
    def _load_persistent_cache(self):
        """Lädt persistenten Cache beim Start"""
        
        if not self.cache_dir.exists():
            return
        
        loaded_count = 0
        
        for category_dir in self.cache_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            for cache_file in category_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    # Nur gültige Entries laden
                    if self._is_entry_valid(entry):
                        # Memory-Limit respektieren
                        if len(self.memory_cache) < self.max_memory_entries:
                            self.memory_cache[entry.key] = entry
                            loaded_count += 1
                    else:
                        # Expired - Datei löschen
                        cache_file.unlink()
                
                except Exception as e:
                    self.logger.warning(f"⚠️  Cache-Load Fehler {cache_file}: {e}")
        
        if loaded_count > 0:
            self.logger.info(f"📂 {loaded_count} Cache-Entries geladen")
    
    def cleanup_expired(self):
        """Bereinigt abgelaufene Cache-Entries"""
        
        with self.lock:
            # Memory-Cache bereinigen
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if not self._is_entry_valid(entry)
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Disk-Cache bereinigen
            disk_cleaned = 0
            for category_dir in self.cache_dir.iterdir():
                if not category_dir.is_dir():
                    continue
                
                for cache_file in category_dir.glob("*.pkl"):
                    try:
                        with open(cache_file, 'rb') as f:
                            entry = pickle.load(f)
                        
                        if not self._is_entry_valid(entry):
                            cache_file.unlink()
                            disk_cleaned += 1
                    
                    except:
                        # Korrupte Datei - löschen
                        cache_file.unlink()
                        disk_cleaned += 1
            
            total_cleaned = len(expired_keys) + disk_cleaned
            if total_cleaned > 0:
                self.logger.info(f"🧹 {total_cleaned} expired Entries bereinigt")
    
    def get_cache_stats(self) -> CacheStats:
        """Vollständige Cache-Statistiken"""
        
        with self.lock:
            total_entries = len(self.memory_cache)
            total_hits = self.stats['hits']
            total_misses = self.stats['misses']
            
            hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
            
            # Größe berechnen
            total_size_bytes = sum(entry.size_bytes for entry in self.memory_cache.values())
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            # Zeitstempel
            timestamps = [entry.timestamp for entry in self.memory_cache.values()]
            oldest_entry = min(timestamps) if timestamps else 0
            newest_entry = max(timestamps) if timestamps else 0
            
            return CacheStats(
                total_entries=total_entries,
                cache_hits=total_hits,
                cache_misses=total_misses,
                hit_rate=hit_rate,
                total_size_mb=total_size_mb,
                oldest_entry=oldest_entry,
                newest_entry=newest_entry
            )
    
    def warm_cache(self, texts: List[str], categories: List[str]):
        """Cache-Warming für häufig verwendete Kombinationen"""
        
        self.logger.info(f"🔥 Cache-Warming: {len(texts)} Texte, {len(categories)} Kategorien")
        
        # Placeholder für Cache-Warming-Logik
        # In der realen Implementierung würden hier vorab Analysen durchgeführt
        for text in texts:
            for category in categories:
                cache_key = self._generate_cache_key(text, category)
                # Simuliere Warm-Entry
                # self.put(text, category, "warmed_result")
    
    def clear_cache(self):
        """Löscht kompletten Cache"""
        
        with self.lock:
            # Memory-Cache löschen
            self.memory_cache.clear()
            
            # Disk-Cache löschen
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self._setup_cache_directory()
            
            # Statistiken zurücksetzen
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'disk_reads': 0,
                'disk_writes': 0
            }
            
            self.logger.info("🧹 Cache komplett geleert")


def main():
    """Test-Funktion für Caching System"""
    
    print("🧪 ADVANCED CACHING SYSTEM - TEST")
    print("=" * 50)
    
    # Erstelle Cache-System
    cache = AdvancedCachingSystem(
        cache_dir=".test_cache",
        max_memory_entries=5,
        ttl_hours=1
    )
    
    # Test-Daten
    test_texts = [
        "Das ist ein Test-Text für die Cache-Funktionalität.",
        "Ein weiterer Test-Text mit anderem Inhalt.",
        "Dritter Test-Text für vollständige Abdeckung."
    ]
    
    categories = ['grammar', 'style', 'clarity']
    
    print(f"📝 Test-Daten: {len(test_texts)} Texte, {len(categories)} Kategorien")
    
    # 1. Cache-Misses (initial)
    print(f"\n🔍 Teste Cache-Misses...")
    for i, text in enumerate(test_texts):
        for category in categories:
            result = cache.get(text, category)
            assert result is None, f"Unerwarteter Cache-Hit bei {i}/{category}"
    
    print(f"   ✅ Alle Cache-Misses korrekt")
    
    # 2. Cache-Puts
    print(f"\n💾 Teste Cache-Puts...")
    for i, text in enumerate(test_texts):
        for category in categories:
            # Simuliere KI-Analyse-Ergebnis
            mock_result = {
                'suggestions': [f"{category}_suggestion_{i}"],
                'confidence': 0.8 + i * 0.05,
                'processing_time': 1.2 + i * 0.1
            }
            cache.put(text, category, mock_result)
    
    print(f"   ✅ {len(test_texts) * len(categories)} Entries gespeichert")
    
    # 3. Cache-Hits
    print(f"\n🎯 Teste Cache-Hits...")
    hits = 0
    for i, text in enumerate(test_texts):
        for category in categories:
            result = cache.get(text, category)
            if result is not None:
                hits += 1
                assert result['suggestions'][0] == f"{category}_suggestion_{i}"
    
    print(f"   ✅ {hits} Cache-Hits erfolgreich")
    
    # 4. Cache-Statistiken
    stats = cache.get_cache_stats()
    print(f"\n📊 CACHE-STATISTIKEN:")
    print(f"   📝 Total Entries: {stats.total_entries}")
    print(f"   ✅ Cache Hits: {stats.cache_hits}")
    print(f"   ❌ Cache Misses: {stats.cache_misses}")
    print(f"   📈 Hit Rate: {stats.hit_rate:.1%}")
    print(f"   💾 Total Size: {stats.total_size_mb:.2f} MB")
    
    # 5. LRU-Eviction testen
    print(f"\n🗑️  Teste LRU-Eviction...")
    # Füge mehr Entries hinzu als max_memory_entries
    for i in range(3):
        extra_text = f"Extra Text {i} für LRU-Test"
        cache.put(extra_text, 'test', {'extra': True})
    
    final_stats = cache.get_cache_stats()
    print(f"   📊 Entries nach Eviction: {final_stats.total_entries}")
    print(f"   🗑️  Evictions: {cache.stats['evictions']}")
    
    # 6. Cleanup
    print(f"\n🧹 Teste Cleanup...")
    cache.cleanup_expired()
    cache.clear_cache()
    
    print(f"\n✅ ADVANCED CACHING SYSTEM TEST ABGESCHLOSSEN")


if __name__ == "__main__":
    # Setup Logging für Test
    logging.basicConfig(level=logging.INFO)
    main()