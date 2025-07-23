#!/usr/bin/env python3
"""
Advanced Parallel Processor für optimierte Multi-Chunk-Analyse
Implementiert intelligente Parallelisierung mit Resource-Management
"""

import os
import sys
import time
import asyncio
import threading
import concurrent.futures
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from queue import Queue, Empty
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Import der Module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.memory_optimizer import MemoryOptimizer, MemoryConfig
from utils.advanced_chunking import TextChunk


@dataclass
class ParallelConfig:
    """Konfiguration für Parallel-Processing"""
    max_thread_workers: int = 3        # Max Thread-Workers
    max_process_workers: int = 2       # Max Process-Workers
    prefer_threads: bool = True        # Threads vs Processes
    chunk_batch_size: int = 5          # Chunks per Batch
    timeout_per_chunk: float = 45.0    # Timeout pro Chunk
    enable_memory_management: bool = True  # Memory-Management aktivieren
    load_balancing: str = "dynamic"    # static, dynamic, adaptive
    rate_limit_delay: float = 0.3      # Rate-Limiting zwischen Calls


@dataclass
class ParallelResult:
    """Ergebnis der parallelen Verarbeitung"""
    total_chunks: int
    processed_chunks: int
    failed_chunks: int
    total_processing_time: float
    avg_chunk_time: float
    throughput_chunks_per_sec: float
    worker_efficiency: Dict[str, float]
    parallelization_speedup: float


class WorkerPool:
    """Intelligenter Worker-Pool mit Load-Balancing"""
    
    def __init__(self, config: ParallelConfig):
        self.config = config
        self.thread_pool = None
        self.process_pool = None
        self.active_workers = 0
        self.completed_tasks = 0
        self.worker_stats = {}
        
        # Setup Logging
        self.logger = logging.getLogger('WorkerPool')
        
        # Initialisiere Pools
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialisiert Worker-Pools"""
        
        if self.config.prefer_threads:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_thread_workers)
            self.logger.info(f"🔧 Thread-Pool initialisiert: {self.config.max_thread_workers} Workers")
        else:
            self.process_pool = ProcessPoolExecutor(max_workers=self.config.max_process_workers)
            self.logger.info(f"🔧 Process-Pool initialisiert: {self.config.max_process_workers} Workers")
    
    def submit_task(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submitted Task an optimalen Worker-Pool"""
        
        if self.thread_pool:
            future = self.thread_pool.submit(func, *args, **kwargs)
        else:
            future = self.process_pool.submit(func, *args, **kwargs)
        
        self.active_workers += 1
        return future
    
    def shutdown(self, wait: bool = True):
        """Stoppt alle Worker-Pools"""
        
        if self.thread_pool:
            self.thread_pool.shutdown(wait=wait)
            self.logger.info("🛑 Thread-Pool gestoppt")
        
        if self.process_pool:
            self.process_pool.shutdown(wait=wait)
            self.logger.info("🛑 Process-Pool gestoppt")


