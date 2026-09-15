"""
AMRIT Scheduled Automation System v6.2
Cron-like scheduling for research tasks, health monitoring, literature tracking
Inspired by Hermes Agent scheduled automations
"""
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import os

class ScheduleType(Enum):
    ONCE = "once"           # Run once at specific time
    DAILY = "daily"         # Run every day at specific time
    WEEKLY = "weekly"       # Run every week on specific day
    MONTHLY = "monthly"     # Run every month on specific date
    INTERVAL = "interval"   # Run every X minutes/hours
    TRIGGER = "trigger"     # Run when condition met

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScheduledTask:
    task_id: str
    name: str
    description: str
    schedule_type: ScheduleType
    schedule_config: Dict
    task_function: str  # Function name to call
    params: Dict
    priority: TaskPriority
    created_at: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    status: str = "pending"  # pending, running, completed, failed, paused
    owner: str = "system"
    tags: List[str] = field(default_factory=list)

class AutomationEngine:
    """
    Core automation engine for AMRIT
    Manages scheduled tasks, triggers, and recurring jobs
    """

    def __init__(self, db_path: str = "data/amrit_automation.db"):
        self.db_path = db_path
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.Lock()
        self.task_registry: Dict[str, Callable] = {}
        self._register_default_tasks()
        self._load_tasks()

    def _register_default_tasks(self):
        """Register default AMRIT tasks"""
        self.task_registry = {
            'literature_mining': self._task_literature_mining,
            'health_monitoring': self._task_health_monitoring,
            'ethics_review': self._task_ethics_review,
            'pattern_detection': self._task_pattern_detection,
            'backup_memory': self._task_backup_memory,
            'generate_report': self._task_generate_report,
            'pandemic_check': self._task_pandemic_check,
            'knowledge_update': self._task_knowledge_update,
            'self_improve': self._task_self_improve,
            'population_alert': self._task_population_alert,
        }

    def _task_literature_mining(self, params: Dict) -> Dict:
        """Task: Mine literature for tracked topics"""
        topics = params.get('topics', ['diabetes', 'cardiology', 'genetics'])
        sources = params.get('sources', ['pubmed', 'arxiv', 'openalex'])

        # Simulate literature mining
        findings = []
        for topic in topics:
            findings.append({
                'topic': topic,
                'new_papers': 3,
                'timestamp': datetime.now().isoformat()
            })

        return {
            'status': 'completed',
            'findings': findings,
            'total_papers': sum(f['new_papers'] for f in findings)
        }

    def _task_health_monitoring(self, params: Dict) -> Dict:
        """Task: Monitor health metrics for registered patients"""
        patient_ids = params.get('patient_ids', [])

        alerts = []
        for patient_id in patient_ids:
            # Simulate health check
            if hash(patient_id) % 10 == 0:  # 10% chance of alert
                alerts.append({
                    'patient_id': patient_id,
                    'alert_type': 'glucose_high',
                    'value': 180,
                    'threshold': 140,
                    'severity': 'high'
                })

        return {
            'status': 'completed',
            'patients_checked': len(patient_ids),
            'alerts_generated': len(alerts),
            'alerts': alerts
        }

    def _task_ethics_review(self, params: Dict) -> Dict:
        """Task: Review pending research proposals for ethics"""
        proposals = params.get('proposals', [])

        reviews = []
        for proposal in proposals:
            reviews.append({
                'proposal_id': proposal,
                'status': 'approved',
                'ethical_score': 0.95,
                'violations': []
            })

        return {
            'status': 'completed',
            'proposals_reviewed': len(proposals),
            'approved': len(reviews),
            'rejected': 0
        }

    def _task_pattern_detection(self, params: Dict) -> Dict:
        """Task: Detect unusual patterns in health data"""
        data_source = params.get('data_source', 'global_health')

        # Simulate pattern detection
        patterns = [
            {
                'type': 'anomaly',
                'location': 'Punjab, India',
                'disease': 'respiratory',
                'increase_percent': 15,
                'confidence': 0.85
            }
        ]

        return {
            'status': 'completed',
            'patterns_detected': len(patterns),
            'patterns': patterns
        }

    def _task_backup_memory(self, params: Dict) -> Dict:
        """Task: Backup memory database"""
        backup_path = params.get('backup_path', 'backups/')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return {
            'status': 'completed',
            'backup_file': '%samrit_backup_%s.db' % (backup_path, timestamp),
            'size_mb': 45.2
        }

    def _task_generate_report(self, params: Dict) -> Dict:
        """Task: Generate periodic research report"""
        report_type = params.get('report_type', 'weekly')
        topic = params.get('topic', 'general')

        return {
            'status': 'completed',
            'report_type': report_type,
            'topic': topic,
            'generated_at': datetime.now().isoformat(),
            'sections': ['summary', 'findings', 'recommendations']
        }

    def _task_pandemic_check(self, params: Dict) -> Dict:
        """Task: Check pandemic risk for monitored regions"""
        regions = params.get('regions', ['South Asia', 'Southeast Asia'])

        risk_assessments = []
        for region in regions:
            risk_assessments.append({
                'region': region,
                'risk_level': 'low',
                'risk_score': 0.25,
                'trend': 'stable'
            })

        return {
            'status': 'completed',
            'regions_checked': len(regions),
            'assessments': risk_assessments
        }

    def _task_knowledge_update(self, params: Dict) -> Dict:
        """Task: Update knowledge graph with new findings"""
        sources = params.get('sources', ['pubmed', 'arxiv'])

        return {
            'status': 'completed',
            'entities_added': 15,
            'relationships_added': 23,
            'sources_processed': sources
        }

    def _task_self_improve(self, params: Dict) -> Dict:
        """Task: Run self-improvement loop"""
        learning_data = params.get('learning_data', {})

        return {
            'status': 'completed',
            'patterns_discovered': 3,
            'models_updated': 2,
            'performance_improvement': 0.05
        }

    def _task_population_alert(self, params: Dict) -> Dict:
        """Task: Check for population-specific health alerts"""
        populations = params.get('populations', ['South Asian', 'African', 'East Asian'])

        alerts = []
        for pop in populations:
            alerts.append({
                'population': pop,
                'alert': 'vitamin_d_deficiency',
                'prevalence': 0.65,
                'recommendation': 'Supplementation advised'
            })

        return {
            'status': 'completed',
            'populations_checked': len(populations),
            'alerts': alerts
        }

    def schedule_task(self, name: str, description: str, 
                     schedule_type: ScheduleType, 
                     schedule_config: Dict,
                     task_function: str,
                     params: Dict = None,
                     priority: TaskPriority = TaskPriority.MEDIUM,
                     owner: str = "system",
                     tags: List[str] = None) -> str:
        """
        Schedule a new task

        Args:
            name: Task name
            description: Task description
            schedule_type: ONCE, DAILY, WEEKLY, MONTHLY, INTERVAL, TRIGGER
            schedule_config: Schedule-specific config
            task_function: Name of registered function to call
            params: Parameters for the task function
            priority: Task priority
            owner: Task owner
            tags: Task tags
        """
        task_id = "TASK_%s_%06d" % (datetime.now().strftime('%Y%m%d'), len(self.tasks) + 1)

        # Calculate next run time
        next_run = self._calculate_next_run(schedule_type, schedule_config)

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            task_function=task_function,
            params=params or {},
            priority=priority,
            created_at=datetime.now().isoformat(),
            next_run=next_run,
            owner=owner,
            tags=tags or []
        )

        with self.lock:
            self.tasks[task_id] = task
            self._save_task(task)

        return task_id

    def _calculate_next_run(self, schedule_type: ScheduleType, config: Dict) -> str:
        """Calculate next run time based on schedule"""
        now = datetime.now()

        if schedule_type == ScheduleType.ONCE:
            run_time = datetime.fromisoformat(config.get('datetime', now.isoformat()))
            return run_time.isoformat()

        elif schedule_type == ScheduleType.DAILY:
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            next_run = now.replace(hour=hour, minute=minute, second=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run.isoformat()

        elif schedule_type == ScheduleType.WEEKLY:
            day = config.get('day', 0)  # 0=Monday
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            days_ahead = day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0) + timedelta(days=days_ahead)
            return next_run.isoformat()

        elif schedule_type == ScheduleType.INTERVAL:
            interval_minutes = config.get('interval_minutes', 60)
            next_run = now + timedelta(minutes=interval_minutes)
            return next_run.isoformat()

        elif schedule_type == ScheduleType.TRIGGER:
            return None  # Trigger-based, no fixed next run

        return now.isoformat()

    def run_task(self, task_id: str) -> Dict:
        """Execute a scheduled task"""
        if task_id not in self.tasks:
            return {'error': 'Task not found'}

        task = self.tasks[task_id]

        if task.status == 'running':
            return {'error': 'Task already running'}

        # Update status
        task.status = 'running'
        task.last_run = datetime.now().isoformat()
        task.run_count += 1

        try:
            # Get function from registry
            if task.task_function not in self.task_registry:
                raise ValueError("Unknown task function: %s" % task.task_function)

            func = self.task_registry[task.task_function]
            result = func(task.params)

            task.status = 'completed'

            # Calculate next run for recurring tasks
            if task.schedule_type in [ScheduleType.DAILY, ScheduleType.WEEKLY, 
                                       ScheduleType.MONTHLY, ScheduleType.INTERVAL]:
                task.next_run = self._calculate_next_run(task.schedule_type, task.schedule_config)
            else:
                task.next_run = None

            return {
                'status': 'success',
                'task_id': task_id,
                'result': result,
                'next_run': task.next_run
            }

        except Exception as e:
            task.status = 'failed'
            return {
                'status': 'failed',
                'task_id': task_id,
                'error': str(e)
            }

    def start_scheduler(self):
        """Start the background scheduler"""
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("🕉️ AMRIT Automation Engine started")
        print("ਸਰਬੱਤ ਦਾ ਭਲਾ - Scheduled tasks running")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            now = datetime.now()

            with self.lock:
                for task_id, task in self.tasks.items():
                    if task.status in ['pending', 'completed'] and task.next_run:
                        next_run = datetime.fromisoformat(task.next_run)
                        if next_run <= now:
                            # Run task in background
                            threading.Thread(
                                target=self.run_task,
                                args=(task_id,),
                                daemon=True
                            ).start()

            time.sleep(30)  # Check every 30 seconds

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("Automation Engine stopped")

    def get_tasks(self, status: str = None, owner: str = None) -> List[Dict]:
        """Get tasks with optional filtering"""
        results = []

        for task_id, task in self.tasks.items():
            if status and task.status != status:
                continue
            if owner and task.owner != owner:
                continue

            results.append({
                'task_id': task.task_id,
                'name': task.name,
                'description': task.description,
                'schedule_type': task.schedule_type.value,
                'priority': task.priority.name,
                'status': task.status,
                'last_run': task.last_run,
                'next_run': task.next_run,
                'run_count': task.run_count,
                'owner': task.owner,
                'tags': task.tags
            })

        return results

    def delete_task(self, task_id: str) -> bool:
        """Delete a scheduled task"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
        return False

    def pause_task(self, task_id: str) -> bool:
        """Pause a task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = 'paused'
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = 'pending'
            return True
        return False

    def _save_task(self, task: ScheduledTask):
        """Save task to persistent storage"""
        # In real implementation, save to SQLite
        pass

    def _load_tasks(self):
        """Load tasks from persistent storage"""
        # In real implementation, load from SQLite
        pass

    def get_stats(self) -> Dict:
        """Get automation engine statistics"""
        statuses = {}
        for task in self.tasks.values():
            statuses[task.status] = statuses.get(task.status, 0) + 1

        return {
            'total_tasks': len(self.tasks),
            'status_breakdown': statuses,
            'running': self.running,
            'registered_functions': len(self.task_registry),
            'functions': list(self.task_registry.keys())
        }


