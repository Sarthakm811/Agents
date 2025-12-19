"""
Property-based tests for settings validation.

**Feature: frontend-backend-integration, Property 8: Invalid settings rejection**
**Validates: Requirements 7.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# Strategy for generating invalid email formats
@st.composite
def invalid_email_strategy(draw):
    """Generate strings that are not valid email addresses."""
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Missing @ symbol - simple alphanumeric string
        return draw(st.from_regex(r'[a-zA-Z0-9]{3,20}', fullmatch=True))
    elif choice == 1:
        # Missing domain after @
        local = draw(st.from_regex(r'[a-zA-Z0-9]{1,10}', fullmatch=True))
        return f"{local}@"
    elif choice == 2:
        # Missing local part before @
        domain = draw(st.from_regex(r'[a-zA-Z0-9]{1,10}', fullmatch=True))
        return f"@{domain}.com"
    elif choice == 3:
        # Multiple @ symbols
        part1 = draw(st.from_regex(r'[a-zA-Z]{1,5}', fullmatch=True))
        part2 = draw(st.from_regex(r'[a-zA-Z]{1,5}', fullmatch=True))
        return f"{part1}@@{part2}"
    else:
        # Empty string
        return ""


# Strategy for valid preferences
valid_preferences_strategy = st.fixed_dictionaries({
    "autoStartEthicsReview": st.booleans(),
    "enablePlagiarismDetection": st.booleans(),
    "realTimeNotifications": st.booleans()
})


# Strategy for invalid settings (missing required fields)
@st.composite
def missing_field_settings_strategy(draw):
    """Generate settings objects with missing required fields."""
    # Randomly decide which fields to include (0-3 fields, ensuring at least one is missing)
    include_fullName = draw(st.booleans())
    include_email = draw(st.booleans())
    include_institution = draw(st.booleans())
    include_preferences = draw(st.booleans())
    
    # Ensure at least one required field is missing
    assume(not (include_fullName and include_email and include_institution and include_preferences))
    
    result = {}
    if include_fullName:
        result["fullName"] = draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True))
    if include_email:
        result["email"] = draw(st.emails())
    if include_institution:
        result["institution"] = draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True))
    if include_preferences:
        result["preferences"] = draw(valid_preferences_strategy)
    
    return result


# Strategy for settings with invalid email
@st.composite
def invalid_email_settings_strategy(draw):
    """Generate settings objects with invalid email format."""
    return {
        "fullName": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
        "email": draw(invalid_email_strategy()),
        "institution": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
        "preferences": draw(valid_preferences_strategy)
    }


# Strategy for settings with wrong types that Pydantic cannot coerce
@st.composite
def wrong_type_settings_strategy(draw):
    """Generate settings objects with wrong field types that cannot be coerced."""
    choice = draw(st.integers(min_value=0, max_value=2))
    
    if choice == 0:
        # fullName as a list (cannot be coerced to string)
        return {
            "fullName": draw(st.lists(st.integers(), min_size=1, max_size=3)),
            "email": draw(st.emails()),
            "institution": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
            "preferences": draw(valid_preferences_strategy)
        }
    elif choice == 1:
        # preferences as a non-dict type (list instead of object)
        return {
            "fullName": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
            "email": draw(st.emails()),
            "institution": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
            "preferences": draw(st.lists(st.booleans(), min_size=1, max_size=3))
        }
    else:
        # preferences with invalid nested types (list instead of boolean)
        return {
            "fullName": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
            "email": draw(st.emails()),
            "institution": draw(st.from_regex(r'[A-Za-z ]{1,30}', fullmatch=True)),
            "preferences": {
                "autoStartEthicsReview": draw(st.lists(st.integers(), min_size=1, max_size=2)),
                "enablePlagiarismDetection": draw(valid_preferences_strategy),  # nested dict instead of bool
                "realTimeNotifications": True
            }
        }


class TestSettingsValidationProperty:
    """
    **Feature: frontend-backend-integration, Property 8: Invalid settings rejection**
    
    *For any* settings object with invalid data (missing required fields, invalid email format, 
    or wrong types), the backend SHALL return a 400 status code with validation error details.
    
    **Validates: Requirements 7.3**
    """

    @given(settings_data=missing_field_settings_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_missing_required_fields_returns_422(self, settings_data):
        """
        Property: Settings with missing required fields are rejected with 422.
        
        **Feature: frontend-backend-integration, Property 8: Invalid settings rejection**
        **Validates: Requirements 7.3**
        """
        response = client.post("/api/settings", json=settings_data)
        
        assert response.status_code == 422, (
            f"Expected 422 for missing fields, got {response.status_code}. "
            f"Data: {settings_data}"
        )
        
        # Verify error details are provided
        error_response = response.json()
        assert "detail" in error_response, "Error response should contain 'detail' field"

    @given(settings_data=invalid_email_settings_strategy())
    @settings(max_examples=100)
    def test_invalid_email_format_returns_422(self, settings_data):
        """
        Property: Settings with invalid email format are rejected with 422.
        
        **Feature: frontend-backend-integration, Property 8: Invalid settings rejection**
        **Validates: Requirements 7.3**
        """
        response = client.post("/api/settings", json=settings_data)
        
        assert response.status_code == 422, (
            f"Expected 422 for invalid email, got {response.status_code}. "
            f"Email: {settings_data.get('email')}"
        )
        
        # Verify error details mention email validation
        error_response = response.json()
        assert "detail" in error_response, "Error response should contain 'detail' field"

    @given(settings_data=wrong_type_settings_strategy())
    @settings(max_examples=100)
    def test_wrong_field_types_returns_422(self, settings_data):
        """
        Property: Settings with wrong field types are rejected with 422.
        
        **Feature: frontend-backend-integration, Property 8: Invalid settings rejection**
        **Validates: Requirements 7.3**
        """
        response = client.post("/api/settings", json=settings_data)
        
        assert response.status_code == 422, (
            f"Expected 422 for wrong types, got {response.status_code}. "
            f"Data: {settings_data}"
        )
        
        # Verify error details are provided
        error_response = response.json()
        assert "detail" in error_response, "Error response should contain 'detail' field"
