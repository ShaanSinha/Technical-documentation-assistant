import pytest
from pydantic import ValidationError

from app.routes.api import QueryRequest, FeedbackRequest


def test_query_request_rejects_too_short_question():
    with pytest.raises(ValidationError):
        QueryRequest(question="hi")


def test_feedback_request_accepts_up_rating():
    request = FeedbackRequest(question="How?", answer="Because.", rating="up")
    assert request.rating == "up"


def test_feedback_request_rejects_invalid_rating():
    with pytest.raises(ValidationError):
        FeedbackRequest(question="How?", answer="Because.", rating="maybe")
