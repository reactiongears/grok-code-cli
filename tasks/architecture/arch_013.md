# Architecture: Task 013 - Implement Monitoring and Metrics System

## Overview
This task implements a comprehensive monitoring and metrics system that tracks technical metrics, user experience metrics, system health, and provides automated alerting with performance analytics and reporting capabilities.

## Technical Scope

### Files to Modify
- `grok/monitoring/` - New monitoring system package
- `grok/metrics/` - New metrics collection system
- `grok/alerting/` - New alerting system
- `grok/dashboard/` - New dashboard system

### Dependencies
- Task 012 (Testing Framework) - Required for monitoring test integration
- Task 006 (Error Handling) - Required for error metrics
- Task 005 (Network Tools) - Required for external metrics reporting

## Implementation Details

### Phase 1: Metrics Collection System

#### Create `grok/metrics/collector.py`
```python
"""
Metrics collection system for Grok CLI
"""

import time
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
import psutil
import functools

from ..error_handling import ErrorHandler, ErrorCategory

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str]
    unit: str = ""

@dataclass
class Counter:
    """Counter metric for counting events"""
    name: str
    count: int = 0
    labels: Dict[str, str] = None
    
    def inc(self, amount: int = 1):
        """Increment counter"""
        self.count += amount

@dataclass
class Gauge:
    """Gauge metric for current values"""
    name: str
    value: float = 0.0
    labels: Dict[str, str] = None
    
    def set(self, value: float):
        """Set gauge value"""
        self.value = value
    
    def inc(self, amount: float = 1.0):
        """Increment gauge"""
        self.value += amount
    
    def dec(self, amount: float = 1.0):
        """Decrement gauge"""
        self.value -= amount

@dataclass
class Histogram:
    """Histogram metric for timing and distribution"""
    name: str
    buckets: List[float]
    counts: List[int]
    sum: float = 0.0
    count: int = 0
    labels: Dict[str, str] = None
    
    def observe(self, value: float):
        """Observe a value"""
        self.sum += value
        self.count += 1
        
        # Update buckets
        for i, bucket in enumerate(self.buckets):
            if value <= bucket:
                self.counts[i] += 1

class MetricsCollector:
    """Central metrics collection system"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.metrics = {}
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        
        # System metrics
        self.system_metrics_enabled = True
        self._start_system_metrics_collection()
        
        # Performance metrics
        self.performance_metrics = deque(maxlen=1000)
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def counter(self, name: str, labels: Dict[str, str] = None) -> Counter:
        """Get or create counter metric"""
        with self._lock:
            key = f"{name}:{labels or {}}"
            if key not in self.counters:
                self.counters[key] = Counter(name, labels=labels or {})
            return self.counters[key]
    
    def gauge(self, name: str, labels: Dict[str, str] = None) -> Gauge:
        """Get or create gauge metric"""
        with self._lock:
            key = f"{name}:{labels or {}}"
            if key not in self.gauges:
                self.gauges[key] = Gauge(name, labels=labels or {})
            return self.gauges[key]
    
    def histogram(self, name: str, buckets: List[float] = None, 
                 labels: Dict[str, str] = None) -> Histogram:
        """Get or create histogram metric"""
        if buckets is None:
            buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        
        with self._lock:
            key = f"{name}:{labels or {}}"
            if key not in self.histograms:
                self.histograms[key] = Histogram(
                    name, buckets, [0] * len(buckets), labels=labels or {}
                )
            return self.histograms[key]
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, unit: str = ""):
        """Record a metric"""
        with self._lock:
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                labels=labels or {},
                unit=unit
            )
            
            key = f"{name}:{labels or {}}"
            if key not in self.metrics:
                self.metrics[key] = deque(maxlen=100)
            self.metrics[key].append(metric)
    
    def record_performance(self, operation: str, duration: float, success: bool):
        """Record performance metric"""
        self.performance_metrics.append({
            'operation': operation,
            'duration': duration,
            'success': success,
            'timestamp': time.time()
        })
        
        # Update histogram
        hist = self.histogram(f"{operation}_duration", labels={'success': str(success)})
        hist.observe(duration)
        
        # Update counter
        counter = self.counter(f"{operation}_total", labels={'success': str(success)})
        counter.inc()
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get snapshot of all metrics"""
        with self._lock:
            snapshot = {
                'timestamp': time.time(),
                'counters': {k: asdict(v) for k, v in self.counters.items()},
                'gauges': {k: asdict(v) for k, v in self.gauges.items()},
                'histograms': {k: asdict(v) for k, v in self.histograms.items()},
                'metrics': {},
                'system': self._get_system_metrics(),
                'performance': list(self.performance_metrics)
            }
            
            # Get latest metrics
            for key, metric_deque in self.metrics.items():
                if metric_deque:
                    snapshot['metrics'][key] = asdict(metric_deque[-1])
            
            return snapshot
    
    def _start_system_metrics_collection(self):
        """Start system metrics collection thread"""
        def collect_system_metrics():
            while self.system_metrics_enabled:
                try:
                    # CPU usage
                    cpu_gauge = self.gauge("system_cpu_percent")
                    cpu_gauge.set(psutil.cpu_percent())
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    memory_gauge = self.gauge("system_memory_percent")
                    memory_gauge.set(memory.percent)
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    disk_gauge = self.gauge("system_disk_percent")
                    disk_gauge.set((disk.used / disk.total) * 100)
                    
                    # Network I/O
                    net_io = psutil.net_io_counters()
                    self.record_metric("system_network_bytes_sent", net_io.bytes_sent)
                    self.record_metric("system_network_bytes_recv", net_io.bytes_recv)
                    
                except Exception as e:
                    self.error_handler.handle_error(
                        e, ErrorCategory.SYSTEM, {"operation": "system_metrics"}
                    )
                
                time.sleep(30)  # Collect every 30 seconds
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            }
        except Exception:
            return {}

# Global metrics collector instance
metrics_collector = MetricsCollector()

def time_operation(operation_name: str):
    """Decorator to time operations"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_performance(operation_name, duration, success)
        
        return wrapper
    return decorator

def increment_counter(counter_name: str, labels: Dict[str, str] = None):
    """Increment a counter metric"""
    counter = metrics_collector.counter(counter_name, labels)
    counter.inc()

def set_gauge(gauge_name: str, value: float, labels: Dict[str, str] = None):
    """Set a gauge metric value"""
    gauge = metrics_collector.gauge(gauge_name, labels)
    gauge.set(value)

def observe_histogram(histogram_name: str, value: float, labels: Dict[str, str] = None):
    """Observe a value in histogram"""
    histogram = metrics_collector.histogram(histogram_name, labels=labels)
    histogram.observe(value)
```

