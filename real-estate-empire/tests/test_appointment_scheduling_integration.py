"""
Integration tests for appointment scheduling system.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import uuid

from app.api.main import app
from app.models.scheduling import AppointmentType, AppointmentStatus


client = TestClient(app)


class TestAppointmentSchedulingIntegration:
    """Integration tests for appointment scheduling."""
    
    def setup_method(self):
        """Set up test data."""
        self.organizer_id = uuid.uuid4()
        self.attendee_email = "attendee@example.com"
        self.attendee_phone = "+1234567890"
        self.start_time = datetime.utcnow() + timedelta(hours=2)
        self.end_time = self.start_time + timedelta(hours=1)
    
    def test_create_appointment_success(self):
        """Test successful appointment creation."""
        appointment_data = {
            "title": "Property Viewing",
            "appointment_type": AppointmentType.PROPERTY_VIEWING.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_email": self.attendee_email,
            "attendee_phone": self.attendee_phone,
            "attendee_name": "John Doe",
            "location": "123 Main St",
            "description": "Viewing investment property"
        }
        
        response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == appointment_data["title"]
        assert data["appointment_type"] == appointment_data["appointment_type"]
        assert data["attendee_email"] == appointment_data["attendee_email"]
        assert data["status"] == AppointmentStatus.SCHEDULED.value
        assert "id" in data
    
    def test_create_appointment_invalid_time(self):
        """Test appointment creation with invalid time (end before start)."""
        appointment_data = {
            "title": "Invalid Appointment",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "start_time": self.start_time.isoformat(),
            "end_time": (self.start_time - timedelta(hours=1)).isoformat(),
            "attendee_email": self.attendee_email
        }
        
        response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_appointment(self):
        """Test retrieving an appointment."""
        # First create an appointment
        appointment_data = {
            "title": "Test Appointment",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_email": self.attendee_email
        }
        
        create_response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Now retrieve it
        get_response = client.get(f"/appointments/{appointment_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == appointment_id
        assert data["title"] == appointment_data["title"]
    
    def test_update_appointment(self):
        """Test updating an appointment."""
        # First create an appointment
        appointment_data = {
            "title": "Original Title",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_email": self.attendee_email
        }
        
        create_response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Update the appointment
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        update_response = client.put(
            f"/appointments/{appointment_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    def test_reschedule_appointment(self):
        """Test rescheduling an appointment."""
        # First create an appointment
        appointment_data = {
            "title": "Reschedule Test",
            "appointment_type": AppointmentType.PROPERTY_VIEWING.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_email": self.attendee_email
        }
        
        create_response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Reschedule to a new time
        new_start_time = self.start_time + timedelta(days=1)
        new_end_time = new_start_time + timedelta(hours=1)
        
        reschedule_data = {
            "new_start_time": new_start_time.isoformat(),
            "new_end_time": new_end_time.isoformat()
        }
        
        reschedule_response = client.post(
            f"/appointments/{appointment_id}/reschedule",
            json=reschedule_data
        )
        
        assert reschedule_response.status_code == 200
        data = reschedule_response.json()
        assert data["status"] == AppointmentStatus.RESCHEDULED.value
        assert data["start_time"] == new_start_time.isoformat()
        assert data["end_time"] == new_end_time.isoformat()
    
    def test_cancel_appointment(self):
        """Test cancelling an appointment."""
        # First create an appointment
        appointment_data = {
            "title": "Cancel Test",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_email": self.attendee_email
        }
        
        create_response = client.post(
            f"/appointments/?organizer_id={self.organizer_id}",
            json=appointment_data
        )
        
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Cancel the appointment
        cancel_response = client.delete(
            f"/appointments/{appointment_id}?reason=Test cancellation"
        )
        
        assert cancel_response.status_code == 200
        assert "cancelled successfully" in cancel_response.json()["message"]
    
    def test_check_availability(self):
        """Test checking time slot availability."""
        response = client.get(
            f"/appointments/availability/check"
            f"?user_id={self.organizer_id}"
            f"&start_time={self.start_time.isoformat()}"
            f"&end_time={self.end_time.isoformat()}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert isinstance(data["available"], bool)
    
    def test_get_upcoming_appointments(self):
        """Test getting upcoming appointments."""
        response = client.get(
            f"/appointments/?user_id={self.organizer_id}&days_ahead=7"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_booking_link(self):
        """Test creating a booking link."""
        booking_link_data = {
            "name": "Property Viewing Booking",
            "appointment_type": AppointmentType.PROPERTY_VIEWING.value,
            "duration_minutes": 60,
            "description": "Book a property viewing appointment",
            "available_days": [1, 2, 3, 4, 5],  # Monday-Friday
            "available_time_start": "09:00",
            "available_time_end": "17:00"
        }
        
        response = client.post(
            f"/appointments/booking-links?user_id={self.organizer_id}",
            json=booking_link_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == booking_link_data["name"]
        assert data["appointment_type"] == booking_link_data["appointment_type"]
        assert data["duration_minutes"] == booking_link_data["duration_minutes"]
        assert data["is_active"] is True
        assert "slug" in data
    
    def test_book_appointment_via_link(self):
        """Test booking an appointment through a booking link."""
        # First create a booking link
        booking_link_data = {
            "name": "Test Booking",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "duration_minutes": 30
        }
        
        link_response = client.post(
            f"/appointments/booking-links?user_id={self.organizer_id}",
            json=booking_link_data
        )
        
        assert link_response.status_code == 200
        slug = link_response.json()["slug"]
        
        # Book an appointment through the link
        booking_data = {
            "attendee_name": "Jane Smith",
            "attendee_email": "jane@example.com",
            "start_time": self.start_time.isoformat(),
            "attendee_phone": "+1987654321"
        }
        
        book_response = client.post(
            f"/appointments/booking-links/{slug}/book",
            json=booking_data
        )
        
        assert book_response.status_code == 200
        data = book_response.json()
        assert data["attendee_name"] == booking_data["attendee_name"]
        assert data["attendee_email"] == booking_data["attendee_email"]
        assert data["status"] == AppointmentStatus.SCHEDULED.value
    
    def test_get_booking_link_availability(self):
        """Test getting available slots for a booking link."""
        # First create a booking link
        booking_link_data = {
            "name": "Availability Test",
            "appointment_type": AppointmentType.PHONE_CALL.value,
            "duration_minutes": 30
        }
        
        link_response = client.post(
            f"/appointments/booking-links?user_id={self.organizer_id}",
            json=booking_link_data
        )
        
        assert link_response.status_code == 200
        slug = link_response.json()["slug"]
        
        # Get availability for tomorrow
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        availability_response = client.get(
            f"/appointments/booking-links/{slug}/availability"
            f"?date={tomorrow.isoformat()}"
        )
        
        assert availability_response.status_code == 200
        data = availability_response.json()
        assert "available_slots" in data
        assert isinstance(data["available_slots"], list)
    
    def test_create_availability_slot(self):
        """Test creating an availability slot."""
        slot_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "is_available": True,
            "buffer_minutes": 15
        }
        
        response = client.post(
            f"/appointments/availability?user_id={self.organizer_id}",
            json=slot_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(self.organizer_id)
        assert data["is_available"] is True
        assert data["buffer_minutes"] == 15
    
    def test_process_reminders(self):
        """Test processing reminders endpoint."""
        response = client.post("/appointments/reminders/process")
        
        assert response.status_code == 200
        data = response.json()
        assert "processed_reminders" in data
        assert isinstance(data["processed_reminders"], int)
    
    def test_appointment_not_found(self):
        """Test handling of non-existent appointment."""
        fake_id = uuid.uuid4()
        response = client.get(f"/appointments/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_booking_link_not_found(self):
        """Test handling of non-existent booking link."""
        response = client.get("/appointments/booking-links/non-existent-slug")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()