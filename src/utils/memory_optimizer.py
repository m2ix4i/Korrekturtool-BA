#!/usr/bin/env python3
"""
Advanced Memory Optimizer für ressourceneffiziente Dokumentverarbeitung
Implementiert intelligente Memory-Management-Strategien
"""

import os
import gc
import sys
import psutil
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager
import logging
import weakref


@dataclass
class MemoryConfig:
    """Konfiguration für Memory-Management"""
    max_memory_mb: int = 1024          # Maximaler Memory-Verbrauch
    warning_threshold: float = 0.8     # Warnung bei 80% des Limits
    critical_threshold: float = 0.95   # Kritisch bei 95% des Limits
    gc_frequency: int = 10             # Garbage Collection alle N Operationen
    monitor_interval: float = 5.0      # Monitoring-Intervall in Sekunden
    enable_monitoring: bool = True     # Real-time Monitoring aktivieren
    enable_optimization: bool = True   # Automatische Optimierungen aktivieren


@dataclass
class MemoryStats:
    """Memory-Statistiken"""
    current_usage_mb: float
    peak_usage_mb: float
    system_total_mb: float
    system_available_mb: float
    process_percent: float
    gc_collections: int
    optimization_events: int


class MemoryOptimizer:
    """
    Advanced Memory Optimizer für große Dokument-Verarbeitung
    
    Features:
    - Real-time Memory-Monitoring
    - Adaptive Garbage Collection
    - Memory-Leak-Erkennung
    - Automatische Optimierungen
    - Resource-aware Processing
    """
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        
        # Tracking-Variablen
        self.peak_memory = 0.0
        self.baseline_memory = 0.0
        self.gc_collections = 0
        self.optimization_events = 0
        self.operation_counter = 0
        
        # Memory-Historie für Leak-Detection
        self.memory_history = []
        self.max_history_size = 100
        
        # Monitoring-Thread
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Registered cleanup functions
        self._cleanup_functions: List[Callable] = []
        
        # Setup Logging
        self.logger = logging.getLogger('MemoryOptimizer')
        
        # Initialisiere Baseline
        self._establish_baseline()
        
        # Starte Monitoring falls aktiviert
        if self.config.enable_monitoring:
            self.start_monitoring()
    
    def _establish_baseline(self):
        """Etabliert Memory-Baseline für Vergleiche"""
        self.baseline_memory = self._get_current_memory()
        self.peak_memory = self.baseline_memory
        
        self.logger.info(f"💾 Memory-Baseline etabliert: {self.baseline_memory:.1f} MB")
    
    def _get_current_memory(self) -> float:
        """Aktuelle Memory-Usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def _get_system_memory_info(self) -> Dict[str, float]:
        """System Memory-Informationen"""
        memory = psutil.virtual_memory()
        return {
            'total_mb': memory.total / (1024 * 1024),
            'available_mb': memory.available / (1024 * 1024),
            'used_percent': memory.percent
        }
    
    @contextmanager
    def memory_context(self, operation_name: str = "Operation"):
        """Context Manager für Memory-bewusste Operationen"""
        
        start_memory = self._get_current_memory()
        self.logger.debug(f"🔄 Start {operation_name}: {start_memory:.1f} MB")
        
        try:
            yield self
            
        finally:
            end_memory = self._get_current_memory()
            memory_diff = end_memory - start_memory
            
            # Update Statistics
            self.peak_memory = max(self.peak_memory, end_memory)
            self.operation_counter += 1
            
            # Add to history
            self.memory_history.append({
                'timestamp': time.time(),
                'operation': operation_name,
                'start_memory': start_memory,
                'end_memory': end_memory,
                'memory_diff': memory_diff
            })
            
            # Trim history
            if len(self.memory_history) > self.max_history_size:
                self.memory_history.pop(0)
            
            self.logger.debug(f"✅ End {operation_name}: {end_memory:.1f} MB ({memory_diff:+.1f} MB)")
            
            # Trigger optimizations if needed
            if self.config.enable_optimization:
                self._check_and_optimize(end_memory)
    
    def _check_and_optimize(self, current_memory: float):
        """Prüft Memory-Status und triggert Optimierungen"""
        
        memory_ratio = current_memory / self.config.max_memory_mb
        
        # Warnung bei hohem Memory-Verbrauch
        if memory_ratio > self.config.warning_threshold:
            self.logger.warning(f"⚠️  Hoher Memory-Verbrauch: {current_memory:.1f} MB ({memory_ratio:.1%})")
        
        # Kritische Optimierungen bei sehr hohem Verbrauch
        if memory_ratio > self.config.critical_threshold:
            self.logger.error(f"🚨 Kritischer Memory-Verbrauch: {current_memory:.1f} MB")
            self._emergency_optimization()
        
        # Regelmäßige Garbage Collection
        elif self.operation_counter % self.config.gc_frequency == 0:
            self._gentle_optimization()
    
    def _gentle_optimization(self):
        """Sanfte Memory-Optimierung"""
        
        before_memory = self._get_current_memory()
        
        # Garbage Collection
        collected = gc.collect()
        self.gc_collections += 1
        
        after_memory = self._get_current_memory()
        freed_memory = before_memory - after_memory
        
        if freed_memory > 1.0:  # Nur loggen wenn signifikant
            self.logger.info(f"🧽 Gentle GC: {freed_memory:.1f} MB freigegeben ({collected} Objekte)")
        
        self.optimization_events += 1
    
    def _emergency_optimization(self):
        """Notfall-Memory-Optimierung"""
        
        before_memory = self._get_current_memory()
        self.logger.warning(f"🚨 Starte Emergency Memory Optimization: {before_memory:.1f} MB")
        
        # 1. Forcierte Garbage Collection
        for generation in range(3):
            collected = gc.collect(generation)
            if collected > 0:
                self.logger.info(f"   🗑️  Generation {generation}: {collected} Objekte freigegeben")
        
        # 2. Cleanup-Funktionen ausführen
        for cleanup_func in self._cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                self.logger.error(f"   ❌ Cleanup-Fehler: {e}")
        
        # 3. System-Memory freigeben (wenn möglich)
        try:
            import ctypes
            ctypes.cdll.msvcrt._set_malloc_crt_max_wait(0)  # Windows-spezifisch
        except:
            pass
        
        after_memory = self._get_current_memory()
        freed_memory = before_memory - after_memory
        
        self.logger.warning(f"🚨 Emergency Optimization: {freed_memory:.1f} MB freigegeben")
        self.optimization_events += 1
        
        # Wenn immer noch kritisch, weitere Maßnahmen
        if after_memory / self.config.max_memory_mb > self.config.critical_threshold:
            self.logger.error(f"🔥 Memory kritisch nach Optimization - erwäge Process-Restart")
    
    def register_cleanup_function(self, cleanup_func: Callable):
        """Registriert Cleanup-Funktion für Emergency-Optimization"""
        self._cleanup_functions.append(cleanup_func)
    
    def start_monitoring(self):
        """Startet Memory-Monitoring-Thread"""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info(f"📊 Memory-Monitoring gestartet (Intervall: {self.config.monitor_interval}s)")
    
    def stop_monitoring(self):
        """Stoppt Memory-Monitoring"""
        
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        self.logger.info("📊 Memory-Monitoring gestoppt")
    
    def _monitoring_loop(self):
        """Monitoring-Loop für kontinuierliche Memory-Überwachung"""
        
        while self.monitoring_active:
            try:
                current_memory = self._get_current_memory()
                system_info = self._get_system_memory_info()
                
                # Update Peak
                self.peak_memory = max(self.peak_memory, current_memory)
                
                # Log bei signifikanten Änderungen
                if len(self.memory_history) > 0:
                    last_memory = self.memory_history[-1]['end_memory']
                    memory_change = current_memory - last_memory
                    
                    if abs(memory_change) > 10.0:  # Signifikante Änderung: 10+ MB
                        self.logger.info(f"📊 Memory-Change: {memory_change:+.1f} MB (Current: {current_memory:.1f} MB)")
                
                # Check für Memory-Leaks
                self._check_memory_leaks()
                
                time.sleep(self.config.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring-Fehler: {e}")
                time.sleep(5.0)  # Länger warten bei Fehlern
    
    def _check_memory_leaks(self):
        """Prüft auf potentielle Memory-Leaks"""
        
        if len(self.memory_history) < 10:
            return
        
        # Analysiere letzten 10 Operationen
        recent_operations = self.memory_history[-10:]
        memory_growth = recent_operations[-1]['end_memory'] - recent_operations[0]['start_memory']
        
        # Warnung bei kontinuierlichem Wachstum
        if memory_growth > 50.0:  # 50+ MB Wachstum in 10 Operationen
            self.logger.warning(f"🔍 Potentieller Memory-Leak erkannt: +{memory_growth:.1f} MB in 10 Operationen")
    
    def get_memory_stats(self) -> MemoryStats:
        """Vollständige Memory-Statistiken"""
        
        current_memory = self._get_current_memory()
        system_info = self._get_system_memory_info()
        
        return MemoryStats(
            current_usage_mb=current_memory,
            peak_usage_mb=self.peak_memory,
            system_total_mb=system_info['total_mb'],
            system_available_mb=system_info['available_mb'],
            process_percent=(current_memory / system_info['total_mb']) * 100,
            gc_collections=self.gc_collections,
            optimization_events=self.optimization_events
        )
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Detaillierter Memory-Report"""
        
        stats = self.get_memory_stats()
        
        # Analysiere Memory-History
        if self.memory_history:
            total_operations = len(self.memory_history)
            memory_changes = [op['memory_diff'] for op in self.memory_history]
            avg_memory_change = sum(memory_changes) / len(memory_changes)
            max_memory_change = max(memory_changes)
            min_memory_change = min(memory_changes)
        else:
            total_operations = 0
            avg_memory_change = 0
            max_memory_change = 0
            min_memory_change = 0
        
        return {
            'current_status': {
                'current_memory_mb': stats.current_usage_mb,
                'peak_memory_mb': stats.peak_usage_mb,
                'baseline_memory_mb': self.baseline_memory,
                'memory_growth_mb': stats.current_usage_mb - self.baseline_memory
            },
            'system_status': {
                'total_memory_mb': stats.system_total_mb,
                'available_memory_mb': stats.system_available_mb,
                'process_percent': stats.process_percent,
                'system_usage_percent': (stats.system_total_mb - stats.system_available_mb) / stats.system_total_mb * 100
            },
            'optimization_stats': {
                'gc_collections': stats.gc_collections,
                'optimization_events': stats.optimization_events,
                'total_operations': total_operations,
                'avg_memory_change_mb': avg_memory_change,
                'max_memory_change_mb': max_memory_change,
                'min_memory_change_mb': min_memory_change
            },
            'config': {
                'max_memory_mb': self.config.max_memory_mb,
                'warning_threshold': self.config.warning_threshold,
                'critical_threshold': self.config.critical_threshold,
                'monitoring_active': self.monitoring_active
            }
        }
    
    def __del__(self):
        """Cleanup beim Zerstören des Optimizers"""
        self.stop_monitoring()


