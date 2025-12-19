"""
Property-based tests for download endpoint.

**Feature: frontend-backend-integration, Property 9: Non-existent session returns 404**
**Feature: frontend-backend-integration, Property 10: Incomplete session download rejection**
**Validates: Requirements 8.3, 8.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi.testclient import TestClient
from datetime import datetime

from main import app, sessions

client = TestClient(app)


# Strategy for generating random session IDs that don't exist
@st.composite
def non_existent_session_id_strategy(draw):
    """Generate session IDs that are guaranteed not to exist in the sessions store."""
    # Generate random session ID patterns
    prefix = draw(st.sampled_from(["session", "sess", "s", "nonexistent", "fake", "test"]))
    random_part = draw(st.from_regex(r'[a-zA-Z0-9]{5,20}', fullmatch=True))
    timestamp = draw(st.integers(min_value=1000000000, max_value=9999999999))
    
    session_id = f"{prefix}-{random_part}-{timestamp}"
    
    # Ensure this ID doesn't exist in sessions
    assume(session_id not in sessions)
    
    return session_id


# Strategy for generating valid download formats
valid_format_strategy = st.sampled_from(["pdf", "latex"])


# Strategy for generating incomplete session statuses
incomplete_status_strategy = st.sampled_from(["configuring", "running", "paused", "stopped", "failed"])


# Strategy for generating valid session config
@st.composite
def valid_session_config_strategy(draw):
    """Generate valid session configuration."""
    title = draw(st.from_regex(r'[A-Za-z ]{5,30}', fullmatch=True))
    domain = draw(st.sampled_from(["AI", "Machine Learning", "Data Science", "NLP", "Computer Vision"]))
    keywords = draw(st.lists(
        st.from_regex(r'[a-z]{3,10}', fullmatch=True),
        min_size=1,
        max_size=5
    ))
    
    return {
        "topic": {
            "title": title,
            "domain": domain,
            "keywords": keywords,
            "complexity": draw(st.sampled_from(["low", "medium", "high"]))
        },
        "authorName": draw(st.from_regex(r'[A-Za-z ]{3,20}', fullmatch=True)),
        "authorInstitution": draw(st.from_regex(r'[A-Za-z ]{5,30}', fullmatch=True))
    }


class TestNonExistentSessionProperty:
    """
    **Feature: frontend-backend-integration, Property 9: Non-existent session returns 404**
    
    *For any* session ID that does not exist in the system, requests to the download 
    endpoint SHALL return a 404 status code.
    
    **Validates: Requirements 8.3**
    """

    @given(
        session_id=non_existent_session_id_strategy(),
        format=valid_format_strategy
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_non_existent_session_returns_404(self, session_id, format):
        """
        Property: Non-existent session download requests return 404.
        
        **Feature: frontend-backend-integration, Property 9: Non-existent session returns 404**
        **Validates: Requirements 8.3**
        """
        response = client.get(f"/api/sessions/{session_id}/download", params={"format": format})
        
        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}. "
            f"Session ID: {session_id}, Format: {format}"
        )
        
        # Verify error details are provided
        error_response = response.json()
        assert "detail" in error_response, "Error response should contain 'detail' field"
        assert "not found" in error_response["detail"].lower(), (
            f"Error message should indicate session not found, got: {error_response['detail']}"
        )


class TestIncompleteSessionDownloadProperty:
    """
    **Feature: frontend-backend-integration, Property 10: Incomplete session download rejection**
    
    *For any* session with status other than "completed", requests to the download 
    endpoint SHALL return a 400 status code indicating the paper is not yet available.
    
    **Validates: Requirements 8.4**
    """

    @given(
        status=incomplete_status_strategy,
        format=valid_format_strategy,
        config=valid_session_config_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_incomplete_session_download_returns_400(self, status, format, config):
        """
        Property: Incomplete session download requests return 400.
        
        **Feature: frontend-backend-integration, Property 10: Incomplete session download rejection**
        **Validates: Requirements 8.4**
        """
        # Create a test session with the given incomplete status
        session_id = f"test-session-{int(datetime.now().timestamp() * 1000000)}"
        
        test_session = {
            "id": session_id,
            "config": config,
            "status": status,
            "stages": [
                {"id": "stage-1", "name": "Literature Review", "status": "pending", "progress": 0},
            ],
            "metrics": {
                "originalityScore": 0,
                "noveltyScore": 0,
                "plagiarismScore": 0,
                "ethicsScore": 0,
                "totalAgents": 5,
                "activeAgents": 0,
                "tasksCompleted": 0,
                "apiCalls": 0,
            },
            "agents": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }
        
        # Add session to storage
        sessions[session_id] = test_session
        
        try:
            response = client.get(f"/api/sessions/{session_id}/download", params={"format": format})
            
            assert response.status_code == 400, (
                f"Expected 400 for incomplete session (status={status}), got {response.status_code}. "
                f"Session ID: {session_id}, Format: {format}"
            )
            
            # Verify error details are provided
            error_response = response.json()
            assert "detail" in error_response, "Error response should contain 'detail' field"
            assert "not yet available" in error_response["detail"].lower() or "completed" in error_response["detail"].lower(), (
                f"Error message should indicate paper not available, got: {error_response['detail']}"
            )
        finally:
            # Clean up: remove test session
            if session_id in sessions:
                del sessions[session_id]


class TestCompletedSessionDownloadProperty:
    """
    Additional property test to verify completed sessions CAN be downloaded.
    This ensures the download endpoint works correctly for valid cases.
    """

    @given(
        format=valid_format_strategy,
        config=valid_session_config_strategy()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_completed_session_download_succeeds(self, format, config):
        """
        Property: Completed session download requests succeed with appropriate content type.
        """
        # Create a test session with completed status
        session_id = f"test-completed-{int(datetime.now().timestamp() * 1000000)}"
        
        test_session = {
            "id": session_id,
            "config": config,
            "status": "completed",
            "stages": [
                {"id": "stage-1", "name": "Literature Review", "status": "completed", "progress": 100},
            ],
            "metrics": {
                "originalityScore": 95,
                "noveltyScore": 90,
                "plagiarismScore": 5,
                "ethicsScore": 98,
                "totalAgents": 5,
                "activeAgents": 0,
                "tasksCompleted": 10,
                "apiCalls": 50,
            },
            "agents": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }
        
        # Add session to storage
        sessions[session_id] = test_session
        
        try:
            response = client.get(f"/api/sessions/{session_id}/download", params={"format": format})
            
            assert response.status_code == 200, (
                f"Expected 200 for completed session, got {response.status_code}. "
                f"Session ID: {session_id}, Format: {format}"
            )
            
            # Verify correct content type
            expected_content_type = "application/pdf" if format == "pdf" else "application/x-latex"
            assert expected_content_type in response.headers.get("content-type", ""), (
                f"Expected content-type {expected_content_type}, got {response.headers.get('content-type')}"
            )
            
            # Verify content is not empty
            assert len(response.content) > 0, "Response content should not be empty"
            
        finally:
            # Clean up: remove test session
            if session_id in sessions:
                del sessions[session_id]
