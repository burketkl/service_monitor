"""
Alert Manager - Handles notifications and alerts
"""

import os
import platform
from typing import Optional
from plyer import notification
from enum import Enum


class AlertType(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: dict):
        self.config = config.get('alerts', {})
        self.sound_enabled = self.config.get('sound_enabled', True)
        self.desktop_enabled = self.config.get('desktop_notifications', True)
        self.sms_enabled = self.config.get('sms_enabled', False)
        
        # Initialize Twilio if SMS is enabled
        self.twilio_client = None
        if self.sms_enabled:
            self._init_twilio()
    
    def _init_twilio(self):
        """Initialize Twilio client for SMS"""
        try:
            from twilio.rest import Client
            account_sid = self.config.get('twilio_account_sid')
            auth_token = self.config.get('twilio_auth_token')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
        except ImportError:
            print("Twilio not installed. SMS alerts disabled.")
            self.sms_enabled = False
    
    def send_alert(self, title: str, message: str, alert_type: AlertType = AlertType.INFO):
        """Send an alert through configured channels"""
        
        # Desktop notification
        if self.desktop_enabled:
            self._send_desktop_notification(title, message)
        
        # Sound alert
        if self.sound_enabled:
            self._play_sound(alert_type)
        
        # SMS alert (only for warnings and critical)
        if self.sms_enabled and alert_type in [AlertType.WARNING, AlertType.CRITICAL]:
            self._send_sms(title, message)
    
    def _send_desktop_notification(self, title: str, message: str):
        """Send desktop notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Service Monitor",
                timeout=10
            )
        except Exception as e:
            print(f"Failed to send desktop notification: {e}")
    
    def _play_sound(self, alert_type: AlertType):
        """Play alert sound"""
        try:
            sound_file = self.config.get('sound_file')
            
            if sound_file and os.path.exists(sound_file):
                # Play custom sound file
                self._play_audio_file(sound_file)
            else:
                # Play system beep
                if platform.system() == 'Windows':
                    import winsound
                    if alert_type == AlertType.CRITICAL:
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                    elif alert_type == AlertType.WARNING:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                else:
                    # Unix-like systems
                    print('\a')  # Terminal bell
        except Exception as e:
            print(f"Failed to play sound: {e}")
    
    def _play_audio_file(self, filepath: str):
        """Play audio file (WAV)"""
        try:
            if platform.system() == 'Windows':
                import winsound
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # For other platforms, would need additional libraries
                print(f"Audio playback not implemented for {platform.system()}")
        except Exception as e:
            print(f"Failed to play audio file: {e}")
    
    def _send_sms(self, title: str, message: str):
        """Send SMS alert via Twilio"""
        if not self.twilio_client:
            return
        
        try:
            from_number = self.config.get('twilio_from_number')
            to_numbers = self.config.get('twilio_to_numbers', [])
            
            body = f"{title}\n{message}"
            
            for to_number in to_numbers:
                self.twilio_client.messages.create(
                    body=body,
                    from_=from_number,
                    to=to_number
                )
        except Exception as e:
            print(f"Failed to send SMS: {e}")
    
    def alert_service_down(self, service_name: str):
        """Alert that a service is down"""
        self.send_alert(
            title=f"Service Down: {service_name}",
            message=f"{service_name} is not responding",
            alert_type=AlertType.CRITICAL
        )
    
    def alert_service_degraded(self, service_name: str):
        """Alert that a service is degraded"""
        self.send_alert(
            title=f"Service Degraded: {service_name}",
            message=f"{service_name} is experiencing slow response times",
            alert_type=AlertType.WARNING
        )
    
    def alert_service_restored(self, service_name: str):
        """Alert that a service is restored"""
        self.send_alert(
            title=f"Service Restored: {service_name}",
            message=f"{service_name} is back online",
            alert_type=AlertType.INFO
        )