class AdvancedParallelProcessor:
    """
    Advanced Parallel Processor für Multi-Chunk-Analyse
    
    Features:
    - Intelligente Worker-Pool-Verwaltung
    - Dynamic Load-Balancing
    - Memory-aware Parallelisierung
    - Adaptive Performance-Optimierung
    - Comprehensive Error-Handling
    """
    
    def __init__(self, config: ParallelConfig = None):
        self.config = config or ParallelConfig()
        
        # Worker-Pool
        self.worker_pool = WorkerPool(self.config)
        
        # Memory-Management
        if self.config.enable_memory_management:
            memory_config = MemoryConfig(
                max_memory_mb=1024,
                warning_threshold=0.75,
                enable_monitoring=True
            )
            self.memory_optimizer = MemoryOptimizer(memory_config)
        else:
            self.memory_optimizer = None
        
        # Performance-Tracking
        self.start_time = 0
        self.processing_times = []
        self.worker_efficiency = {}
        
        # Setup Logging
        self.logger = logging.getLogger('AdvancedParallelProcessor')
    
    def process_chunks_parallel(self, chunks: List[TextChunk], 
                              processing_func: Callable,
                              func_args: Tuple = ()) -> Tuple[List[Any], ParallelResult]:
        """
        Verarbeitet Chunks parallel mit optimierter Resource-Verwaltung
        
        Args:
            chunks: Liste der zu verarbeitenden Chunks
            processing_func: Funktion für Chunk-Verarbeitung
            func_args: Zusätzliche Argumente für processing_func
            
        Returns:
            Tuple aus (Ergebnisliste, Performance-Metriken)
        """
        
        self.start_time = time.time()
        self.logger.info(f"🚀 Starte parallele Verarbeitung: {len(chunks)} Chunks")
        
        try:
            # Memory-Context falls aktiviert
            if self.memory_optimizer:
                with self.memory_optimizer.memory_context("Parallel Processing"):
                    return self._execute_parallel_processing(chunks, processing_func, func_args)
            else:
                return self._execute_parallel_processing(chunks, processing_func, func_args)
                
        except Exception as e:
            self.logger.error(f"❌ Parallele Verarbeitung fehlgeschlagen: {e}")
            return [], self._create_error_result(len(chunks))
        
        finally:
            # Cleanup
            self.worker_pool.shutdown()
    
    def _execute_parallel_processing(self, chunks: List[TextChunk], 
                                   processing_func: Callable,
                                   func_args: Tuple) -> Tuple[List[Any], ParallelResult]:
        """Führt die eigentliche parallele Verarbeitung durch"""
        
        all_results = []
        futures_to_chunks = {}
        
        # Load-Balancing-Strategie
        if self.config.load_balancing == "dynamic":
            chunk_batches = self._create_dynamic_batches(chunks)
            self.logger.info(f"📊 Dynamic Load-Balancing: {len(chunk_batches)} Batches")
        else:
            chunk_batches = self._create_static_batches(chunks)
            self.logger.info(f"📊 Static Load-Balancing: {len(chunk_batches)} Batches")
        
        # Submit alle Batches
        for batch_id, chunk_batch in enumerate(chunk_batches):
            future = self.worker_pool.submit_task(
                self._process_chunk_batch,
                chunk_batch,
                processing_func,
                func_args,
                batch_id
            )
            futures_to_chunks[future] = (batch_id, chunk_batch)
        
        # Sammle Ergebnisse
        processed_chunks = 0
        failed_chunks = 0
        
        for future in as_completed(futures_to_chunks.keys()):
            batch_id, chunk_batch = futures_to_chunks[future]
            
            try:
                batch_result = future.result(timeout=self.config.timeout_per_chunk * len(chunk_batch))
                
                if batch_result['success']:
                    all_results.extend(batch_result['results'])
                    processed_chunks += len(chunk_batch)
                    
                    # Worker-Performance tracking
                    self._update_worker_stats(batch_id, batch_result['processing_time'], len(chunk_batch))
                    
                    self.logger.debug(f"✅ Batch {batch_id}: {len(chunk_batch)} Chunks in {batch_result['processing_time']:.2f}s")
                else:
                    failed_chunks += len(chunk_batch)
                    self.logger.warning(f"❌ Batch {batch_id} fehlgeschlagen: {batch_result['error']}")
                
            except concurrent.futures.TimeoutError:
                self.logger.error(f"⏰ Batch {batch_id} Timeout")
                failed_chunks += len(chunk_batch)
            except Exception as e:
                self.logger.error(f"❌ Batch {batch_id} Fehler: {e}")
                failed_chunks += len(chunk_batch)
        
        # Erstelle Performance-Result
        result = self._create_performance_result(
            len(chunks), processed_chunks, failed_chunks
        )
        
        self.logger.info(f"✅ Parallele Verarbeitung abgeschlossen: {processed_chunks}/{len(chunks)} erfolgreich")
        return all_results, result
    
    def _create_dynamic_batches(self, chunks: List[TextChunk]) -> List[List[TextChunk]]:
        """Erstellt dynamische Batches basierend auf Chunk-Eigenschaften"""
        
        # Sortiere Chunks nach Größe (kleinste zuerst für bessere Load-Balance)
        sorted_chunks = sorted(chunks, key=lambda c: len(c.text))
        
        batches = []
        current_batch = []
        current_batch_size = 0
        target_batch_size = self.config.chunk_batch_size
        
        for chunk in sorted_chunks:
            chunk_complexity = len(chunk.text) / 1000  # Approximierte Komplexität
            
            # Adaptive Batch-Größe basierend auf Komplexität
            if chunk_complexity > 2.0:  # Komplexer Chunk
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                batches.append([chunk])  # Komplexe Chunks einzeln verarbeiten
            else:
                current_batch.append(chunk)
                current_batch_size += 1
                
                if current_batch_size >= target_batch_size:
                    batches.append(current_batch)
                    current_batch = []
                    current_batch_size = 0
        
        # Letzten Batch hinzufügen
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _create_static_batches(self, chunks: List[TextChunk]) -> List[List[TextChunk]]:
        """Erstellt statische Batches mit fester Größe"""
        
        batch_size = self.config.chunk_batch_size
        batches = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def _process_chunk_batch(self, chunk_batch: List[TextChunk], 
                           processing_func: Callable,
                           func_args: Tuple,
                           batch_id: int) -> Dict[str, Any]:
        """Verarbeitet einen Batch von Chunks"""
        
        batch_start_time = time.time()
        
        try:
            batch_results = []
            
            for i, chunk in enumerate(chunk_batch):
                # Rate-Limiting
                if i > 0:
                    time.sleep(self.config.rate_limit_delay)
                
                # Memory-Check (falls verfügbar)
                if self.memory_optimizer:
                    current_memory = self.memory_optimizer._get_current_memory()
                    if current_memory > self.memory_optimizer.config.max_memory_mb * 0.9:
                        self.logger.warning(f"⚠️  Memory-Limit erreicht in Batch {batch_id}")
                        break
                
                # Verarbeite Chunk
                try:
                    result = processing_func(chunk, *func_args)
                    batch_results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ Chunk-Verarbeitung Fehler in Batch {batch_id}: {e}")
                    batch_results.append(None)
            
            processing_time = time.time() - batch_start_time
            
            return {
                'success': True,
                'results': batch_results,
                'processing_time': processing_time,
                'batch_id': batch_id,
                'chunks_processed': len(batch_results)
            }
            
        except Exception as e:
            processing_time = time.time() - batch_start_time
            return {
                'success': False,
                'results': [],
                'processing_time': processing_time,
                'batch_id': batch_id,
                'error': str(e),
                'chunks_processed': 0
            }
    
    def _update_worker_stats(self, worker_id: int, processing_time: float, chunks_processed: int):
        """Aktualisiert Worker-Performance-Statistiken"""
        
        if worker_id not in self.worker_efficiency:
            self.worker_efficiency[worker_id] = {
                'total_time': 0,
                'total_chunks': 0,
                'avg_time_per_chunk': 0
            }
        
        stats = self.worker_efficiency[worker_id]
        stats['total_time'] += processing_time
        stats['total_chunks'] += chunks_processed
        stats['avg_time_per_chunk'] = stats['total_time'] / stats['total_chunks']
        
        self.processing_times.append(processing_time)
    
    def _create_performance_result(self, total_chunks: int, 
                                 processed_chunks: int, 
                                 failed_chunks: int) -> ParallelResult:
        """Erstellt Performance-Result mit Metriken"""
        
        total_processing_time = time.time() - self.start_time
        
        # Berechnungen
        avg_chunk_time = (sum(self.processing_times) / len(self.processing_times)) if self.processing_times else 0
        throughput = processed_chunks / total_processing_time if total_processing_time > 0 else 0
        
        # Speedup-Berechnung (vereinfacht)
        sequential_estimate = avg_chunk_time * total_chunks
        parallelization_speedup = sequential_estimate / total_processing_time if total_processing_time > 0 else 1.0
        
        # Worker-Efficiency aufbereiten
        worker_efficiency_summary = {}
        for worker_id, stats in self.worker_efficiency.items():
            worker_efficiency_summary[f"worker_{worker_id}"] = stats['avg_time_per_chunk']
        
        return ParallelResult(
            total_chunks=total_chunks,
            processed_chunks=processed_chunks,
            failed_chunks=failed_chunks,
            total_processing_time=total_processing_time,
            avg_chunk_time=avg_chunk_time,
            throughput_chunks_per_sec=throughput,
            worker_efficiency=worker_efficiency_summary,
            parallelization_speedup=parallelization_speedup
        )
    
    def _create_error_result(self, total_chunks: int) -> ParallelResult:
        """Erstellt Error-Result bei kritischen Fehlern"""
        
        total_processing_time = time.time() - self.start_time if self.start_time > 0 else 0
        
        return ParallelResult(
            total_chunks=total_chunks,
            processed_chunks=0,
            failed_chunks=total_chunks,
            total_processing_time=total_processing_time,
            avg_chunk_time=0,
            throughput_chunks_per_sec=0,
            worker_efficiency={},
            parallelization_speedup=0
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Detaillierte Performance-Zusammenfassung"""
        
        return {
            'config': {
                'max_thread_workers': self.config.max_thread_workers,
                'max_process_workers': self.config.max_process_workers,
                'prefer_threads': self.config.prefer_threads,
                'chunk_batch_size': self.config.chunk_batch_size,
                'load_balancing': self.config.load_balancing
            },
            'worker_stats': self.worker_efficiency,
            'processing_times': self.processing_times,
            'memory_enabled': self.memory_optimizer is not None
        }


def simulate_chunk_processing(chunk: TextChunk, delay: float = 0.1) -> Dict[str, Any]:
    """Simulierte Chunk-Verarbeitung für Tests"""
    
    time.sleep(delay)  # Simuliere Verarbeitungszeit
    
    return {
        'chunk_length': len(chunk.text),
        'word_count': len(chunk.text.split()),
        'processing_time': delay,
        'success': True
    }


def main():
    """Test-Funktion für Advanced Parallel Processor"""
    
    print("🧪 ADVANCED PARALLEL PROCESSOR - TEST")
    print("=" * 50)
    
    # Test-Konfiguration
    config = ParallelConfig(
        max_thread_workers=3,
        chunk_batch_size=2,
        prefer_threads=True,
        load_balancing="dynamic",
        enable_memory_management=True
    )
    
    # Erstelle Processor
    processor = AdvancedParallelProcessor(config)
    
    # Erstelle Test-Chunks
    test_chunks = []
    for i in range(8):
        chunk_text = f"Das ist Test-Chunk {i+1}. " * (50 + i * 20)  # Variable Größen
        chunk = TextChunk(
            text=chunk_text,
            start_pos=i * 1000,
            end_pos=(i + 1) * 1000,
            chunk_type="test"
        )
        test_chunks.append(chunk)
    
    print(f"📊 Test-Setup: {len(test_chunks)} Chunks, {config.max_thread_workers} Workers")
    print(f"⚙️  Load-Balancing: {config.load_balancing}")
    
    # Parallele Verarbeitung
    print(f"\n🚀 Starte parallele Verarbeitung...")
    
    results, performance = processor.process_chunks_parallel(
        test_chunks,
        simulate_chunk_processing,
        (0.2,)  # 0.2s Delay pro Chunk
    )
    
    # Ergebnisse anzeigen
    print(f"\n📊 PARALLEL-PROCESSING ERGEBNISSE:")
    print(f"   📝 Total Results: {len(results)}")
    print(f"   ✅ Processed Chunks: {performance.processed_chunks}/{performance.total_chunks}")
    print(f"   ❌ Failed Chunks: {performance.failed_chunks}")
    print(f"   ⏱️  Total Time: {performance.total_processing_time:.2f}s")
    print(f"   📊 Avg Chunk Time: {performance.avg_chunk_time:.2f}s")
    print(f"   🚀 Throughput: {performance.throughput_chunks_per_sec:.2f} Chunks/Sek")
    print(f"   ⚡ Speedup: {performance.parallelization_speedup:.1f}x")
    
    # Worker-Efficiency
    if performance.worker_efficiency:
        print(f"\n👥 WORKER-EFFICIENCY:")
        for worker, efficiency in performance.worker_efficiency.items():
            print(f"   {worker}: {efficiency:.2f}s/Chunk")
    
    # Performance-Summary
    summary = processor.get_performance_summary()
    print(f"\n📈 PERFORMANCE-SUMMARY:")
    print(f"   🔧 Threading: {'Threads' if summary['config']['prefer_threads'] else 'Processes'}")
    print(f"   📦 Batch Size: {summary['config']['chunk_batch_size']}")
    print(f"   💾 Memory Management: {'Aktiviert' if summary['memory_enabled'] else 'Deaktiviert'}")
    print(f"   🔢 Processing Times: {len(summary['processing_times'])} Messungen")
    
    print(f"\n✅ ADVANCED PARALLEL PROCESSOR TEST ABGESCHLOSSEN")


if __name__ == "__main__":
    # Setup Logging für Test
    logging.basicConfig(level=logging.INFO)
    main()