#### Create `grok/metrics/exporters.py`
```python
"""
Metrics exporters for different monitoring systems
"""

import json
import time
from typing import Dict, Any, List
import requests
from pathlib import Path

from .collector import MetricsCollector
from ..error_handling import ErrorHandler, ErrorCategory

class PrometheusExporter:
    """Export metrics in Prometheus format"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.error_handler = ErrorHandler()
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        snapshot = self.collector.get_metrics_snapshot()
        prometheus_text = []
        
        # Export counters
        for key, counter in snapshot['counters'].items():
            labels_str = self._format_labels(counter['labels'])
            prometheus_text.append(
                f"# TYPE {counter['name']} counter"
            )
            prometheus_text.append(
                f"{counter['name']}{labels_str} {counter['count']}"
            )
        
        # Export gauges
        for key, gauge in snapshot['gauges'].items():
            labels_str = self._format_labels(gauge['labels'])
            prometheus_text.append(
                f"# TYPE {gauge['name']} gauge"
            )
            prometheus_text.append(
                f"{gauge['name']}{labels_str} {gauge['value']}"
            )
        
        # Export histograms
        for key, histogram in snapshot['histograms'].items():
            labels_str = self._format_labels(histogram['labels'])
            prometheus_text.append(
                f"# TYPE {histogram['name']} histogram"
            )
            
            # Buckets
            for i, bucket in enumerate(histogram['buckets']):
                bucket_labels = {**histogram['labels'], 'le': str(bucket)}
                bucket_labels_str = self._format_labels(bucket_labels)
                prometheus_text.append(
                    f"{histogram['name']}_bucket{bucket_labels_str} {histogram['counts'][i]}"
                )
            
            # Sum and count
            prometheus_text.append(
                f"{histogram['name']}_sum{labels_str} {histogram['sum']}"
            )
            prometheus_text.append(
                f"{histogram['name']}_count{labels_str} {histogram['count']}"
            )
        
        return '\n'.join(prometheus_text)
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus"""
        if not labels:
            return ""
        
        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"

class JSONExporter:
    """Export metrics in JSON format"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.error_handler = ErrorHandler()
    
    def export_metrics(self) -> str:
        """Export metrics in JSON format"""
        snapshot = self.collector.get_metrics_snapshot()
        return json.dumps(snapshot, indent=2)
    
    def save_to_file(self, file_path: str):
        """Save metrics to JSON file"""
        try:
            metrics_json = self.export_metrics()
            Path(file_path).write_text(metrics_json)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.FILE_SYSTEM, {"file_path": file_path}
            )

class InfluxDBExporter:
    """Export metrics to InfluxDB"""
    
    def __init__(self, collector: MetricsCollector, influxdb_url: str, 
                 database: str, username: str = None, password: str = None):
        self.collector = collector
        self.influxdb_url = influxdb_url
        self.database = database
        self.username = username
        self.password = password
        self.error_handler = ErrorHandler()
    
    def export_metrics(self):
        """Export metrics to InfluxDB"""
        try:
            snapshot = self.collector.get_metrics_snapshot()
            lines = []
            
            # Convert metrics to InfluxDB line protocol
            for key, counter in snapshot['counters'].items():
                line = self._create_line_protocol(
                    counter['name'], counter['labels'], {'count': counter['count']}
                )
                lines.append(line)
            
            for key, gauge in snapshot['gauges'].items():
                line = self._create_line_protocol(
                    gauge['name'], gauge['labels'], {'value': gauge['value']}
                )
                lines.append(line)
            
            # Send to InfluxDB
            self._send_to_influxdb('\n'.join(lines))
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.NETWORK, {"operation": "influxdb_export"}
            )
    
    def _create_line_protocol(self, measurement: str, tags: Dict[str, str], 
                             fields: Dict[str, float]) -> str:
        """Create InfluxDB line protocol"""
        # Tags
        tag_str = ','.join([f'{k}={v}' for k, v in tags.items()]) if tags else ''
        
        # Fields
        field_str = ','.join([f'{k}={v}' for k, v in fields.items()])
        
        # Timestamp
        timestamp = int(time.time() * 1000000000)  # Nanoseconds
        
        measurement_with_tags = f"{measurement},{tag_str}" if tag_str else measurement
        return f"{measurement_with_tags} {field_str} {timestamp}"
    
    def _send_to_influxdb(self, data: str):
        """Send data to InfluxDB"""
        url = f"{self.influxdb_url}/write?db={self.database}"
        
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)
        
        response = requests.post(url, data=data, auth=auth)
        response.raise_for_status()
```

