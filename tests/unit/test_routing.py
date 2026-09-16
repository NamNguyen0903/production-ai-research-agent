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
        "tool_calls": 0,
        "max_tool_calls": 15,
        "retry_queries": ["targeted query"],
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


def test_finish_when_tool_budget_exhausted():
    state = {
        "iteration": 1,
        "max_iterations": 3,
        "tool_calls": 15,
        "max_tool_calls": 15,
        "retry_queries": ["targeted query"],
        "verification": VerificationResult(
            passed=False,
            coverage_score=0.5,
        ),
    }

    assert route_after_verification(state) == "finish"


def test_finish_when_no_retry_queries():
    state = {
        "iteration": 1,
        "max_iterations": 3,
        "tool_calls": 3,
        "max_tool_calls": 15,
        "retry_queries": [],
        "verification": VerificationResult(
            passed=False,
            coverage_score=0.5,
        ),
    }

    assert route_after_verification(state) == "finish"


def test_retry_when_all_budgets_allow():
    state = {
        "iteration": 1,
        "max_iterations": 3,
        "tool_calls": 3,
        "max_tool_calls": 15,
        "retry_queries": ["targeted query"],
        "verification": VerificationResult(
            passed=False,
            coverage_score=0.5,
        ),
    }

    assert route_after_verification(state) == "retry"
