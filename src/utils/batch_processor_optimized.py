#!/usr/bin/env python3
"""
Optimized Batch Processor für große Dokumente
Vereinfachte aber robuste Implementierung mit Memory-Management
"""

import os
import sys
import time
import psutil
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import der Advanced-Module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.analyzers.advanced_gemini_analyzer import AdvancedGeminiAnalyzer
from src.utils.advanced_chunking import AdvancedChunker, TextChunk
from src.utils.smart_comment_formatter import SmartCommentFormatter


@dataclass
class OptimizedBatchConfig:
    """Optimierte Konfiguration für Batch-Verarbeitung"""
    max_workers: int = 2           # Anzahl paralleler Workers
    chunk_target_size: int = 600   # Ziel-Chunk-Größe in Wörtern
    chunk_max_size: int = 1000     # Max Chunk-Größe
    memory_limit_mb: int = 512     # Memory-Limit
    rate_limit_delay: float = 0.5  # Delay zwischen API-Calls
    enable_parallel: bool = True   # Parallele Verarbeitung aktivieren


@dataclass  
class BatchProcessingResult:
    """Ergebnis der Batch-Verarbeitung"""
    chunks_processed: int
    chunks_failed: int
    total_suggestions: int
    processing_time: float
    peak_memory_mb: float
    api_calls_total: int
    throughput_chunks_per_sec: float
    success_rate: float


