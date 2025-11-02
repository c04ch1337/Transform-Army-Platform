"""
Alert configuration and notification system.

Provides configurable alerting for system health issues including
threshold checks, notification channels, and alert suppression.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import json

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class AlertRule:
    """
    Configuration for an alert rule.
    
    Defines when and how to trigger alerts based on metrics
    or health check results.
    """
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable[[], bool]
    channels: List[AlertChannel]
    threshold: Optional[float] = None
    duration_seconds: int = 60
    enabled: bool = True
    suppression_seconds: int = 300  # 5 minutes default
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """An active or historical alert."""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "metadata": self.metadata
        }


class AlertManager:
    """
    Manages alert rules, evaluation, and notifications.
    
    Handles alert lifecycle including:
    - Rule evaluation
    - Alert triggering
    - Notification dispatch
    - Alert suppression
    - Alert history
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_until: Dict[str, float] = {}
        self._alert_id_counter = 0
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules."""
        
        # High error rate alert
        self.add_rule(AlertRule(
            name="high_error_rate",
            description="Error rate exceeds threshold",
            severity=AlertSeverity.ERROR,
            condition=lambda: False,  # Placeholder, will be set dynamically
            channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
            threshold=0.05,  # 5% error rate
            duration_seconds=60
        ))
        
        # Slow response time alert
        self.add_rule(AlertRule(
            name="slow_response_time",
            description="Average response time exceeds threshold",
            severity=AlertSeverity.WARNING,
            condition=lambda: False,
            channels=[AlertChannel.LOG],
            threshold=2000,  # 2 seconds in ms
            duration_seconds=120
        ))
        
        # Database connection pool exhaustion
        self.add_rule(AlertRule(
            name="db_pool_exhaustion",
            description="Database connection pool nearing capacity",
            severity=AlertSeverity.CRITICAL,
            condition=lambda: False,
            channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
            threshold=0.9,  # 90% utilization
            duration_seconds=30
        ))
        
        # High memory usage
        self.add_rule(AlertRule(
            name="high_memory_usage",
            description="Memory usage exceeds threshold",
            severity=AlertSeverity.WARNING,
            condition=lambda: False,
            channels=[AlertChannel.LOG],
            threshold=85.0,  # 85% memory usage
            duration_seconds=180
        ))
        
        # High CPU usage
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            description="CPU usage exceeds threshold",
            severity=AlertSeverity.WARNING,
            condition=lambda: False,
            channels=[AlertChannel.LOG],
            threshold=80.0,  # 80% CPU usage
            duration_seconds=180
        ))
        
        # Disk space critical
        self.add_rule(AlertRule(
            name="disk_space_critical",
            description="Disk space critically low",
            severity=AlertSeverity.CRITICAL,
            condition=lambda: False,
            channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
            threshold=90.0,  # 90% disk usage
            duration_seconds=60
        ))
        
        # Provider unavailable
        self.add_rule(AlertRule(
            name="provider_unavailable",
            description="External provider is unavailable",
            severity=AlertSeverity.ERROR,
            condition=lambda: False,
            channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
            duration_seconds=120
        ))
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule.
        
        Args:
            rule: Alert rule to add
        """
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove an alert rule.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if removed, False if not found
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """
        Enable an alert rule.
        
        Args:
            rule_name: Name of rule to enable
            
        Returns:
            True if enabled, False if not found
        """
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            logger.info(f"Enabled alert rule: {rule_name}")
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """
        Disable an alert rule.
        
        Args:
            rule_name: Name of rule to disable
            
        Returns:
            True if disabled, False if not found
        """
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            logger.info(f"Disabled alert rule: {rule_name}")
            return True
        return False
    
    def is_suppressed(self, rule_name: str) -> bool:
        """
        Check if alerts for a rule are currently suppressed.
        
        Args:
            rule_name: Name of rule to check
            
        Returns:
            True if suppressed, False otherwise
        """
        if rule_name not in self.suppressed_until:
            return False
        
        return time.time() < self.suppressed_until[rule_name]
    
    def suppress_rule(
        self,
        rule_name: str,
        duration_seconds: Optional[int] = None
    ) -> None:
        """
        Suppress alerts for a rule for a specified duration.
        
        Args:
            rule_name: Name of rule to suppress
            duration_seconds: Suppression duration (uses rule default if None)
        """
        if rule_name not in self.rules:
            logger.warning(f"Cannot suppress unknown rule: {rule_name}")
            return
        
        rule = self.rules[rule_name]
        duration = duration_seconds or rule.suppression_seconds
        
        self.suppressed_until[rule_name] = time.time() + duration
        logger.info(f"Suppressed alert rule {rule_name} for {duration}s")
    
    def trigger_alert(
        self,
        rule_name: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """
        Trigger an alert for a rule.
        
        Args:
            rule_name: Name of rule triggering the alert
            message: Alert message
            metadata: Additional alert metadata
            
        Returns:
            Alert object if triggered, None if suppressed
        """
        if rule_name not in self.rules:
            logger.error(f"Cannot trigger alert for unknown rule: {rule_name}")
            return None
        
        rule = self.rules[rule_name]
        
        if not rule.enabled:
            logger.debug(f"Alert rule {rule_name} is disabled")
            return None
        
        if self.is_suppressed(rule_name):
            logger.debug(f"Alert rule {rule_name} is suppressed")
            return None
        
        # Generate alert ID
        self._alert_id_counter += 1
        alert_id = f"alert_{self._alert_id_counter}_{int(time.time())}"
        
        # Create alert
        alert = Alert(
            id=alert_id,
            rule_name=rule_name,
            severity=rule.severity,
            message=message,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {}
        )
        
        # Store active alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        asyncio.create_task(self._send_notifications(alert, rule))
        
        # Start suppression
        self.suppress_rule(rule_name)
        
        logger.warning(
            f"Alert triggered: {rule_name} - {message}",
            extra={"alert_id": alert_id, "severity": rule.severity.value}
        )
        
        return alert
    
    async def _send_notifications(
        self,
        alert: Alert,
        rule: AlertRule
    ) -> None:
        """
        Send alert notifications through configured channels.
        
        Args:
            alert: Alert to send
            rule: Alert rule configuration
        """
        for channel in rule.channels:
            try:
                if channel == AlertChannel.LOG:
                    await self._send_log_notification(alert)
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_notification(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
                
            except Exception as e:
                logger.error(
                    f"Failed to send alert via {channel.value}: {e}",
                    extra={"alert_id": alert.id}
                )
    
    async def _send_log_notification(self, alert: Alert) -> None:
        """Send alert notification to logs."""
        log_level = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.warning)
        
        log_level(
            f"ALERT [{alert.severity.value.upper()}]: {alert.message}",
            extra={"alert": alert.to_dict()}
        )
    
    async def _send_email_notification(self, alert: Alert) -> None:
        """Send alert notification via email."""
        # TODO: Implement email notification
        logger.info(f"Email notification not implemented for alert {alert.id}")
    
    async def _send_slack_notification(self, alert: Alert) -> None:
        """Send alert notification to Slack."""
        # TODO: Implement Slack notification
        logger.info(f"Slack notification not implemented for alert {alert.id}")
    
    async def _send_webhook_notification(self, alert: Alert) -> None:
        """Send alert notification to webhook."""
        # TODO: Implement webhook notification
        logger.info(f"Webhook notification not implemented for alert {alert.id}")
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.
        
        Args:
            alert_id: ID of alert to resolve
            
        Returns:
            True if resolved, False if not found
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow().isoformat() + "Z"
            del self.active_alerts[alert_id]
            
            logger.info(f"Resolved alert {alert_id}: {alert.message}")
            return True
        
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get list of active alerts.
        
        Args:
            severity: Filter by severity (optional)
            
        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity (optional)
            
        Returns:
            List of historical alerts
        """
        alerts = self.alert_history[-limit:]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get summary of alert status.
        
        Returns:
            Dictionary with alert statistics
        """
        active_by_severity = {
            severity: len([a for a in self.active_alerts.values() 
                          if a.severity == severity])
            for severity in AlertSeverity
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_active": len(self.active_alerts),
            "active_by_severity": {
                k.value: v for k, v in active_by_severity.items()
            },
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "suppressed_rules": len([r for r in self.rules.keys() 
                                    if self.is_suppressed(r)]),
            "total_history": len(self.alert_history)
        }


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    Get the global alert manager instance.
    
    Returns:
        AlertManager instance
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager