#!/usr/bin/env python3
"""
Agent Management System for BFI Signals
Manages intelligent agents for various trading and analysis tasks
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import threading
import time
from dataclasses import dataclass
from enum import Enum

class AgentStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class AgentType(Enum):
    SIGNAL_ANALYZER = "signal_analyzer"
    MARKET_MONITOR = "market_monitor" 
    RISK_ASSESSOR = "risk_assessor"
    TREND_PREDICTOR = "trend_predictor"
    NEWS_ANALYZER = "news_analyzer"
    PORTFOLIO_OPTIMIZER = "portfolio_optimizer"
    ALERT_MANAGER = "alert_manager"

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    agent_type: AgentType
    description: str
    parameters: Dict[str, Any]
    schedule: Optional[str] = None  # Cron-like schedule
    max_concurrent_tasks: int = 1
    timeout_seconds: int = 300
    retry_count: int = 3
    priority: int = 5  # 1-10, higher is more priority

@dataclass
class AgentTask:
    """Task for an agent to execute"""
    id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3

class Agent:
    """Base agent class"""
    
    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.INACTIVE
        self.last_activity = datetime.now()
        self.current_tasks = []
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.average_execution_time = 0.0
        self.lock = threading.Lock()
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task - to be overridden by specific agent types"""
        raise NotImplementedError("Subclasses must implement execute_task")
    
    def can_accept_task(self) -> bool:
        """Check if agent can accept more tasks"""
        with self.lock:
            return (self.status == AgentStatus.ACTIVE and 
                   len(self.current_tasks) < self.config.max_concurrent_tasks)
    
    def start_task(self, task: AgentTask):
        """Start executing a task"""
        with self.lock:
            self.current_tasks.append(task)
            self.status = AgentStatus.BUSY
    
    def complete_task(self, task: AgentTask, success: bool = True):
        """Mark task as completed"""
        with self.lock:
            if task in self.current_tasks:
                self.current_tasks.remove(task)
            
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
            
            # Update status
            if len(self.current_tasks) == 0:
                self.status = AgentStatus.ACTIVE
            
            self.last_activity = datetime.now()

class SignalAnalyzerAgent(Agent):
    """Agent for analyzing trading signals"""
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Analyze signals and provide recommendations"""
        try:
            if task.task_type == "analyze_signal":
                symbol = task.parameters.get('symbol')
                signal_data = task.parameters.get('signal_data')
                
                # Simulate signal analysis
                analysis = {
                    'symbol': symbol,
                    'confidence': 0.75,
                    'recommendation': 'BUY',
                    'risk_level': 'MEDIUM',
                    'target_price': signal_data.get('current_price', 0) * 1.05,
                    'stop_loss': signal_data.get('current_price', 0) * 0.95,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                return {
                    'success': True,
                    'result': analysis,
                    'execution_time': 2.5
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }

class MarketMonitorAgent(Agent):
    """Agent for monitoring market conditions"""
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Monitor market conditions and detect anomalies"""
        try:
            if task.task_type == "monitor_market":
                symbols = task.parameters.get('symbols', [])
                timeframe = task.parameters.get('timeframe', '1h')
                
                # Simulate market monitoring
                market_status = {
                    'timestamp': datetime.now().isoformat(),
                    'overall_sentiment': 'BULLISH',
                    'volatility_index': 0.65,
                    'trending_symbols': symbols[:3],
                    'alerts': []
                }
                
                return {
                    'success': True,
                    'result': market_status,
                    'execution_time': 1.2
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }

