"""
Sistema de Message Queue com Redis
Gerencia filas de processamento assíncronos
"""
import redis
import json
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import pickle

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Prioridades de tarefas"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """Status das tarefas"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class Task:
    """Tarefa para processamento"""
    id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = None
    scheduled_at: datetime = None
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.scheduled_at is None:
            self.scheduled_at = datetime.utcnow()

class MessageQueue:
    """Sistema de filas de mensagens com Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.redis_binary = redis.from_url(redis_url, decode_responses=False)
        
        # Configurações de filas
        self.queues = {
            TaskPriority.CRITICAL: "queue:critical",
            TaskPriority.HIGH: "queue:high", 
            TaskPriority.NORMAL: "queue:normal",
            TaskPriority.LOW: "queue:low"
        }
        
        # Filas especiais
        self.delayed_queue = "queue:delayed"
        self.processing_queue = "queue:processing"
        self.failed_queue = "queue:failed"
        self.completed_queue = "queue:completed"
        
        # Registry de handlers
        self.task_handlers: Dict[str, Callable] = {}
        
        # Worker status
        self.workers_running = False
        self.worker_threads = []
        
        # Métricas
        self.metrics = {
            'tasks_processed': 0,
            'tasks_failed': 0,
            'processing_time_total': 0.0,
            'start_time': datetime.utcnow()
        }
    
    def register_handler(self, task_type: str, handler: Callable):
        """Registrar handler para tipo de tarefa"""
        self.task_handlers[task_type] = handler
        logger.info(f"Handler registrado para {task_type}")
    
    def enqueue(self, task: Task) -> bool:
        """Adicionar tarefa à fila"""
        try:
            # Serializar tarefa
            task_data = {
                'id': task.id,
                'task_type': task.task_type,
                'payload': task.payload,
                'priority': task.priority.value,
                'max_retries': task.max_retries,
                'retry_count': task.retry_count,
                'created_at': task.created_at.isoformat(),
                'scheduled_at': task.scheduled_at.isoformat(),
                'status': task.status.value
            }
            
            # Determinar fila baseada na prioridade
            queue_name = self.queues[task.priority]
            
            # Se é agendada para o futuro, colocar na fila delayed
            if task.scheduled_at > datetime.utcnow():
                delay_seconds = (task.scheduled_at - datetime.utcnow()).total_seconds()
                self.redis_client.zadd(
                    self.delayed_queue,
                    {json.dumps(task_data): time.time() + delay_seconds}
                )
            else:
                # Adicionar à fila imediata
                self.redis_client.lpush(queue_name, json.dumps(task_data))
            
            # Salvar metadata da tarefa
            self.redis_client.hset(
                f"task:{task.id}",
                mapping=task_data
            )
            self.redis_client.expire(f"task:{task.id}", 86400)  # 24h TTL
            
            logger.info(f"Tarefa {task.id} adicionada à fila {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar tarefa à fila: {e}")
            return False
    
    def enqueue_bulk(self, tasks: List[Task]) -> int:
        """Adicionar múltiplas tarefas em lote"""
        success_count = 0
        
        with self.redis_client.pipeline() as pipe:
            for task in tasks:
                try:
                    task_data = json.dumps({
                        'id': task.id,
                        'task_type': task.task_type,
                        'payload': task.payload,
                        'priority': task.priority.value,
                        'max_retries': task.max_retries,
                        'retry_count': task.retry_count,
                        'created_at': task.created_at.isoformat(),
                        'scheduled_at': task.scheduled_at.isoformat(),
                        'status': task.status.value
                    })
                    
                    queue_name = self.queues[task.priority]
                    pipe.lpush(queue_name, task_data)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao preparar tarefa {task.id}: {e}")
            
            pipe.execute()
        
        logger.info(f"{success_count}/{len(tasks)} tarefas adicionadas em lote")
        return success_count
    
    def dequeue(self, timeout: int = 10) -> Optional[Task]:
        """Remover tarefa da fila para processamento"""
        try:
            # Tentar das filas por ordem de prioridade
            queue_names = [
                self.queues[TaskPriority.CRITICAL],
                self.queues[TaskPriority.HIGH],
                self.queues[TaskPriority.NORMAL],
                self.queues[TaskPriority.LOW]
            ]
            
            # Bloquear esperando por tarefa
            result = self.redis_client.brpop(queue_names, timeout=timeout)
            
            if not result:
                return None
            
            queue_name, task_data = result
            task_dict = json.loads(task_data)
            
            # Converter de volta para Task
            task = Task(
                id=task_dict['id'],
                task_type=task_dict['task_type'],
                payload=task_dict['payload'],
                priority=TaskPriority(task_dict['priority']),
                max_retries=task_dict['max_retries'],
                retry_count=task_dict['retry_count'],
                created_at=datetime.fromisoformat(task_dict['created_at']),
                scheduled_at=datetime.fromisoformat(task_dict['scheduled_at']),
                status=TaskStatus(task_dict['status'])
            )
            
            # Mover para fila de processamento
            task.status = TaskStatus.PROCESSING
            self._update_task_status(task)
            
            return task
            
        except Exception as e:
            logger.error(f"Erro ao remover tarefa da fila: {e}")
            return None
    
    def process_delayed_tasks(self):
        """Processar tarefas agendadas que estão prontas"""
        try:
            current_time = time.time()
            
            # Buscar tarefas prontas para execução
            ready_tasks = self.redis_client.zrangebyscore(
                self.delayed_queue, 
                0, 
                current_time,
                withscores=True
            )
            
            for task_data, score in ready_tasks:
                task_dict = json.loads(task_data)
                
                # Mover para fila apropriada
                priority = TaskPriority(task_dict['priority'])
                queue_name = self.queues[priority]
                
                with self.redis_client.pipeline() as pipe:
                    pipe.lpush(queue_name, task_data)
                    pipe.zrem(self.delayed_queue, task_data)
                    pipe.execute()
                
                logger.info(f"Tarefa agendada {task_dict['id']} movida para execução")
                
        except Exception as e:
            logger.error(f"Erro ao processar tarefas agendadas: {e}")
    
    def process_task(self, task: Task) -> bool:
        """Processar uma tarefa específica"""
        start_time = time.time()
        
        try:
            # Verificar se há handler registrado
            if task.task_type not in self.task_handlers:
                raise ValueError(f"Handler não encontrado para {task.task_type}")
            
            handler = self.task_handlers[task.task_type]
            
            # Executar handler
            logger.info(f"Processando tarefa {task.id} ({task.task_type})")
            result = handler(task.payload)
            
            # Marcar como completada
            task.status = TaskStatus.COMPLETED
            self._update_task_status(task)
            
            # Adicionar à fila de completadas
            self.redis_client.lpush(
                self.completed_queue,
                json.dumps({
                    'task_id': task.id,
                    'completed_at': datetime.utcnow().isoformat(),
                    'result': result
                })
            )
            
            # Atualizar métricas
            processing_time = time.time() - start_time
            self.metrics['tasks_processed'] += 1
            self.metrics['processing_time_total'] += processing_time
            
            logger.info(f"Tarefa {task.id} completada em {processing_time:.2f}s")
            return True
            
        except Exception as e:
            # Marcar como falhada
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            
            # Tentar retry se ainda há tentativas
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRY
                
                # Re-agendar com delay exponencial
                delay = min(300, 2 ** task.retry_count)  # Max 5 min
                task.scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
                
                self.enqueue(task)
                logger.warning(f"Tarefa {task.id} reagendada para retry {task.retry_count}")
            else:
                # Adicionar à fila de falhadas
                self.redis_client.lpush(
                    self.failed_queue,
                    json.dumps({
                        'task_id': task.id,
                        'failed_at': datetime.utcnow().isoformat(),
                        'error': str(e),
                        'retry_count': task.retry_count
                    })
                )
                
                self.metrics['tasks_failed'] += 1
                logger.error(f"Tarefa {task.id} falhou definitivamente: {e}")
            
            self._update_task_status(task)
            return False
    
    def _update_task_status(self, task: Task):
        """Atualizar status da tarefa no Redis"""
        try:
            task_data = {
                'status': task.status.value,
                'retry_count': task.retry_count,
                'error_message': task.error_message or '',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.redis_client.hset(f"task:{task.id}", mapping=task_data)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status da tarefa {task.id}: {e}")
    
    def start_workers(self, num_workers: int = 4):
        """Iniciar workers para processar filas"""
        if self.workers_running:
            logger.warning("Workers já estão executando")
            return
        
        self.workers_running = True
        logger.info(f"Iniciando {num_workers} workers")
        
        # Worker para tarefas agendadas
        delayed_worker = threading.Thread(
            target=self._delayed_task_worker,
            daemon=True
        )
        delayed_worker.start()
        self.worker_threads.append(delayed_worker)
        
        # Workers para processamento
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._task_worker,
                args=(f"worker-{i}",),
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
    
    def stop_workers(self):
        """Parar todos os workers"""
        self.workers_running = False
        logger.info("Parando workers...")
        
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        self.worker_threads.clear()
        logger.info("Workers parados")
    
    def _task_worker(self, worker_id: str):
        """Loop principal do worker"""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.workers_running:
            try:
                task = self.dequeue(timeout=5)
                if task:
                    self.process_task(task)
                
            except Exception as e:
                logger.error(f"Erro no worker {worker_id}: {e}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} parado")
    
    def _delayed_task_worker(self):
        """Worker para processar tarefas agendadas"""
        logger.info("Worker de tarefas agendadas iniciado")
        
        while self.workers_running:
            try:
                self.process_delayed_tasks()
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no worker de tarefas agendadas: {e}")
                time.sleep(30)
        
        logger.info("Worker de tarefas agendadas parado")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das filas"""
        stats = {}
        
        try:
            # Tamanho das filas
            for priority, queue_name in self.queues.items():
                stats[f"{priority.name.lower()}_queue_size"] = self.redis_client.llen(queue_name)
            
            # Filas especiais
            stats['delayed_queue_size'] = self.redis_client.zcard(self.delayed_queue)
            stats['processing_queue_size'] = self.redis_client.llen(self.processing_queue)
            stats['failed_queue_size'] = self.redis_client.llen(self.failed_queue)
            stats['completed_queue_size'] = self.redis_client.llen(self.completed_queue)
            
            # Métricas de performance
            uptime = (datetime.utcnow() - self.metrics['start_time']).total_seconds()
            avg_processing_time = (
                self.metrics['processing_time_total'] / max(1, self.metrics['tasks_processed'])
            )
            
            stats.update({
                'total_tasks_processed': self.metrics['tasks_processed'],
                'total_tasks_failed': self.metrics['tasks_failed'],
                'average_processing_time': round(avg_processing_time, 2),
                'tasks_per_minute': round(self.metrics['tasks_processed'] / max(1, uptime / 60), 2),
                'uptime_seconds': round(uptime, 2),
                'workers_running': len(self.worker_threads),
                'system_status': 'running' if self.workers_running else 'stopped'
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Obter status de uma tarefa específica"""
        try:
            task_data = self.redis_client.hgetall(f"task:{task_id}")
            if not task_data:
                return None
            
            return dict(task_data)
            
        except Exception as e:
            logger.error(f"Erro ao obter status da tarefa {task_id}: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancelar uma tarefa"""
        try:
            # Atualizar status para cancelada
            self.redis_client.hset(
                f"task:{task_id}",
                mapping={
                    'status': 'cancelled',
                    'cancelled_at': datetime.utcnow().isoformat()
                }
            )
            
            # Tentar remover das filas
            for queue_name in self.queues.values():
                # Esta operação é O(n) mas necessária para cancelamento
                tasks = self.redis_client.lrange(queue_name, 0, -1)
                for task_data in tasks:
                    task_dict = json.loads(task_data)
                    if task_dict['id'] == task_id:
                        self.redis_client.lrem(queue_name, 1, task_data)
                        logger.info(f"Tarefa {task_id} cancelada")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao cancelar tarefa {task_id}: {e}")
            return False
    
    def purge_completed_tasks(self, older_than_hours: int = 24):
        """Limpar tarefas completadas antigas"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Remover tarefas da fila de completadas
            completed_tasks = self.redis_client.lrange(self.completed_queue, 0, -1)
            removed_count = 0
            
            for task_data in completed_tasks:
                task_dict = json.loads(task_data)
                completed_at = datetime.fromisoformat(task_dict['completed_at'])
                
                if completed_at < cutoff_time:
                    self.redis_client.lrem(self.completed_queue, 1, task_data)
                    # Remover metadata também
                    self.redis_client.delete(f"task:{task_dict['task_id']}")
                    removed_count += 1
            
            logger.info(f"Removidas {removed_count} tarefas completadas antigas")
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar tarefas antigas: {e}")
            return 0

# Handlers de exemplo para diferentes tipos de tarefa
class TaskHandlers:
    """Handlers para diferentes tipos de tarefa"""
    
    @staticmethod
    def process_document_analysis(payload: Dict) -> Dict:
        """Processar análise de documento"""
        document_id = payload.get('document_id')
        analysis_type = payload.get('analysis_type', 'basic')
        
        # Simular processamento
        time.sleep(2)
        
        return {
            'document_id': document_id,
            'analysis_type': analysis_type,
            'result': 'Document analyzed successfully',
            'score': 0.95
        }
    
    @staticmethod
    def generate_document(payload: Dict) -> Dict:
        """Gerar documento"""
        template_id = payload.get('template_id')
        variables = payload.get('variables', {})
        
        # Simular geração
        time.sleep(3)
        
        return {
            'template_id': template_id,
            'document_url': f'/documents/generated_{int(time.time())}.pdf',
            'variables_used': len(variables)
        }
    
    @staticmethod
    def send_notification(payload: Dict) -> Dict:
        """Enviar notificação"""
        recipient = payload.get('recipient')
        message = payload.get('message')
        notification_type = payload.get('type', 'email')
        
        # Simular envio
        time.sleep(1)
        
        return {
            'recipient': recipient,
            'type': notification_type,
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        }

# Exemplo de uso
def example_usage():
    """Exemplo de como usar o sistema de filas"""
    
    # Inicializar fila
    queue = MessageQueue()
    
    # Registrar handlers
    queue.register_handler('document_analysis', TaskHandlers.process_document_analysis)
    queue.register_handler('document_generation', TaskHandlers.generate_document)
    queue.register_handler('notification', TaskHandlers.send_notification)
    
    # Iniciar workers
    queue.start_workers(num_workers=3)
    
    # Adicionar algumas tarefas
    tasks = [
        Task(
            id=f"task_{i}",
            task_type='document_analysis',
            payload={'document_id': f'doc_{i}', 'analysis_type': 'full'},
            priority=TaskPriority.HIGH if i % 2 == 0 else TaskPriority.NORMAL
        )
        for i in range(10)
    ]
    
    # Adicionar tarefas à fila
    for task in tasks:
        queue.enqueue(task)
    
    # Aguardar processamento
    time.sleep(30)
    
    # Obter estatísticas
    stats = queue.get_queue_stats()
    print("Estatísticas da fila:", json.dumps(stats, indent=2))
    
    # Parar workers
    queue.stop_workers()

if __name__ == "__main__":
    example_usage() 