"""
API router for appointment scheduling functionality.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...models.scheduling import (
    Appointment, AppointmentType, AppointmentStatus, BookingLink,
    AvailabilitySlot
)
from ...services.appointment_scheduling_service import AppointmentSchedulingService


router = APIRouter(prefix="/appointments", tags=["appointments"])


# Request/Response models
class CreateAppointmentRequest(BaseModel):
    title: str
    appointment_type: AppointmentType
    start_time: datetime
    end_time: datetime
    attendee_email: Optional[str] = None
    attendee_phone: Optional[str] = None
    attendee_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    property_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    reminders_enabled: bool = True
    reminder_minutes_before: List[int] = [15, 60]


class UpdateAppointmentRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[AppointmentStatus] = None


class RescheduleAppointmentRequest(BaseModel):
    new_start_time: datetime
    new_end_time: datetime


class CreateBookingLinkRequest(BaseModel):
    name: str
    appointment_type: AppointmentType
    duration_minutes: int
    description: Optional[str] = None
    buffer_minutes: int = 15
    available_days: List[int] = [1, 2, 3, 4, 5]  # Monday-Friday
    available_time_start: str = "09:00"
    available_time_end: str = "17:00"
    max_days_in_advance: int = 30
    min_hours_in_advance: int = 2
    require_phone: bool = False


class BookAppointmentRequest(BaseModel):
    attendee_name: str
    attendee_email: str
    start_time: datetime
    attendee_phone: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CreateAvailabilitySlotRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    buffer_minutes: int = 15


def get_scheduling_service(db: Session = Depends(get_db)) -> AppointmentSchedulingService:
    """Get appointment scheduling service instance."""
    return AppointmentSchedulingService(db)


@router.post("/", response_model=Appointment)
async def create_appointment(
    request: CreateAppointmentRequest,
    organizer_id: uuid.UUID = Query(..., description="ID of the appointment organizer"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Create a new appointment."""
    try:
        appointment = await service.create_appointment(
            title=request.title,
            appointment_type=request.appointment_type,
            organizer_id=organizer_id,
            start_time=request.start_time,
            end_time=request.end_time,
            attendee_email=request.attendee_email,
            attendee_phone=request.attendee_phone,
            attendee_name=request.attendee_name,
            location=request.location,
            description=request.description,
            property_id=request.property_id,
            lead_id=request.lead_id,
            reminders_enabled=request.reminders_enabled,
            reminder_minutes_before=request.reminder_minutes_before
        )
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")


@router.get("/{appointment_id}", response_model=Appointment)
async def get_appointment(
    appointment_id: uuid.UUID,
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Get an appointment by ID."""
    appointment = await service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.put("/{appointment_id}", response_model=Appointment)
async def update_appointment(
    appointment_id: uuid.UUID,
    request: UpdateAppointmentRequest,
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Update an appointment."""
    updates = request.dict(exclude_unset=True)
    appointment = await service.update_appointment(appointment_id, **updates)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.post("/{appointment_id}/reschedule", response_model=Appointment)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    request: RescheduleAppointmentRequest,
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Reschedule an appointment."""
    try:
        appointment = await service.reschedule_appointment(
            appointment_id,
            request.new_start_time,
            request.new_end_time
        )
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reschedule appointment: {str(e)}")


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: uuid.UUID,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Cancel an appointment."""
    success = await service.cancel_appointment(appointment_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment cancelled successfully"}


@router.get("/", response_model=List[Appointment])
async def get_appointments(
    user_id: uuid.UUID = Query(..., description="User ID to get appointments for"),
    days_ahead: int = Query(7, description="Number of days ahead to look"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Get upcoming appointments for a user."""
    appointments = await service.get_upcoming_appointments(user_id, days_ahead)
    return appointments


@router.get("/availability/check")
async def check_availability(
    user_id: uuid.UUID = Query(..., description="User ID to check availability for"),
    start_time: datetime = Query(..., description="Start time to check"),
    end_time: datetime = Query(..., description="End time to check"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Check if a time slot is available."""
    is_available = await service.is_time_slot_available(user_id, start_time, end_time)
    return {"available": is_available}


@router.post("/availability", response_model=AvailabilitySlot)
async def create_availability_slot(
    request: CreateAvailabilitySlotRequest,
    user_id: uuid.UUID = Query(..., description="User ID to create availability for"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Create an availability slot."""
    slot = AvailabilitySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        start_time=request.start_time,
        end_time=request.end_time,
        is_available=request.is_available,
        buffer_minutes=request.buffer_minutes,
        created_at=datetime.utcnow()
    )
    return slot


# Booking Links endpoints
@router.post("/booking-links", response_model=BookingLink)
async def create_booking_link(
    request: CreateBookingLinkRequest,
    user_id: uuid.UUID = Query(..., description="User ID to create booking link for"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Create a public booking link."""
    booking_link = await service.create_booking_link(
        user_id=user_id,
        name=request.name,
        appointment_type=request.appointment_type,
        duration_minutes=request.duration_minutes,
        description=request.description,
        buffer_minutes=request.buffer_minutes,
        available_days=request.available_days,
        available_time_start=request.available_time_start,
        available_time_end=request.available_time_end,
        max_days_in_advance=request.max_days_in_advance,
        min_hours_in_advance=request.min_hours_in_advance,
        require_phone=request.require_phone
    )
    return booking_link


@router.get("/booking-links/{slug}/availability")
async def get_booking_link_availability(
    slug: str,
    date: datetime = Query(..., description="Date to check availability for"),
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Get available time slots for a booking link on a specific date."""
    slots = await service.get_available_time_slots(slug, date)
    return {"available_slots": slots}


@router.post("/booking-links/{slug}/book", response_model=Appointment)
async def book_appointment_via_link(
    slug: str,
    request: BookAppointmentRequest,
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Book an appointment through a public booking link."""
    try:
        appointment = await service.book_appointment_via_link(
            booking_link_slug=slug,
            attendee_name=request.attendee_name,
            attendee_email=request.attendee_email,
            start_time=request.start_time,
            attendee_phone=request.attendee_phone,
            custom_fields=request.custom_fields
        )
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")


@router.get("/booking-links/{slug}", response_model=BookingLink)
async def get_booking_link(
    slug: str,
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Get booking link details by slug."""
    booking_link = await service.get_booking_link_by_slug(slug)
    if not booking_link:
        raise HTTPException(status_code=404, detail="Booking link not found")
    return booking_link


# Reminder processing endpoint (for background tasks)
@router.post("/reminders/process")
async def process_reminders(
    service: AppointmentSchedulingService = Depends(get_scheduling_service)
):
    """Process pending reminders (typically called by background task)."""
    processed_count = await service.process_pending_reminders()
    return {"processed_reminders": processed_count}