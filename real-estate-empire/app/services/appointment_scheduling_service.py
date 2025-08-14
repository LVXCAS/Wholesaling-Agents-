"""
Appointment scheduling service for managing appointments, availability, and calendar integration.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from sqlalchemy.orm import Session

from ..models.scheduling import (
    Appointment, AppointmentType, AppointmentStatus, AppointmentReminder,
    AvailabilitySlot, CalendarIntegration, BookingLink, ReminderType
)
from ..models.communication import CommunicationChannel
from ..core.database import get_db


class AppointmentSchedulingService:
    """Service for managing appointments and scheduling."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_appointment(
        self,
        title: str,
        appointment_type: AppointmentType,
        organizer_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        attendee_email: Optional[str] = None,
        attendee_phone: Optional[str] = None,
        attendee_name: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        property_id: Optional[uuid.UUID] = None,
        lead_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Appointment:
        """Create a new appointment."""
        
        # Validate time slot availability
        if not await self.is_time_slot_available(organizer_id, start_time, end_time):
            raise ValueError("Time slot is not available")
        
        appointment = Appointment(
            id=uuid.uuid4(),
            title=title,
            appointment_type=appointment_type,
            organizer_id=organizer_id,
            start_time=start_time,
            end_time=end_time,
            attendee_email=attendee_email,
            attendee_phone=attendee_phone,
            attendee_name=attendee_name,
            location=location,
            description=description,
            property_id=property_id,
            lead_id=lead_id,
            created_at=datetime.utcnow(),
            **kwargs
        )
        
        # Schedule reminders if enabled
        if appointment.reminders_enabled:
            await self.schedule_reminders(appointment)
        
        # Sync with external calendar if configured
        await self.sync_to_external_calendar(appointment)
        
        return appointment
    
    async def is_time_slot_available(
        self,
        user_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if a time slot is available for scheduling."""
        
        # Check for conflicting appointments
        conflicting_appointments = await self.get_appointments_in_range(
            user_id, start_time, end_time, exclude_appointment_id
        )
        
        if conflicting_appointments:
            return False
        
        # Check availability slots
        availability_slots = await self.get_availability_slots(
            user_id, start_time, end_time
        )
        
        # If no specific availability slots are defined, assume available during business hours
        if not availability_slots:
            return self.is_business_hours(start_time, end_time)
        
        # Check if the requested time falls within any availability slot
        for slot in availability_slots:
            if (slot.start_time <= start_time and 
                slot.end_time >= end_time and 
                slot.is_available):
                return True
        
        return False
    
    async def get_appointments_in_range(
        self,
        user_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: Optional[uuid.UUID] = None
    ) -> List[Appointment]:
        """Get appointments in a specific time range."""
        # This would query the database for appointments
        # For now, returning empty list as placeholder
        return []
    
    async def get_availability_slots(
        self,
        user_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[AvailabilitySlot]:
        """Get availability slots for a user in a time range."""
        # This would query the database for availability slots
        # For now, returning empty list as placeholder
        return []
    
    def is_business_hours(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if the time falls within standard business hours."""
        # Simple business hours check (9 AM - 5 PM, Monday-Friday)
        if start_time.weekday() >= 5:  # Weekend
            return False
        
        if start_time.hour < 9 or end_time.hour > 17:
            return False
        
        return True
    
    async def schedule_reminders(self, appointment: Appointment) -> List[AppointmentReminder]:
        """Schedule reminders for an appointment."""
        reminders = []
        
        for minutes_before in appointment.reminder_minutes_before:
            reminder_time = appointment.start_time - timedelta(minutes=minutes_before)
            
            # Don't schedule reminders in the past
            if reminder_time <= datetime.utcnow():
                continue
            
            # Create email reminder
            if appointment.attendee_email:
                email_reminder = AppointmentReminder(
                    id=uuid.uuid4(),
                    appointment_id=appointment.id,
                    reminder_type=ReminderType.EMAIL,
                    minutes_before=minutes_before,
                    scheduled_time=reminder_time,
                    created_at=datetime.utcnow()
                )
                reminders.append(email_reminder)
            
            # Create SMS reminder
            if appointment.attendee_phone:
                sms_reminder = AppointmentReminder(
                    id=uuid.uuid4(),
                    appointment_id=appointment.id,
                    reminder_type=ReminderType.SMS,
                    minutes_before=minutes_before,
                    scheduled_time=reminder_time,
                    created_at=datetime.utcnow()
                )
                reminders.append(sms_reminder)
        
        return reminders
    
    async def sync_to_external_calendar(self, appointment: Appointment) -> bool:
        """Sync appointment to external calendar."""
        # Get calendar integration settings
        calendar_integration = await self.get_calendar_integration(appointment.organizer_id)
        
        if not calendar_integration or not calendar_integration.sync_enabled:
            return False
        
        try:
            # This would integrate with Google Calendar, Outlook, etc.
            # For now, just return True as placeholder
            return True
        except Exception as e:
            print(f"Failed to sync appointment to external calendar: {e}")
            return False
    
    async def get_calendar_integration(self, user_id: uuid.UUID) -> Optional[CalendarIntegration]:
        """Get calendar integration settings for a user."""
        # This would query the database for calendar integration
        # For now, returning None as placeholder
        return None
    
    async def update_appointment(
        self,
        appointment_id: uuid.UUID,
        **updates
    ) -> Optional[Appointment]:
        """Update an existing appointment."""
        # This would update the appointment in the database
        # For now, returning None as placeholder
        return None
    
    async def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> bool:
        """Cancel an appointment."""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return False
        
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        
        # Cancel scheduled reminders
        await self.cancel_reminders(appointment_id)
        
        # Send cancellation notification
        await self.send_cancellation_notification(appointment, reason)
        
        return True
    
    async def get_appointment(self, appointment_id: uuid.UUID) -> Optional[Appointment]:
        """Get an appointment by ID."""
        # This would query the database for the appointment
        # For now, returning None as placeholder
        return None
    
    async def cancel_reminders(self, appointment_id: uuid.UUID) -> bool:
        """Cancel all reminders for an appointment."""
        # This would update reminder status in the database
        # For now, returning True as placeholder
        return True
    
    async def send_cancellation_notification(
        self,
        appointment: Appointment,
        reason: Optional[str] = None
    ) -> bool:
        """Send cancellation notification to attendee."""
        # This would send email/SMS notification
        # For now, returning True as placeholder
        return True
    
    async def reschedule_appointment(
        self,
        appointment_id: uuid.UUID,
        new_start_time: datetime,
        new_end_time: datetime
    ) -> Optional[Appointment]:
        """Reschedule an appointment to a new time."""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return None
        
        # Check if new time slot is available
        if not await self.is_time_slot_available(
            appointment.organizer_id,
            new_start_time,
            new_end_time,
            exclude_appointment_id=appointment_id
        ):
            raise ValueError("New time slot is not available")
        
        # Update appointment
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.updated_at = datetime.utcnow()
        
        # Reschedule reminders
        await self.cancel_reminders(appointment_id)
        await self.schedule_reminders(appointment)
        
        # Send reschedule notification
        await self.send_reschedule_notification(appointment)
        
        return appointment
    
    async def send_reschedule_notification(self, appointment: Appointment) -> bool:
        """Send reschedule notification to attendee."""
        # This would send email/SMS notification
        # For now, returning True as placeholder
        return True
    
    async def get_upcoming_appointments(
        self,
        user_id: uuid.UUID,
        days_ahead: int = 7
    ) -> List[Appointment]:
        """Get upcoming appointments for a user."""
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        # This would query the database for upcoming appointments
        # For now, returning empty list as placeholder
        return []
    
    async def create_booking_link(
        self,
        user_id: uuid.UUID,
        name: str,
        appointment_type: AppointmentType,
        duration_minutes: int,
        **kwargs
    ) -> BookingLink:
        """Create a public booking link."""
        slug = name.lower().replace(' ', '-').replace('_', '-')
        
        booking_link = BookingLink(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            slug=slug,
            appointment_type=appointment_type,
            duration_minutes=duration_minutes,
            created_at=datetime.utcnow(),
            **kwargs
        )
        
        return booking_link
    
    async def book_appointment_via_link(
        self,
        booking_link_slug: str,
        attendee_name: str,
        attendee_email: str,
        start_time: datetime,
        attendee_phone: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Appointment:
        """Book an appointment through a public booking link."""
        booking_link = await self.get_booking_link_by_slug(booking_link_slug)
        if not booking_link or not booking_link.is_active:
            raise ValueError("Booking link not found or inactive")
        
        # Validate booking constraints
        await self.validate_booking_constraints(booking_link, start_time)
        
        end_time = start_time + timedelta(minutes=booking_link.duration_minutes)
        
        appointment = await self.create_appointment(
            title=f"{booking_link.name} - {attendee_name}",
            appointment_type=booking_link.appointment_type,
            organizer_id=booking_link.user_id,
            start_time=start_time,
            end_time=end_time,
            attendee_name=attendee_name,
            attendee_email=attendee_email,
            attendee_phone=attendee_phone,
            metadata=custom_fields
        )
        
        # Send confirmation if enabled
        if booking_link.send_confirmation:
            await self.send_booking_confirmation(appointment)
        
        return appointment
    
    async def get_booking_link_by_slug(self, slug: str) -> Optional[BookingLink]:
        """Get a booking link by its slug."""
        # This would query the database for the booking link
        # For now, returning None as placeholder
        return None
    
    async def validate_booking_constraints(
        self,
        booking_link: BookingLink,
        start_time: datetime
    ) -> bool:
        """Validate booking constraints for a booking link."""
        now = datetime.utcnow()
        
        # Check minimum advance notice
        min_advance = timedelta(hours=booking_link.min_hours_in_advance)
        if start_time < now + min_advance:
            raise ValueError(f"Appointment must be scheduled at least {booking_link.min_hours_in_advance} hours in advance")
        
        # Check maximum advance booking
        max_advance = timedelta(days=booking_link.max_days_in_advance)
        if start_time > now + max_advance:
            raise ValueError(f"Appointment cannot be scheduled more than {booking_link.max_days_in_advance} days in advance")
        
        # Check available days
        if start_time.isoweekday() not in booking_link.available_days:
            raise ValueError("Appointment cannot be scheduled on this day of the week")
        
        # Check available hours
        start_hour_minute = start_time.strftime("%H:%M")
        if (start_hour_minute < booking_link.available_time_start or 
            start_hour_minute >= booking_link.available_time_end):
            raise ValueError("Appointment time is outside available hours")
        
        return True
    
    async def send_booking_confirmation(self, appointment: Appointment) -> bool:
        """Send booking confirmation to attendee."""
        # This would send email confirmation
        # For now, returning True as placeholder
        return True
    
    async def get_available_time_slots(
        self,
        booking_link_slug: str,
        date: datetime,
        timezone: str = "UTC"
    ) -> List[datetime]:
        """Get available time slots for a booking link on a specific date."""
        booking_link = await self.get_booking_link_by_slug(booking_link_slug)
        if not booking_link or not booking_link.is_active:
            return []
        
        # Generate time slots based on availability
        slots = []
        start_time = datetime.combine(
            date.date(),
            datetime.strptime(booking_link.available_time_start, "%H:%M").time()
        )
        end_time = datetime.combine(
            date.date(),
            datetime.strptime(booking_link.available_time_end, "%H:%M").time()
        )
        
        current_time = start_time
        while current_time + timedelta(minutes=booking_link.duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=booking_link.duration_minutes)
            
            # Check if slot is available
            if await self.is_time_slot_available(booking_link.user_id, current_time, slot_end):
                slots.append(current_time)
            
            # Move to next slot (with buffer)
            current_time += timedelta(minutes=booking_link.duration_minutes + booking_link.buffer_minutes)
        
        return slots
    
    async def process_pending_reminders(self) -> int:
        """Process pending reminders that are due to be sent."""
        # This would query for pending reminders and send them
        # For now, returning 0 as placeholder
        return 0
    
    async def send_reminder(self, reminder: AppointmentReminder) -> bool:
        """Send a specific reminder."""
        appointment = await self.get_appointment(reminder.appointment_id)
        if not appointment:
            return False
        
        try:
            if reminder.reminder_type == ReminderType.EMAIL and appointment.attendee_email:
                # Send email reminder
                await self.send_email_reminder(appointment, reminder)
            elif reminder.reminder_type == ReminderType.SMS and appointment.attendee_phone:
                # Send SMS reminder
                await self.send_sms_reminder(appointment, reminder)
            
            reminder.sent_at = datetime.utcnow()
            reminder.status = "sent"
            return True
        except Exception as e:
            print(f"Failed to send reminder: {e}")
            reminder.status = "failed"
            return False
    
    async def send_email_reminder(self, appointment: Appointment, reminder: AppointmentReminder):
        """Send email reminder for appointment."""
        # This would integrate with email service
        pass
    
    async def send_sms_reminder(self, appointment: Appointment, reminder: AppointmentReminder):
        """Send SMS reminder for appointment."""
        # This would integrate with SMS service
        pass