def main():
    """Test-Funktion für Memory Optimizer"""
    
    print("🧪 ADVANCED MEMORY OPTIMIZER - TEST")
    print("=" * 50)
    
    # Konfiguration
    config = MemoryConfig(
        max_memory_mb=256,
        warning_threshold=0.7,
        enable_monitoring=True,
        monitor_interval=2.0
    )
    
    # Erstelle Optimizer
    optimizer = MemoryOptimizer(config)
    
    # Zeige Initial-Stats
    initial_stats = optimizer.get_memory_stats()
    print(f"💾 Initial Memory: {initial_stats.current_usage_mb:.1f} MB")
    print(f"💾 System Available: {initial_stats.system_available_mb:.0f} MB")
    
    # Test Memory-Context
    print(f"\n🔄 Teste Memory-Context...")
    
    with optimizer.memory_context("Test Operation 1"):
        # Simuliere Memory-Verbrauch
        test_data = [list(range(10000)) for _ in range(100)]  # ~40MB
        time.sleep(1)
    
    with optimizer.memory_context("Test Operation 2"):
        # Mehr Memory-Verbrauch
        more_data = [list(range(20000)) for _ in range(150)]  # ~120MB
        time.sleep(1)
    
    # Memory-Stats nach Tests
    final_stats = optimizer.get_memory_stats()
    print(f"\n📊 MEMORY-STATISTICS:")
    print(f"   💾 Current Usage: {final_stats.current_usage_mb:.1f} MB")
    print(f"   📈 Peak Usage: {final_stats.peak_usage_mb:.1f} MB")
    print(f"   🧽 GC Collections: {final_stats.gc_collections}")
    print(f"   ⚙️  Optimization Events: {final_stats.optimization_events}")
    
    # Detaillierter Report
    report = optimizer.get_detailed_report()
    print(f"\n📋 DETAILED REPORT:")
    print(f"   📈 Memory Growth: {report['current_status']['memory_growth_mb']:+.1f} MB")
    print(f"   📊 Process Usage: {report['system_status']['process_percent']:.2f}% of System")
    print(f"   🔢 Total Operations: {report['optimization_stats']['total_operations']}")
    print(f"   📊 Avg Memory Change: {report['optimization_stats']['avg_memory_change_mb']:+.1f} MB/Op")
    
    # Cleanup
    optimizer.stop_monitoring()
    
    print(f"\n✅ MEMORY OPTIMIZER TEST ABGESCHLOSSEN")


if __name__ == "__main__":
    # Setup Logging für Test
    logging.basicConfig(level=logging.INFO)
    main()