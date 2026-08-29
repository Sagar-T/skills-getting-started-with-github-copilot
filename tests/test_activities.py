"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Verify that GET /activities returns all 9 activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
    
    def test_get_activities_contains_all_expected_names(self, client):
        """Verify all expected activity names are in response"""
        response = client.get("/activities")
        activities = response.json()
        expected_names = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Swimming Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club"
        }
        assert set(activities.keys()) == expected_names
    
    def test_get_activities_has_correct_structure(self, client):
        """Verify response has correct data structure for each activity"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_success(self, client):
        """Verify new student can sign up successfully"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "alex@mergington.edu" in data["message"]
    
    def test_signup_appears_in_activity_list(self, client):
        """Verify signed up student appears in activity participants"""
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "alex@mergington.edu" in activities["Basketball Team"]["participants"]
    
    def test_signup_already_registered_student_returns_400(self, client):
        """Verify signup fails with 400 if student already registered"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}  # Already in Chess Club
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_activity_not_found_returns_404(self, client):
        """Verify signup fails with 404 for non-existent activity"""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_invalid_email_domain_returns_400(self, client):
        """Verify signup fails if email is not @mergington.edu"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@gmail.com"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "mergington.edu" in data["detail"]
    
    def test_signup_with_other_domain_returns_400(self, client):
        """Verify signup rejects various non-mergington domains"""
        invalid_emails = [
            "student@example.com",
            "user@school.edu",
            "test@mergington.com",  # Wrong TLD
            "alex@gmergington.edu"  # Wrong domain
        ]
        
        for email in invalid_emails:
            response = client.post(
                "/activities/Basketball Team/signup",
                params={"email": email}
            )
            assert response.status_code == 400
            assert "mergington.edu" in response.json()["detail"]
    
    def test_signup_multiple_students_same_activity(self, client):
        """Verify multiple students can sign up for same activity"""
        client.post("/activities/Basketball Team/signup", params={"email": "alex@mergington.edu"})
        client.post("/activities/Basketball Team/signup", params={"email": "james@mergington.edu"})
        
        response = client.get("/activities")
        participants = response.json()["Basketball Team"]["participants"]
        assert "alex@mergington.edu" in participants
        assert "james@mergington.edu" in participants
        assert len(participants) == 2


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_registered_student_success(self, client):
        """Verify registered student can unregister successfully"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}  # Already registered
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_from_participants(self, client):
        """Verify unregistered student is removed from participants list"""
        client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
    
    def test_unregister_not_registered_student_returns_400(self, client):
        """Verify unregister fails with 400 if student not registered"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_activity_not_found_returns_404(self, client):
        """Verify unregister fails with 404 for non-existent activity"""
        response = client.post(
            "/activities/Fake Activity/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_invalid_email_domain_returns_400(self, client):
        """Verify unregister fails if email is not @mergington.edu"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "alex@gmail.com"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "mergington.edu" in data["detail"]


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_signup_then_unregister_flow(self, client):
        """Verify complete signup -> unregister lifecycle"""
        # Student signs up
        signup_response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert signup_response.status_code == 200
        
        # Verify student is in activity
        get_response = client.get("/activities")
        assert "alex@mergington.edu" in get_response.json()["Basketball Team"]["participants"]
        
        # Student unregisters
        unregister_response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert unregister_response.status_code == 200
        
        # Verify student is no longer in activity
        get_response = client.get("/activities")
        assert "alex@mergington.edu" not in get_response.json()["Basketball Team"]["participants"]
    
    def test_signup_unregister_resignup_flow(self, client):
        """Verify student can re-signup after unregistering"""
        # Signup
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        # Unregister
        client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "alex@mergington.edu"}
        )
        
        # Re-signup (should succeed)
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify student is back in activity
        get_response = client.get("/activities")
        assert "alex@mergington.edu" in get_response.json()["Basketball Team"]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client):
        """Verify multiple students can signup and unregister in sequence"""
        emails = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]
        
        # All sign up
        for email in emails:
            response = client.post(
                "/activities/Basketball Team/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()["Basketball Team"]["participants"]
        for email in emails:
            assert email in participants
        assert len(participants) == 3
        
        # Two unregister
        client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "alice@mergington.edu"}
        )
        client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "bob@mergington.edu"}
        )
        
        # Verify only charlie remains
        response = client.get("/activities")
        participants = response.json()["Basketball Team"]["participants"]
        assert "charlie@mergington.edu" in participants
        assert "alice@mergington.edu" not in participants
        assert "bob@mergington.edu" not in participants
        assert len(participants) == 1


class TestEmailValidation:
    """Tests for email domain validation (@mergington.edu)"""
    
    def test_valid_mergington_email_accepted_for_signup(self, client):
        """Verify valid @mergington.edu emails are accepted"""
        valid_emails = [
            "student@mergington.edu",
            "alex.smith@mergington.edu",
            "m.johnson@mergington.edu",
            "user123@mergington.edu"
        ]
        
        for email in valid_emails:
            response = client.post(
                "/activities/Basketball Team/signup",
                params={"email": email}
            )
            assert response.status_code == 200
    
    def test_invalid_emails_rejected_for_signup(self, client):
        """Verify non-@mergington.edu emails are rejected"""
        invalid_emails = [
            "student@gmail.com",
            "user@yahoo.edu",
            "alex@mergingtonia.edu",
            "test@mergington.org",
            "nomail",
            "student@example.com"
        ]
        
        for email in invalid_emails:
            response = client.post(
                "/activities/Basketball Team/signup",
                params={"email": email}
            )
            assert response.status_code == 400
    
    def test_email_validation_case_sensitive_domain(self, client):
        """Verify domain validation works regardless of case"""
        # FastAPI/Python string endswith is case-sensitive
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@MERGINGTON.EDU"}
        )
        # Current implementation requires lowercase - should fail
        assert response.status_code == 400


class TestActivityStability:
    """Tests to ensure activity data remains stable across operations"""
    
    def test_activity_data_unchanged_after_get(self, client):
        """Verify GET request doesn't modify activity data"""
        response1 = client.get("/activities")
        response2 = client.get("/activities")
        
        assert response1.json() == response2.json()
    
    def test_max_participants_not_decremented_by_signup(self, client):
        """Verify max_participants stays constant after signup"""
        response1 = client.get("/activities")
        max_before = response1.json()["Basketball Team"]["max_participants"]
        
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        response2 = client.get("/activities")
        max_after = response2.json()["Basketball Team"]["max_participants"]
        
        assert max_before == max_after
    
    def test_other_activities_unaffected_by_signup(self, client):
        """Verify signup to one activity doesn't affect others"""
        response1 = client.get("/activities")
        chess_before = response1.json()["Chess Club"]["participants"].copy()
        
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        response2 = client.get("/activities")
        chess_after = response2.json()["Chess Club"]["participants"]
        
        assert chess_before == chess_after