class OptimizedBatchProcessor:
    """
    Optimierter Batch Processor für große Dokumente
    
    Features:
    - Memory-bewusste Verarbeitung
    - Optionale Parallelisierung
    - Intelligente Chunk-Aufteilung  
    - Performance-Monitoring
    - Graceful Error-Handling
    """
    
    def __init__(self, config: OptimizedBatchConfig = None):
        self.config = config or OptimizedBatchConfig()
        
        # Module initialisieren
        self.analyzer = AdvancedGeminiAnalyzer()
        self.chunker = AdvancedChunker(
            target_chunk_size=self.config.chunk_target_size,
            overlap_size=100,
            max_chunk_size=self.config.chunk_max_size
        )
        self.formatter = SmartCommentFormatter()
        
        # Performance-Tracking
        self.start_time = 0
        self.peak_memory = 0
        self.api_calls_made = 0
        
        # Setup Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('OptimizedBatchProcessor')
    
    def process_large_document(self, full_text: str, categories: List[str] = None) -> BatchProcessingResult:
        """
        Hauptfunktion für optimierte Verarbeitung großer Dokumente
        
        Args:
            full_text: Vollständiger Dokument-Text
            categories: Analyse-Kategorien (default: ['grammar', 'style', 'clarity', 'academic'])
            
        Returns:
            BatchProcessingResult mit Performance-Metriken
        """
        
        self.start_time = time.time()
        categories = categories or ['grammar', 'style', 'clarity', 'academic']
        
        self.logger.info(f"🚀 Starte optimierte Batch-Verarbeitung: {len(full_text):,} Zeichen")
        
        try:
            # 1. MEMORY CHECK und ADAPTIVE CONFIGURATION
            self._optimize_config_for_memory()
            
            # 2. INTELLIGENTE CHUNKING
            chunks = self._create_memory_optimized_chunks(full_text)
            self.logger.info(f"📊 {len(chunks)} Chunks erstellt (Ziel: {self.config.chunk_target_size} Wörter)")
            
            # 3. BATCH PROCESSING (parallel vs sequential)
            if self.config.enable_parallel and len(chunks) > 1:
                all_suggestions = self._process_chunks_parallel(chunks, categories)
            else:
                all_suggestions = self._process_chunks_sequential(chunks, categories)
            
            # 4. ERGEBNIS ERSTELLEN
            result = self._create_processing_result(len(chunks), all_suggestions)
            
            self.logger.info(f"✅ Batch-Verarbeitung erfolgreich: {result.total_suggestions} Suggestions in {result.processing_time:.1f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Batch-Verarbeitung fehlgeschlagen: {e}")
            return self._create_error_result(str(e))
    
    def _optimize_config_for_memory(self):
        """Optimiert Konfiguration basierend auf verfügbarem Memory"""
        
        available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
        current_memory_mb = self._get_current_memory_usage()
        
        self.logger.info(f"💾 Memory Status: {current_memory_mb:.1f} MB verwendet, {available_memory_mb:.0f} MB verfügbar")
        
        # Adaptive Konfiguration bei niedrigem Memory
        if available_memory_mb < self.config.memory_limit_mb:
            self.logger.warning(f"⚠️  Niedriges Memory - optimiere Konfiguration")
            
            # Reduziere Chunk-Größen
            self.config.chunk_target_size = min(400, self.config.chunk_target_size)
            self.config.chunk_max_size = min(600, self.config.chunk_max_size)
            
            # Reduziere Parallelität
            self.config.max_workers = 1
            self.config.enable_parallel = False
            
            self.logger.info(f"📉 Angepasst: {self.config.chunk_target_size} Wörter/Chunk, {self.config.max_workers} Worker")
    
    def _create_memory_optimized_chunks(self, full_text: str) -> List[TextChunk]:
        """Erstellt memory-optimierte Chunks mit kontinuierlichem Monitoring"""
        
        initial_memory = self._get_current_memory_usage()
        
        # Update Chunker mit optimierten Parametern
        self.chunker.target_chunk_size = self.config.chunk_target_size
        self.chunker.max_chunk_size = self.config.chunk_max_size
        
        chunks = self.chunker.create_intelligent_chunks(full_text, "academic")
        
        post_chunking_memory = self._get_current_memory_usage()
        memory_increase = post_chunking_memory - initial_memory
        
        self.peak_memory = max(self.peak_memory, post_chunking_memory)
        
        self.logger.info(f"💾 Chunking Memory-Impact: +{memory_increase:.1f} MB (Peak: {self.peak_memory:.1f} MB)")
        
        return chunks
    
    def _process_chunks_sequential(self, chunks: List[TextChunk], categories: List[str]) -> List:
        """Sequentielle Verarbeitung für memory-kritische Situationen"""
        
        self.logger.info(f"🔄 Sequentielle Verarbeitung von {len(chunks)} Chunks")
        
        all_suggestions = []
        processed = 0
        failed = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Memory-Check vor jeder Verarbeitung
                current_memory = self._get_current_memory_usage()
                self.peak_memory = max(self.peak_memory, current_memory)
                
                if current_memory > self.config.memory_limit_mb:
                    self.logger.warning(f"⚠️  Memory-Limit erreicht ({current_memory:.1f} MB) - überspringe Chunk {i+1}")
                    failed += 1
                    continue
                
                # Rate-Limiting
                if i > 0:
                    time.sleep(self.config.rate_limit_delay)
                
                # Chunk verarbeiten
                chunk_suggestions = self._process_single_chunk(chunk, categories, i)
                
                if chunk_suggestions is not None:
                    # Korrigiere Positionen
                    for suggestion in chunk_suggestions:
                        start, end = suggestion.position
                        suggestion.position = (start + chunk.start_pos, end + chunk.start_pos)
                    
                    all_suggestions.extend(chunk_suggestions)
                    processed += 1
                    
                    self.logger.debug(f"✅ Chunk {i+1}: {len(chunk_suggestions)} Suggestions")
                else:
                    failed += 1
                    self.logger.warning(f"❌ Chunk {i+1} fehlgeschlagen")
                
                # Progress-Update
                if (i + 1) % 5 == 0 or (i + 1) == len(chunks):
                    progress = (i + 1) / len(chunks) * 100
                    self.logger.info(f"📈 Progress: {progress:.1f}% ({i+1}/{len(chunks)}), Memory: {current_memory:.1f} MB")
                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei Chunk {i+1}: {e}")
                failed += 1
        
        self.logger.info(f"📊 Sequentielle Verarbeitung: {processed} erfolgreich, {failed} fehlgeschlagen")
        return all_suggestions
    
    def _process_chunks_parallel(self, chunks: List[TextChunk], categories: List[str]) -> List:
        """Parallele Verarbeitung für bessere Performance"""
        
        self.logger.info(f"⚡ Parallele Verarbeitung von {len(chunks)} Chunks mit {self.config.max_workers} Workers")
        
        all_suggestions = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit alle Chunk-Verarbeitungen
            future_to_chunk = {
                executor.submit(self._process_single_chunk, chunk, categories, i): (i, chunk)
                for i, chunk in enumerate(chunks)
            }
            
            processed = 0
            failed = 0
            
            # Sammle Ergebnisse
            for future in as_completed(future_to_chunk):
                chunk_index, chunk = future_to_chunk[future]
                
                try:
                    chunk_suggestions = future.result(timeout=30)  # 30s Timeout pro Chunk
                    
                    if chunk_suggestions is not None:
                        # Korrigiere Positionen
                        for suggestion in chunk_suggestions:
                            start, end = suggestion.position
                            suggestion.position = (start + chunk.start_pos, end + chunk.start_pos)
                        
                        all_suggestions.extend(chunk_suggestions)
                        processed += 1
                        
                        self.logger.debug(f"✅ Parallel Chunk {chunk_index+1}: {len(chunk_suggestions)} Suggestions")
                    else:
                        failed += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ Parallel Chunk {chunk_index+1} Fehler: {e}")
                    failed += 1
                
                # Progress-Update
                completed = processed + failed
                if completed % 3 == 0 or completed == len(chunks):
                    progress = completed / len(chunks) * 100
                    current_memory = self._get_current_memory_usage()
                    self.peak_memory = max(self.peak_memory, current_memory)
                    
                    self.logger.info(f"📈 Parallel Progress: {progress:.1f}% ({completed}/{len(chunks)}), Memory: {current_memory:.1f} MB")
        
        self.logger.info(f"📊 Parallele Verarbeitung: {processed} erfolgreich, {failed} fehlgeschlagen")
        return all_suggestions
    
    def _process_single_chunk(self, chunk: TextChunk, categories: List[str], chunk_index: int) -> Optional[List]:
        """Verarbeitet einen einzelnen Chunk"""
        
        try:
            # Rate-Limiting
            time.sleep(self.config.rate_limit_delay)
            
            # Multi-Pass-Analyse
            suggestions = self.analyzer.analyze_text_multipass(
                chunk.text,
                context=f"Chunk {chunk_index+1} aus Batch-Verarbeitung",
                categories=categories
            )
            
            self.api_calls_made += len(categories)
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ Einzelchunk-Verarbeitung Fehler: {e}")
            return None
    
    def _create_processing_result(self, total_chunks: int, all_suggestions: List) -> BatchProcessingResult:
        """Erstellt Verarbeitungs-Ergebnis mit Metriken"""
        
        processing_time = time.time() - self.start_time
        processed = len([s for s in all_suggestions if s is not None])
        failed = total_chunks - (processed if processed > 0 else 0)
        
        return BatchProcessingResult(
            chunks_processed=max(0, total_chunks - failed),
            chunks_failed=failed,
            total_suggestions=len(all_suggestions),
            processing_time=processing_time,
            peak_memory_mb=self.peak_memory,
            api_calls_total=self.api_calls_made,
            throughput_chunks_per_sec=total_chunks / processing_time if processing_time > 0 else 0,
            success_rate=(total_chunks - failed) / total_chunks * 100 if total_chunks > 0 else 0
        )
    
    def _create_error_result(self, error_msg: str) -> BatchProcessingResult:
        """Erstellt Fehler-Ergebnis"""
        
        processing_time = time.time() - self.start_time if self.start_time > 0 else 0
        
        return BatchProcessingResult(
            chunks_processed=0,
            chunks_failed=1,
            total_suggestions=0,
            processing_time=processing_time,
            peak_memory_mb=self._get_current_memory_usage(),
            api_calls_total=self.api_calls_made,
            throughput_chunks_per_sec=0,
            success_rate=0
        )
    
    def _get_current_memory_usage(self) -> float:
        """Aktuelle Memory-Usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """System und Performance-Statistics"""
        
        memory_info = psutil.virtual_memory()
        
        return {
            'system': {
                'total_memory_mb': memory_info.total / (1024 * 1024),
                'available_memory_mb': memory_info.available / (1024 * 1024),
                'memory_usage_percent': memory_info.percent
            },
            'process': {
                'current_memory_mb': self._get_current_memory_usage(),
                'peak_memory_mb': self.peak_memory,
                'api_calls_made': self.api_calls_made
            },
            'config': {
                'max_workers': self.config.max_workers,
                'chunk_target_size': self.config.chunk_target_size,
                'chunk_max_size': self.config.chunk_max_size,
                'parallel_enabled': self.config.enable_parallel
            }
        }


def main():
    """Test-Funktion für optimierten Batch Processor"""
    
    print("🧪 OPTIMIZED BATCH PROCESSOR - TEST")
    print("=" * 50)
    
    # Test-Konfiguration
    config = OptimizedBatchConfig(
        max_workers=2,
        chunk_target_size=300,  # Kleinere Chunks für mehr Parallelität
        enable_parallel=True,
        rate_limit_delay=0.2
    )
    
    # Erstelle Processor
    processor = OptimizedBatchProcessor(config)
    
    # Zeige System-Stats
    stats = processor.get_system_stats()
    print(f"💾 System Memory: {stats['system']['available_memory_mb']:.0f} MB verfügbar")
    print(f"⚙️  Konfiguration: {config.max_workers} Workers, {config.chunk_target_size} Wörter/Chunk")
    
    # Test mit realistischem Text
    test_text = ("Dies ist ein ausführlicher Test für die optimierte Batch-Verarbeitung von großen Dokumenten. " +
                "Der Text sollte verschiedene grammatikalische Strukturen und stilistische Elemente enthalten, " + 
                "um eine realistische KI-Analyse zu ermöglichen. ") * 50  # ~7500 Zeichen
    
    print(f"📄 Test-Text: {len(test_text):,} Zeichen")
    
    # Verarbeitung starten  
    result = processor.process_large_document(test_text, ['grammar', 'style'])
    
    # Ergebnisse anzeigen
    print(f"\n📊 BATCH-VERARBEITUNG ERGEBNIS:")
    print(f"   📝 Total Suggestions: {result.total_suggestions}")
    print(f"   ✅ Processed Chunks: {result.chunks_processed}")
    print(f"   ❌ Failed Chunks: {result.chunks_failed}")
    print(f"   ⏱️  Processing Time: {result.processing_time:.2f}s")
    print(f"   💾 Peak Memory: {result.peak_memory_mb:.1f} MB")
    print(f"   🌐 API Calls: {result.api_calls_total}")
    print(f"   🚀 Throughput: {result.throughput_chunks_per_sec:.2f} Chunks/Sek")
    print(f"   ✅ Success Rate: {result.success_rate:.1f}%")
    
    # Final System-Stats
    final_stats = processor.get_system_stats()
    print(f"\n📈 FINAL SYSTEM STATUS:")
    print(f"   💾 Process Memory: {final_stats['process']['current_memory_mb']:.1f} MB")
    print(f"   📊 System Memory Usage: {final_stats['system']['memory_usage_percent']:.1f}%")
    
    print(f"\n✅ OPTIMIZED BATCH PROCESSOR TEST ABGESCHLOSSEN")


if __name__ == "__main__":
    main()