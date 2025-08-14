"""
Voice call service integration for making calls, dropping voicemails, and handling transcriptions.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from twilio.twiml.voice_response import VoiceResponse
from jinja2 import Template
import requests

try:
    from ..models.communication import (
        VoiceCall, VoiceScript, MessageStatus, MessagePriority,
        CommunicationAnalytics, CommunicationChannel
    )
except ImportError:
    from app.models.communication import (
        VoiceCall, VoiceScript, MessageStatus, MessagePriority,
        CommunicationAnalytics, CommunicationChannel
    )


logger = logging.getLogger(__name__)


class VoiceServiceConfig:
    """Voice service configuration."""
    
    def __init__(
        self,
        twilio_account_sid: str = "",
        twilio_auth_token: str = "",
        default_from_phone: str = "",
        webhook_base_url: str = "",
        recording_enabled: bool = True,
        transcription_enabled: bool = True,
        voicemail_detection: bool = True,
        max_call_duration: int = 300  # 5 minutes
    ):
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.default_from_phone = default_from_phone
        self.webhook_base_url = webhook_base_url
        self.recording_enabled = recording_enabled
        self.transcription_enabled = transcription_enabled
        self.voicemail_detection = voicemail_detection
        self.max_call_duration = max_call_duration


class VoiceScriptEngine:
    """Voice script engine using Jinja2."""
    
    def render_script(self, script: VoiceScript, variables: Dict[str, Any]) -> str:
        """Render voice script with variables."""
        try:
            script_template = Template(script.script)
            rendered_script = script_template.render(**variables)
            return rendered_script
        except Exception as e:
            logger.error(f"Error rendering voice script {script.id}: {e}")
            raise
    
    def validate_script(self, script: VoiceScript) -> List[str]:
        """Validate voice script for syntax errors."""
        errors = []
        
        try:
            Template(script.script)
        except Exception as e:
            errors.append(f"Script template error: {e}")
        
        # Check script length (reasonable limit for voice)
        if len(script.script) > 5000:
            errors.append("Script is too long (max 5000 characters)")
        
        return errors
    
    def generate_twiml(self, script_content: str, call_id: uuid.UUID) -> str:
        """Generate TwiML for voice script."""
        response = VoiceResponse()
        
        # Add pause at the beginning
        response.pause(length=1)
        
        # Split script into sentences for natural speech
        sentences = script_content.split('. ')
        
        for sentence in sentences:
            if sentence.strip():
                # Add sentence with pause
                response.say(sentence.strip() + '.', voice='alice', rate='medium')
                response.pause(length=0.5)
        
        # Add gather for response if needed
        gather = response.gather(
            input='speech dtmf',
            timeout=10,
            speech_timeout='auto',
            action=f'/voice/response/{call_id}'
        )
        gather.say("Please respond after the beep.", voice='alice')
        
        # Fallback if no response
        response.say("Thank you for your time. Goodbye.", voice='alice')
        response.hangup()
        
        return str(response)


class VoiceCallAnalyzer:
    """Voice call analyzer for processing recordings and transcriptions."""
    
    def __init__(self):
        self.sentiment_keywords = {
            'positive': ['interested', 'yes', 'great', 'good', 'excellent', 'perfect'],
            'negative': ['no', 'not interested', 'stop', 'remove', 'annoying', 'busy'],
            'neutral': ['maybe', 'think about it', 'call back', 'later', 'unsure']
        }
    
    def analyze_transcription(self, transcription: str) -> Dict[str, Any]:
        """Analyze call transcription for sentiment and key information."""
        if not transcription:
            return {
                'sentiment': 'unknown',
                'confidence': 0.0,
                'keywords': [],
                'interest_level': 0.0,
                'callback_requested': False
            }
        
        transcription_lower = transcription.lower()
        
        # Simple sentiment analysis
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in transcription_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in transcription_lower)
        neutral_count = sum(1 for word in self.sentiment_keywords['neutral'] if word in transcription_lower)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            sentiment = 'neutral'
            confidence = 0.0
        elif positive_count > negative_count:
            sentiment = 'positive'
            confidence = positive_count / total_sentiment_words
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = negative_count / total_sentiment_words
        else:
            sentiment = 'neutral'
            confidence = neutral_count / total_sentiment_words if neutral_count > 0 else 0.0
        
        # Calculate interest level
        interest_level = max(0.0, min(1.0, (positive_count - negative_count + 1) / 3))
        
        # Check for callback request
        callback_keywords = ['call back', 'callback', 'call me back', 'reach out', 'contact me']
        callback_requested = any(keyword in transcription_lower for keyword in callback_keywords)
        
        # Extract keywords
        all_keywords = self.sentiment_keywords['positive'] + self.sentiment_keywords['negative'] + self.sentiment_keywords['neutral']
        found_keywords = [word for word in all_keywords if word in transcription_lower]
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'keywords': found_keywords,
            'interest_level': interest_level,
            'callback_requested': callback_requested
        }
    
    def analyze_call_metrics(self, call: VoiceCall) -> Dict[str, Any]:
        """Analyze call metrics and performance."""
        metrics = {
            'call_duration': call.duration_seconds or 0,
            'answered': call.answered_at is not None,
            'voicemail_dropped': call.voicemail_dropped,
            'recording_available': call.recording_url is not None,
            'transcription_available': call.transcription is not None
        }
        
        # Determine call outcome
        if not metrics['answered']:
            metrics['outcome'] = 'no_answer'
        elif metrics['voicemail_dropped']:
            metrics['outcome'] = 'voicemail'
        elif metrics['call_duration'] > 30:
            metrics['outcome'] = 'conversation'
        else:
            metrics['outcome'] = 'brief_contact'
        
        return metrics


class VoiceService:
    """Voice service for making calls, dropping voicemails, and handling transcriptions."""
    
    def __init__(self, config: VoiceServiceConfig):
        self.config = config
        self.client = Client(config.twilio_account_sid, config.twilio_auth_token) if config.twilio_account_sid else None
        self.script_engine = VoiceScriptEngine()
        self.analyzer = VoiceCallAnalyzer()
        self.calls: Dict[uuid.UUID, VoiceCall] = {}
        self.scripts: Dict[uuid.UUID, VoiceScript] = {}
    
    async def initiate_call(
        self,
        to_phone: str,
        script: VoiceScript,
        script_variables: Optional[Dict[str, Any]] = None,
        from_phone: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> VoiceCall:
        """Initiate a voice call."""
        if not self.client:
            raise ValueError("Twilio client not configured")
        
        call_id = uuid.uuid4()
        call = VoiceCall(
            id=call_id,
            to_phone=to_phone,
            from_phone=from_phone or self.config.default_from_phone,
            script_id=script.id,
            script_variables=script_variables or {},
            priority=priority,
            scheduled_at=scheduled_at,
            created_at=datetime.now()
        )
        
        try:
            # Render script with variables
            rendered_script = self.script_engine.render_script(script, script_variables or {})
            
            # Generate TwiML
            twiml = self.script_engine.generate_twiml(rendered_script, call_id)
            
            # Store call for tracking
            self.calls[call_id] = call
            
            if scheduled_at and scheduled_at > datetime.now():
                # Schedule call for later
                call.status = MessageStatus.QUEUED
                logger.info(f"Call {call_id} scheduled for {scheduled_at}")
            else:
                # Make call immediately
                call.status = MessageStatus.SENT
                call.initiated_at = datetime.now()
                
                # Create Twilio call
                twilio_call = self.client.calls.create(
                    to=to_phone,
                    from_=call.from_phone,
                    url=f"{self.config.webhook_base_url}/voice/twiml/{call_id}",
                    status_callback=f"{self.config.webhook_base_url}/voice/status/{call_id}",
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                    record=self.config.recording_enabled,
                    recording_status_callback=f"{self.config.webhook_base_url}/voice/recording/{call_id}",
                    timeout=30,
                    machine_detection='Enable' if self.config.voicemail_detection else 'Disable'
                )
                
                # Store Twilio call SID
                call.metadata = {'twilio_call_sid': twilio_call.sid}
                
                logger.info(f"Call {call_id} initiated to {to_phone}")
        
        except Exception as e:
            call.status = MessageStatus.FAILED
            call.metadata = {'error': str(e)}
            logger.error(f"Failed to initiate call {call_id}: {e}")
            raise
        
        return call
    
    async def drop_voicemail(
        self,
        call_id: uuid.UUID,
        voicemail_script: str
    ) -> bool:
        """Drop a voicemail message."""
        call = self.calls.get(call_id)
        if not call:
            logger.error(f"Call {call_id} not found")
            return False
        
        try:
            # Generate voicemail TwiML
            response = VoiceResponse()
            response.pause(length=1)
            response.say(voicemail_script, voice='alice', rate='medium')
            response.hangup()
            
            # Update call status
            call.voicemail_dropped = True
            call.status = MessageStatus.DELIVERED
            
            logger.info(f"Voicemail dropped for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop voicemail for call {call_id}: {e}")
            return False
    
    async def handle_call_status(
        self,
        call_id: uuid.UUID,
        status: str,
        call_duration: Optional[int] = None
    ) -> None:
        """Handle call status updates from Twilio."""
        call = self.calls.get(call_id)
        if not call:
            logger.error(f"Call {call_id} not found for status update")
            return
        
        try:
            if status == 'ringing':
                # Call is ringing
                pass
            elif status == 'in-progress':
                call.answered_at = datetime.now()
                call.status = MessageStatus.DELIVERED
            elif status == 'completed':
                call.ended_at = datetime.now()
                call.duration_seconds = call_duration
                
                # Determine final status
                if call.answered_at:
                    call.status = MessageStatus.DELIVERED
                else:
                    call.status = MessageStatus.FAILED
            elif status == 'failed' or status == 'busy' or status == 'no-answer':
                call.status = MessageStatus.FAILED
                call.ended_at = datetime.now()
            
            logger.info(f"Call {call_id} status updated to {status}")
            
        except Exception as e:
            logger.error(f"Error handling call status for {call_id}: {e}")
    
    async def handle_recording(
        self,
        call_id: uuid.UUID,
        recording_url: str,
        recording_duration: Optional[int] = None
    ) -> None:
        """Handle call recording from Twilio."""
        call = self.calls.get(call_id)
        if not call:
            logger.error(f"Call {call_id} not found for recording")
            return
        
        try:
            call.recording_url = recording_url
            
            # Request transcription if enabled
            if self.config.transcription_enabled:
                await self._request_transcription(call_id, recording_url)
            
            logger.info(f"Recording saved for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error handling recording for call {call_id}: {e}")
    
    async def _request_transcription(
        self,
        call_id: uuid.UUID,
        recording_url: str
    ) -> None:
        """Request transcription for a call recording."""
        try:
            # This would integrate with a transcription service like AssemblyAI or AWS Transcribe
            # For now, we'll simulate with a placeholder
            
            # In a real implementation, you would:
            # 1. Send the recording to a transcription service
            # 2. Handle the async response
            # 3. Store the transcription
            
            # Placeholder transcription
            call = self.calls.get(call_id)
            if call:
                call.transcription = "Transcription would be processed here"
                
                # Analyze transcription
                analysis = self.analyzer.analyze_transcription(call.transcription)
                if not call.metadata:
                    call.metadata = {}
                call.metadata['transcription_analysis'] = analysis
            
            logger.info(f"Transcription requested for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error requesting transcription for call {call_id}: {e}")
    
    async def get_call_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CommunicationAnalytics:
        """Get voice call analytics for a date range."""
        calls_in_range = [
            call for call in self.calls.values()
            if call.created_at and start_date <= call.created_at <= end_date
        ]
        
        total_sent = len(calls_in_range)
        total_delivered = len([c for c in calls_in_range if c.answered_at])
        total_failed = len([c for c in calls_in_range if c.status == MessageStatus.FAILED])
        
        delivery_rate = (total_delivered / total_sent) if total_sent > 0 else 0.0
        
        return CommunicationAnalytics(
            channel=CommunicationChannel.VOICE,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_bounced=total_failed,
            delivery_rate=delivery_rate,
            period_start=start_date,
            period_end=end_date
        )
    
    async def get_call(self, call_id: uuid.UUID) -> Optional[VoiceCall]:
        """Get a call by ID."""
        return self.calls.get(call_id)
    
    async def get_calls_by_phone(self, phone: str) -> List[VoiceCall]:
        """Get all calls to a specific phone number."""
        return [call for call in self.calls.values() if call.to_phone == phone]
    
    async def cancel_call(self, call_id: uuid.UUID) -> bool:
        """Cancel a scheduled call."""
        call = self.calls.get(call_id)
        if not call:
            return False
        
        if call.status == MessageStatus.QUEUED:
            call.status = MessageStatus.FAILED
            call.metadata = {'cancelled': True}
            return True
        
        return False
    
    def create_script(self, script: VoiceScript) -> VoiceScript:
        """Create a new voice script."""
        if not script.id:
            script.id = uuid.uuid4()
        
        script.created_at = datetime.now()
        script.updated_at = datetime.now()
        
        # Validate script
        errors = self.script_engine.validate_script(script)
        if errors:
            raise ValueError(f"Script validation errors: {errors}")
        
        self.scripts[script.id] = script
        logger.info(f"Voice script created: {script.name}")
        return script
    
    def get_script(self, script_id: uuid.UUID) -> Optional[VoiceScript]:
        """Get a voice script by ID."""
        return self.scripts.get(script_id)
    
    def list_scripts(self, category: Optional[str] = None) -> List[VoiceScript]:
        """List all voice scripts, optionally filtered by category."""
        scripts = list(self.scripts.values())
        if category:
            scripts = [s for s in scripts if s.category == category]
        return scripts
    
    def delete_script(self, script_id: uuid.UUID) -> bool:
        """Delete a voice script."""
        if script_id in self.scripts:
            del self.scripts[script_id]
            logger.info(f"Voice script deleted: {script_id}")
            return True
        return False
    
    async def send_bulk_calls(
        self,
        script: VoiceScript,
        recipients: List[Dict[str, Any]],
        batch_size: int = 5,
        delay_seconds: float = 2.0
    ) -> List[VoiceCall]:
        """Send bulk voice calls with rate limiting."""
        sent_calls = []
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            batch_tasks = []
            
            for recipient in batch:
                call = await self.initiate_call(
                    to_phone=recipient["phone"],
                    script=script,
                    script_variables=recipient.get("variables", {}),
                    priority=recipient.get("priority", MessagePriority.NORMAL)
                )
                batch_tasks.append(call)
            
            sent_calls.extend(batch_tasks)
            
            # Delay between batches to avoid rate limiting
            if i + batch_size < len(recipients):
                await asyncio.sleep(delay_seconds)
        
        logger.info(f"Bulk calls initiated to {len(recipients)} recipients")
        return sent_calls