"""
Monitoring module for Word Guess Game.
Handles CloudWatch metrics, logging, and alerts.
"""

import os
import boto3
import logging
from datetime import datetime
from typing import Dict, Optional
from botocore.exceptions import ClientError
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'game.log'),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

class GameMonitor:
    def __init__(self, environment: str = 'Development'):
        self.environment = environment
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.alert_topic_arn = os.getenv('ALERT_TOPIC_ARN')
        
        # Metric constants
        self.namespace = f"WordGuessGame/{environment}"
        self.dimension_name = "GameInstance"
        
    def put_metric(self, metric_name: str, value: float, unit: str,
                  dimensions: Optional[Dict[str, str]] = None) -> None:
        """
        Put a metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (e.g., 'Count', 'Milliseconds')
            dimensions: Optional dictionary of dimension name-value pairs
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            logger.debug(f"Published metric {metric_name}: {value} {unit}")
            
        except ClientError as e:
            logger.error(f"Failed to publish metric {metric_name}: {str(e)}")
    
    def track_game_duration(self, game_id: str, duration_ms: float) -> None:
        """Track game duration."""
        self.put_metric(
            metric_name='GameDuration',
            value=duration_ms,
            unit='Milliseconds',
            dimensions={'GameId': game_id}
        )
    
    def track_api_latency(self, endpoint: str, latency_ms: float) -> None:
        """Track API endpoint latency."""
        self.put_metric(
            metric_name='APILatency',
            value=latency_ms,
            unit='Milliseconds',
            dimensions={'Endpoint': endpoint}
        )
    
    def track_error(self, error_type: str) -> None:
        """Track error occurrence."""
        self.put_metric(
            metric_name='Errors',
            value=1,
            unit='Count',
            dimensions={'ErrorType': error_type}
        )
    
    def track_game_score(self, score: int) -> None:
        """Track game score."""
        self.put_metric(
            metric_name='GameScore',
            value=score,
            unit='Count'
        )
    
    def track_api_quota(self, remaining: int, reset_time: int) -> None:
        """Track OpenRouter API quota."""
        self.put_metric(
            metric_name='APIQuotaRemaining',
            value=remaining,
            unit='Count'
        )
        
        # Alert if quota is low
        if remaining < 100:  # Less than 100 requests remaining
            self.send_alert(
                f"API Quota Alert: Only {remaining} requests remaining. "
                f"Reset time: {datetime.fromtimestamp(reset_time)}"
            )
    
    def send_alert(self, message: str, subject: str = "Word Guess Game Alert") -> None:
        """Send SNS alert."""
        if not self.alert_topic_arn:
            logger.warning("Alert topic ARN not configured. Skipping alert.")
            return
            
        try:
            self.sns.publish(
                TopicArn=self.alert_topic_arn,
                Message=message,
                Subject=subject
            )
            logger.info(f"Sent alert: {subject}")
        except ClientError as e:
            logger.error(f"Failed to send alert: {str(e)}")

# Global monitor instance
monitor = GameMonitor(os.getenv('ENVIRONMENT', 'Development')) 