### Phase 2: Monitoring Dashboard

#### Create `grok/dashboard/server.py`
```python
"""
Monitoring dashboard server for Grok CLI
"""

import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import threading

from ..metrics.collector import MetricsCollector
from ..metrics.exporters import PrometheusExporter, JSONExporter

class DashboardServer:
    """Monitoring dashboard web server"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        self.metrics_collector = metrics_collector
        self.prometheus_exporter = PrometheusExporter(metrics_collector)
        self.json_exporter = JSONExporter(metrics_collector)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """API endpoint for metrics data"""
            snapshot = self.metrics_collector.get_metrics_snapshot()
            return jsonify(snapshot)
        
        @self.app.route('/api/metrics/prometheus')
        def api_prometheus():
            """Prometheus metrics endpoint"""
            metrics_text = self.prometheus_exporter.export_metrics()
            return metrics_text, 200, {'Content-Type': 'text/plain'}
        
        @self.app.route('/api/system')
        def api_system():
            """System metrics endpoint"""
            system_metrics = self.metrics_collector._get_system_metrics()
            return jsonify(system_metrics)
        
        @self.app.route('/api/performance')
        def api_performance():
            """Performance metrics endpoint"""
            return jsonify(list(self.metrics_collector.performance_metrics))
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({'status': 'healthy', 'timestamp': time.time()})
    
    def start_server(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Start dashboard server"""
        def run_server():
            self.app.run(host=host, port=port, debug=debug)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print(f"Dashboard server started on http://{host}:{port}")
```

#### Create `grok/dashboard/templates/dashboard.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grok CLI Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2196F3;
        }
        .metric-label {
            color: #666;
            margin-bottom: 10px;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #4CAF50; }
        .status-warning { background-color: #FF9800; }
        .status-critical { background-color: #F44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Grok CLI Monitoring Dashboard</h1>
            <p>
                <span class="status-indicator status-healthy"></span>
                System Status: <span id="system-status">Healthy</span>
            </p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-value" id="cpu-usage">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Memory Usage</div>
                <div class="metric-value" id="memory-usage">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Active Conversations</div>
                <div class="metric-value" id="active-conversations">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">API Calls (Total)</div>
                <div class="metric-value" id="api-calls">-</div>
            </div>
        </div>

        <div class="metric-card">
            <h3>Performance Metrics</h3>
            <div class="chart-container">
                <canvas id="performance-chart"></canvas>
            </div>
        </div>

        <div class="metric-card">
            <h3>System Metrics</h3>
            <div class="chart-container">
                <canvas id="system-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Initialize charts
        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
        const systemCtx = document.getElementById('system-chart').getContext('2d');

        const performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        const systemChart = new Chart(systemCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    },
                    {
                        label: 'Memory %',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // Update metrics
        async function updateMetrics() {
            try {
                // Get system metrics
                const systemResponse = await fetch('/api/system');
                const systemData = await systemResponse.json();
                
                document.getElementById('cpu-usage').textContent = 
                    systemData.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = 
                    systemData.memory_percent.toFixed(1) + '%';

                // Get all metrics
                const metricsResponse = await fetch('/api/metrics');
                const metricsData = await metricsResponse.json();
                
                // Update counters
                const apiCallsCounter = Object.values(metricsData.counters)
                    .find(c => c.name === 'api_calls_total');
                if (apiCallsCounter) {
                    document.getElementById('api-calls').textContent = apiCallsCounter.count;
                }

                // Update charts
                updateCharts(systemData, metricsData);
                
            } catch (error) {
                console.error('Error updating metrics:', error);
            }
        }

        function updateCharts(systemData, metricsData) {
            const now = new Date().toLocaleTimeString();
            
            // Update system chart
            systemChart.data.labels.push(now);
            systemChart.data.datasets[0].data.push(systemData.cpu_percent);
            systemChart.data.datasets[1].data.push(systemData.memory_percent);
            
            // Keep last 20 data points
            if (systemChart.data.labels.length > 20) {
                systemChart.data.labels.shift();
                systemChart.data.datasets[0].data.shift();
                systemChart.data.datasets[1].data.shift();
            }
            
            systemChart.update();

            // Update performance chart with recent performance data
            if (metricsData.performance && metricsData.performance.length > 0) {
                const recentPerf = metricsData.performance.slice(-20);
                performanceChart.data.labels = recentPerf.map((_, i) => i);
                performanceChart.data.datasets[0].data = recentPerf.map(p => p.duration * 1000);
                performanceChart.update();
            }
        }

        // Update every 5 seconds
        setInterval(updateMetrics, 5000);
        updateMetrics(); // Initial load
    </script>
</body>
</html>
```

### Phase 3: Alerting System

#### Create `grok/alerting/system.py`
```python
"""
Alerting system for Grok CLI monitoring
"""

import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import requests

from ..metrics.collector import MetricsCollector
from ..error_handling import ErrorHandler, ErrorCategory

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert data structure"""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float
    labels: Dict[str, str]
    resolved: bool = False

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    description: str
    query: str  # Metric query
    condition: str  # e.g., "> 80"
    severity: AlertSeverity
    duration: float  # How long condition must be true
    labels: Dict[str, str]
    enabled: bool = True

class AlertManager:
    """Alert management system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.error_handler = ErrorHandler()
        
        # Alert storage
        self.active_alerts = {}
        self.alert_history = []
        self.alert_rules = {}
        
        # Notification channels
        self.notification_channels = {}
        
        # Alert evaluation
        self.evaluation_interval = 30  # seconds
        self.evaluation_thread = None
        self.running = False
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                description="High CPU usage detected",
                query="system_cpu_percent",
                condition="> 80",
                severity=AlertSeverity.WARNING,
                duration=60.0,
                labels={"type": "system"}
            ),
            AlertRule(
                name="high_memory_usage",
                description="High memory usage detected",
                query="system_memory_percent",
                condition="> 85",
                severity=AlertSeverity.WARNING,
                duration=60.0,
                labels={"type": "system"}
            ),
            AlertRule(
                name="critical_memory_usage",
                description="Critical memory usage detected",
                query="system_memory_percent",
                condition="> 95",
                severity=AlertSeverity.CRITICAL,
                duration=30.0,
                labels={"type": "system"}
            ),
            AlertRule(
                name="high_error_rate",
                description="High error rate detected",
                query="error_rate_percent",
                condition="> 10",
                severity=AlertSeverity.WARNING,
                duration=120.0,
                labels={"type": "application"}
            ),
            AlertRule(
                name="slow_response_time",
                description="Slow response time detected",
                query="avg_response_time",
                condition="> 5000",  # 5 seconds
                severity=AlertSeverity.WARNING,
                duration=180.0,
                labels={"type": "performance"}
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_rules[rule.name] = rule
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
    
    def add_notification_channel(self, name: str, channel_type: str, config: Dict[str, Any]):
        """Add notification channel"""
        self.notification_channels[name] = {
            'type': channel_type,
            'config': config
        }
    
    def start_monitoring(self):
        """Start alert monitoring"""
        if self.running:
            return
        
        self.running = True
        self.evaluation_thread = threading.Thread(target=self._evaluation_loop, daemon=True)
        self.evaluation_thread.start()
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        if self.evaluation_thread:
            self.evaluation_thread.join()
    
    def _evaluation_loop(self):
        """Main alert evaluation loop"""
        while self.running:
            try:
                self._evaluate_rules()
                time.sleep(self.evaluation_interval)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, {"operation": "alert_evaluation"}
                )
    
    def _evaluate_rules(self):
        """Evaluate all alert rules"""
        snapshot = self.metrics_collector.get_metrics_snapshot()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Get metric value
                metric_value = self._get_metric_value(snapshot, rule.query)
                if metric_value is None:
                    continue
                
                # Evaluate condition
                if self._evaluate_condition(metric_value, rule.condition):
                    self._handle_alert_condition_met(rule, metric_value)
                else:
                    self._handle_alert_condition_resolved(rule)
                    
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, {"rule": rule_name}
                )
    
    def _get_metric_value(self, snapshot: Dict[str, Any], query: str) -> Optional[float]:
        """Get metric value from snapshot"""
        # System metrics
        if query in snapshot['system']:
            return snapshot['system'][query]
        
        # Gauge metrics
        for key, gauge in snapshot['gauges'].items():
            if gauge['name'] == query:
                return gauge['value']
        
        # Calculate derived metrics
        if query == "error_rate_percent":
            return self._calculate_error_rate(snapshot)
        elif query == "avg_response_time":
            return self._calculate_avg_response_time(snapshot)
        
        return None
    
    def _calculate_error_rate(self, snapshot: Dict[str, Any]) -> float:
        """Calculate error rate percentage"""
        total_requests = 0
        error_requests = 0
        
        for key, counter in snapshot['counters'].items():
            if 'total' in counter['name']:
                total_requests += counter['count']
            elif 'error' in counter['name'] or counter['labels'].get('success') == 'False':
                error_requests += counter['count']
        
        if total_requests == 0:
            return 0.0
        
        return (error_requests / total_requests) * 100
    
    def _calculate_avg_response_time(self, snapshot: Dict[str, Any]) -> float:
        """Calculate average response time"""
        response_times = []
        
        for perf in snapshot.get('performance', []):
            response_times.append(perf['duration'] * 1000)  # Convert to ms
        
        if not response_times:
            return 0.0
        
        return sum(response_times) / len(response_times)
    
    def _evaluate_condition(self, value: float, condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            if condition.startswith('> '):
                threshold = float(condition[2:])
                return value > threshold
            elif condition.startswith('< '):
                threshold = float(condition[2:])
                return value < threshold
            elif condition.startswith('== '):
                threshold = float(condition[3:])
                return value == threshold
            elif condition.startswith('!= '):
                threshold = float(condition[3:])
                return value != threshold
            
            return False
        except ValueError:
            return False
    
    def _handle_alert_condition_met(self, rule: AlertRule, value: float):
        """Handle when alert condition is met"""
        alert_key = rule.name
        current_time = time.time()
        
        if alert_key not in self.active_alerts:
            # New alert condition
            self.active_alerts[alert_key] = {
                'rule': rule,
                'start_time': current_time,
                'value': value,
                'notified': False
            }
        else:
            # Update existing alert
            alert_info = self.active_alerts[alert_key]
            alert_info['value'] = value
            
            # Check if duration threshold is met
            if (current_time - alert_info['start_time'] >= rule.duration and 
                not alert_info['notified']):
                
                # Fire alert
                alert = Alert(
                    name=rule.name,
                    severity=rule.severity,
                    message=f"{rule.description}: {value}",
                    timestamp=current_time,
                    labels=rule.labels
                )
                
                self._fire_alert(alert)
                alert_info['notified'] = True
    
    def _handle_alert_condition_resolved(self, rule: AlertRule):
        """Handle when alert condition is resolved"""
        alert_key = rule.name
        
        if alert_key in self.active_alerts:
            alert_info = self.active_alerts[alert_key]
            
            if alert_info['notified']:
                # Send resolution notification
                alert = Alert(
                    name=rule.name,
                    severity=AlertSeverity.INFO,
                    message=f"{rule.description}: Resolved",
                    timestamp=time.time(),
                    labels=rule.labels,
                    resolved=True
                )
                
                self._fire_alert(alert)
            
            # Remove from active alerts
            del self.active_alerts[alert_key]
    
    def _fire_alert(self, alert: Alert):
        """Fire an alert through notification channels"""
        # Add to history
        self.alert_history.append(alert)
        
        # Send notifications
        for channel_name, channel in self.notification_channels.items():
            try:
                self._send_notification(channel, alert)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.NETWORK, {"channel": channel_name}
                )
    
    def _send_notification(self, channel: Dict[str, Any], alert: Alert):
        """Send notification through specific channel"""
        channel_type = channel['type']
        config = channel['config']
        
        if channel_type == 'email':
            self._send_email_notification(config, alert)
        elif channel_type == 'slack':
            self._send_slack_notification(config, alert)
        elif channel_type == 'webhook':
            self._send_webhook_notification(config, alert)
    
    def _send_email_notification(self, config: Dict[str, Any], alert: Alert):
        """Send email notification"""
        smtp_server = config['smtp_server']
        smtp_port = config['smtp_port']
        username = config['username']
        password = config['password']
        to_emails = config['to_emails']
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"
        
        body = f"""
Alert: {alert.name}
Severity: {alert.severity.value}
Message: {alert.message}
Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}
Labels: {alert.labels}
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_emails, msg.as_string())
    
    def _send_slack_notification(self, config: Dict[str, Any], alert: Alert):
        """Send Slack notification"""
        webhook_url = config['webhook_url']
        
        color = {
            AlertSeverity.INFO: 'good',
            AlertSeverity.WARNING: 'warning',
            AlertSeverity.CRITICAL: 'danger'
        }[alert.severity]
        
        payload = {
            'attachments': [
                {
                    'color': color,
                    'title': f"{alert.severity.value.upper()}: {alert.name}",
                    'text': alert.message,
                    'fields': [
                        {
                            'title': 'Time',
                            'value': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp)),
                            'short': True
                        }
                    ]
                }
            ]
        }
        
        requests.post(webhook_url, json=payload)
    
    def _send_webhook_notification(self, config: Dict[str, Any], alert: Alert):
        """Send webhook notification"""
        webhook_url = config['url']
        
        payload = {
            'alert': {
                'name': alert.name,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'labels': alert.labels,
                'resolved': alert.resolved
            }
        }
        
        requests.post(webhook_url, json=payload)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get current active alerts"""
        active = []
        for alert_info in self.active_alerts.values():
            if alert_info['notified']:
                alert = Alert(
                    name=alert_info['rule'].name,
                    severity=alert_info['rule'].severity,
                    message=f"{alert_info['rule'].description}: {alert_info['value']}",
                    timestamp=alert_info['start_time'],
                    labels=alert_info['rule'].labels
                )
                active.append(alert)
        return active
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
```

## Implementation Steps for Claude Code

### Step 1: Create Metrics Collection System
```
Task: Implement comprehensive metrics collection framework

Instructions:
1. Create grok/metrics/collector.py with MetricsCollector class
2. Implement Counter, Gauge, and Histogram metric types
3. Add system metrics collection (CPU, memory, disk)
4. Create performance metrics tracking
5. Test metrics collection and data integrity
```

### Step 2: Implement Metrics Exporters
```
Task: Create metrics exporters for various monitoring systems

Instructions:
1. Create grok/metrics/exporters.py with multiple export formats
2. Implement Prometheus metrics exporter
3. Implement JSON metrics exporter
4. Implement InfluxDB metrics exporter
5. Test export functionality with real monitoring systems
```

### Step 3: Build Monitoring Dashboard
```
Task: Create web-based monitoring dashboard

Instructions:
1. Create grok/dashboard/ package with Flask web server
2. Implement dashboard HTML template with charts
3. Create REST API endpoints for metrics data
4. Add real-time metrics visualization
5. Test dashboard functionality and responsiveness
```

### Step 4: Implement Alerting System
```
Task: Create comprehensive alerting and notification system

Instructions:
1. Create grok/alerting/system.py with AlertManager class
2. Implement alert rules and condition evaluation
3. Add notification channels (email, Slack, webhook)
4. Create alert history and management
5. Test alerting with various conditions and channels
```

### Step 5: Integration and Performance Optimization
```
Task: Integrate monitoring system and optimize performance

Instructions:
1. Integrate monitoring with existing Grok CLI components
2. Add monitoring decorators and instrumentation
3. Optimize metrics collection performance
4. Add configuration for monitoring settings
5. Test end-to-end monitoring functionality
```

## Testing Strategy

### Unit Tests
- Metrics collection accuracy
- Alert rule evaluation
- Notification channel functionality
- Dashboard API endpoints

### Integration Tests
- End-to-end monitoring workflow
- Real-time metrics collection
- Alert firing and resolution
- Dashboard visualization

### Performance Tests
- Metrics collection overhead
- Dashboard response times
- Alert evaluation performance
- Memory usage optimization

## Success Metrics
- Accurate metrics collection and reporting
- Reliable alert firing and resolution
- Responsive dashboard with real-time updates
- Minimal performance overhead (<5%)
- Comprehensive system visibility

## Next Steps
After completion of this task:
1. Complete system observability
2. Proactive issue detection and alerting
3. Performance monitoring and optimization
4. Foundation for operational excellence