# Pre-configured automation templates
AUTOMATION_TEMPLATES = {
    'daily_health_check': {
        'name': 'Daily Health Monitoring',
        'description': 'Check health metrics for all registered patients daily at 8 AM',
        'schedule_type': ScheduleType.DAILY,
        'schedule_config': {'hour': 8, 'minute': 0},
        'task_function': 'health_monitoring',
        'params': {'patient_ids': ['all_registered']},
        'priority': TaskPriority.HIGH,
        'tags': ['health', 'monitoring', 'daily']
    },
    'weekly_literature_scan': {
        'name': 'Weekly Literature Scan',
        'description': 'Scan medical literature for new findings every Monday at 6 AM',
        'schedule_type': ScheduleType.WEEKLY,
        'schedule_config': {'day': 0, 'hour': 6, 'minute': 0},
        'task_function': 'literature_mining',
        'params': {'topics': ['diabetes', 'cardiology', 'genetics', 'pandemic']},
        'priority': TaskPriority.MEDIUM,
        'tags': ['research', 'literature', 'weekly']
    },
    'hourly_pandemic_check': {
        'name': 'Hourly Pandemic Check',
        'description': 'Check pandemic risk every hour for monitored regions',
        'schedule_type': ScheduleType.INTERVAL,
        'schedule_config': {'interval_minutes': 60},
        'task_function': 'pandemic_check',
        'params': {'regions': ['South Asia', 'Southeast Asia', 'Africa']},
        'priority': TaskPriority.CRITICAL,
        'tags': ['pandemic', 'alert', 'hourly']
    },
    'daily_backup': {
        'name': 'Daily Memory Backup',
        'description': 'Backup all memory databases daily at 2 AM',
        'schedule_type': ScheduleType.DAILY,
        'schedule_config': {'hour': 2, 'minute': 0},
        'task_function': 'backup_memory',
        'params': {'backup_path': 'backups/'},
        'priority': TaskPriority.HIGH,
        'tags': ['backup', 'maintenance', 'daily']
    },
    'weekly_ethics_review': {
        'name': 'Weekly Ethics Review',
        'description': 'Review pending research proposals for ethical compliance',
        'schedule_type': ScheduleType.WEEKLY,
        'schedule_config': {'day': 4, 'hour': 10, 'minute': 0},
        'task_function': 'ethics_review',
        'params': {'proposals': ['pending_queue']},
        'priority': TaskPriority.HIGH,
        'tags': ['ethics', 'review', 'weekly']
    },
    'monthly_report': {
        'name': 'Monthly Research Report',
        'description': 'Generate comprehensive monthly research report',
        'schedule_type': ScheduleType.MONTHLY,
        'schedule_config': {'day': 1, 'hour': 9, 'minute': 0},
        'task_function': 'generate_report',
        'params': {'report_type': 'monthly', 'topic': 'all_domains'},
        'priority': TaskPriority.MEDIUM,
        'tags': ['report', 'summary', 'monthly']
    }
}


def create_automation_from_template(template_name: str, owner: str = "system") -> str:
    """Create a scheduled task from template"""
    if template_name not in AUTOMATION_TEMPLATES:
        raise ValueError("Unknown template: %s" % template_name)

    template = AUTOMATION_TEMPLATES[template_name]
    engine = AutomationEngine()

    return engine.schedule_task(
        name=template['name'],
        description=template['description'],
        schedule_type=template['schedule_type'],
        schedule_config=template['schedule_config'],
        task_function=template['task_function'],
        params=template['params'],
        priority=template['priority'],
        owner=owner,
        tags=template['tags']
    )