class RiskAssessorAgent(Agent):
    """Agent for assessing trading risks"""
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Assess risk for trading positions"""
        try:
            if task.task_type == "assess_risk":
                portfolio = task.parameters.get('portfolio', {})
                new_position = task.parameters.get('new_position', {})
                
                # Simulate risk assessment
                risk_assessment = {
                    'overall_risk': 'MEDIUM',
                    'portfolio_var': 0.15,
                    'position_size_recommendation': 0.05,
                    'diversification_score': 0.75,
                    'risk_factors': [
                        'Market volatility elevated',
                        'Sector concentration detected'
                    ],
                    'assessment_timestamp': datetime.now().isoformat()
                }
                
                return {
                    'success': True,
                    'result': risk_assessment,
                    'execution_time': 1.8
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }

class AgentManager:
    """Manages all agents and task distribution"""
    
    def __init__(self, db_path='ai_learning.db'):
        self.db_path = db_path
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[AgentTask] = []
        self.running = False
        self.scheduler_thread = None
        self.init_database()
        self.load_agents()
    
    def init_database(self):
        """Initialize agent-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                description TEXT,
                config TEXT,
                status TEXT DEFAULT 'inactive',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                average_execution_time REAL DEFAULT 0.0
            )
        ''')
        
        # Agent tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                task_type TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                scheduled_for DATETIME,
                started_at DATETIME,
                completed_at DATETIME,
                result TEXT,
                error_message TEXT,
                execution_time REAL DEFAULT 0.0,
                priority INTEGER DEFAULT 5,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        ''')
        
        # Agent performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())
        
        # Create appropriate agent instance
        if config.agent_type == AgentType.SIGNAL_ANALYZER:
            agent = SignalAnalyzerAgent(agent_id, config)
        elif config.agent_type == AgentType.MARKET_MONITOR:
            agent = MarketMonitorAgent(agent_id, config)
        elif config.agent_type == AgentType.RISK_ASSESSOR:
            agent = RiskAssessorAgent(agent_id, config)
        else:
            agent = Agent(agent_id, config)  # Base agent
        
        self.agents[agent_id] = agent
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agents (id, name, agent_type, description, config, status, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent_id,
            config.name,
            config.agent_type.value,
            config.description,
            json.dumps(config.parameters),
            agent.status.value,
            agent.last_activity
        ))
        
        conn.commit()
        conn.close()
        
        return agent_id
    
    def load_agents(self):
        """Load agents from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM agents')
        agents_data = cursor.fetchall()
        conn.close()
        
        for agent_data in agents_data:
            agent_id = agent_data[0]
            name = agent_data[1]
            agent_type = AgentType(agent_data[2])
            description = agent_data[3]
            parameters = json.loads(agent_data[4]) if agent_data[4] else {}
            
            config = AgentConfig(
                name=name,
                agent_type=agent_type,
                description=description,
                parameters=parameters
            )
            
            # Create agent instance
            if agent_type == AgentType.SIGNAL_ANALYZER:
                agent = SignalAnalyzerAgent(agent_id, config)
            elif agent_type == AgentType.MARKET_MONITOR:
                agent = MarketMonitorAgent(agent_id, config)
            elif agent_type == AgentType.RISK_ASSESSOR:
                agent = RiskAssessorAgent(agent_id, config)
            else:
                agent = Agent(agent_id, config)
            
            # Set status to active for loaded agents
            agent.status = AgentStatus.ACTIVE
            self.agents[agent_id] = agent
    
    def submit_task(self, task: AgentTask) -> bool:
        """Submit a task to the appropriate agent"""
        # Find suitable agent
        suitable_agents = [
            agent for agent in self.agents.values()
            if agent.can_accept_task()
        ]
        
        if not suitable_agents:
            # Add to queue
            self.task_queue.append(task)
            return False
        
        # Select best agent (lowest current load)
        best_agent = min(suitable_agents, key=lambda a: len(a.current_tasks))
        
        # Assign task to agent
        self._execute_task_async(best_agent, task)
        return True
    
    def _execute_task_async(self, agent: Agent, task: AgentTask):
        """Execute task asynchronously"""
        def execute():
            start_time = time.time()
            
            # Update database - task started
            self._update_task_status(task.id, 'running', started_at=datetime.now())
            
            agent.start_task(task)
            
            try:
                result = agent.execute_task(task)
                execution_time = time.time() - start_time
                
                if result.get('success', False):
                    # Task completed successfully
                    self._update_task_status(
                        task.id, 'completed',
                        completed_at=datetime.now(),
                        result=json.dumps(result.get('result', {})),
                        execution_time=execution_time
                    )
                    agent.complete_task(task, success=True)
                else:
                    # Task failed
                    self._update_task_status(
                        task.id, 'failed',
                        completed_at=datetime.now(),
                        error_message=result.get('error', 'Unknown error'),
                        execution_time=execution_time
                    )
                    agent.complete_task(task, success=False)
                
            except Exception as e:
                execution_time = time.time() - start_time
                self._update_task_status(
                    task.id, 'failed',
                    completed_at=datetime.now(),
                    error_message=str(e),
                    execution_time=execution_time
                )
                agent.complete_task(task, success=False)
        
        # Start task in separate thread
        task_thread = threading.Thread(target=execute)
        task_thread.daemon = True
        task_thread.start()
    
    def _update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = ['status = ?']
        values = [status]
        
        for field, value in kwargs.items():
            update_fields.append(f'{field} = ?')
            values.append(value)
        
        values.append(task_id)
        
        query = f"UPDATE agent_tasks SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def create_task(self, agent_type: str, task_type: str, parameters: Dict[str, Any], 
                   priority: int = 5, scheduled_for: Optional[datetime] = None) -> str:
        """Create a new task"""
        task_id = str(uuid.uuid4())
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_tasks (id, task_type, parameters, priority, scheduled_for)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            task_id,
            task_type,
            json.dumps(parameters),
            priority,
            scheduled_for
        ))
        
        conn.commit()
        conn.close()
        
        # Create task object
        task = AgentTask(
            id=task_id,
            agent_id='',  # Will be assigned when executed
            task_type=task_type,
            parameters=parameters,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            priority=priority
        )
        
        # Try to submit immediately
        if not scheduled_for or scheduled_for <= datetime.now():
            self.submit_task(task)
        
        return task_id
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            'id': agent_id,
            'name': agent.config.name,
            'type': agent.config.agent_type.value,
            'status': agent.status.value,
            'current_tasks': len(agent.current_tasks),
            'completed_tasks': agent.completed_tasks,
            'failed_tasks': agent.failed_tasks,
            'last_activity': agent.last_activity.isoformat(),
            'average_execution_time': agent.average_execution_time
        }
    
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return [self.get_agent_status(agent_id) for agent_id in self.agents.keys()]
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent task execution history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent_id, task_type, status, created_at, completed_at, 
                   execution_time, error_message
            FROM agent_tasks 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        tasks = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': task[0],
                'agent_id': task[1],
                'task_type': task[2],
                'status': task[3],
                'created_at': task[4],
                'completed_at': task[5],
                'execution_time': task[6],
                'error_message': task[7]
            }
            for task in tasks
        ]
    
    def start_scheduler(self):
        """Start the task scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the task scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Process queued tasks
                if self.task_queue:
                    task = self.task_queue.pop(0)
                    if not self.submit_task(task):
                        # Put back if no agent available
                        self.task_queue.insert(0, task)
                
                # Check for scheduled tasks
                self._process_scheduled_tasks()
                
                # Update agent metrics
                self._update_agent_metrics()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(5)
    
    def _process_scheduled_tasks(self):
        """Process tasks scheduled for execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, task_type, parameters, priority
            FROM agent_tasks 
            WHERE status = 'pending' 
            AND (scheduled_for IS NULL OR scheduled_for <= ?)
            ORDER BY priority DESC, created_at ASC
            LIMIT 10
        ''', (datetime.now(),))
        
        tasks = cursor.fetchall()
        conn.close()
        
        for task_data in tasks:
            task = AgentTask(
                id=task_data[0],
                agent_id='',
                task_type=task_data[1],
                parameters=json.loads(task_data[2]),
                created_at=datetime.now(),
                priority=task_data[3]
            )
            
            self.submit_task(task)
    
    def _update_agent_metrics(self):
        """Update agent performance metrics"""
        for agent_id, agent in self.agents.items():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update agent status in database
            cursor.execute('''
                UPDATE agents 
                SET status = ?, last_activity = ?, completed_tasks = ?, failed_tasks = ?
                WHERE id = ?
            ''', (
                agent.status.value,
                agent.last_activity,
                agent.completed_tasks,
                agent.failed_tasks,
                agent_id
            ))
            
            conn.commit()
            conn.close()

# Initialize global agent manager
agent_manager = AgentManager()

def setup_default_agents():
    """Setup default agents"""
    # Signal Analyzer Agent
    signal_config = AgentConfig(
        name="Signal Analyzer Pro",
        agent_type=AgentType.SIGNAL_ANALYZER,
        description="Advanced trading signal analysis and recommendations",
        parameters={
            "confidence_threshold": 0.7,
            "risk_tolerance": "medium",
            "analysis_timeframes": ["1h", "4h", "1d"]
        },
        max_concurrent_tasks=3
    )
    
    # Market Monitor Agent
    market_config = AgentConfig(
        name="Market Monitor",
        agent_type=AgentType.MARKET_MONITOR,
        description="Real-time market condition monitoring",
        parameters={
            "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
            "alert_thresholds": {
                "volatility": 0.8,
                "volume_spike": 2.0
            }
        },
        max_concurrent_tasks=2
    )
    
    # Risk Assessor Agent
    risk_config = AgentConfig(
        name="Risk Assessor",
        agent_type=AgentType.RISK_ASSESSOR,
        description="Portfolio risk assessment and management",
        parameters={
            "max_portfolio_risk": 0.02,
            "position_sizing_method": "kelly",
            "risk_models": ["var", "expected_shortfall"]
        },
        max_concurrent_tasks=2
    )
    
    # Create agents if they don't exist
    if len(agent_manager.agents) == 0:
        agent_manager.create_agent(signal_config)
        agent_manager.create_agent(market_config)
        agent_manager.create_agent(risk_config)
        print("✅ Default agents created successfully")

# Setup default agents
setup_default_agents()