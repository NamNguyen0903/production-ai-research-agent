from app.agent.routing import route_after_verification
from app.models.verification import VerificationResult


def test_finish_when_verification_passes():
    state = {
        "iteration": 1,
        "max_iterations": 2,
        "verification": VerificationResult(
            passed=True,
            coverage_score=1.0,
        ),
    }

    result = route_after_verification(state)

    assert result == "finish"


def test_retry_when_verification_fails():
    state = {
        "iteration": 1,
        "max_iterations": 2,
        "verification": VerificationResult(
            passed=False,
            coverage_score=0.5,
        ),
    }

    result = route_after_verification(state)

    assert result == "retry"


def test_finish_when_retry_budget_is_exhausted():
    state = {
        "iteration": 2,
        "max_iterations": 2,
        "verification": VerificationResult(
            passed=False,
            coverage_score=0.5,
        ),
    }

    result = route_after_verification(state)

    assert result == "finish"
