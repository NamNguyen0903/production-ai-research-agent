import pytest
from pydantic import ValidationError

from app.models.research import ResearchPlan, ResearchStep


def test_research_plan_accepts_valid_steps():
    plan = ResearchPlan(
        steps=[
            ResearchStep(
                id="step-1",
                question="Which SLMs are currently available?",
                rationale="Identify major current model families.",
            ),
            ResearchStep(
                id="step-2",
                question="How do current SLMs compare?",
                rationale="Compare their technical tradeoffs.",
            ),
        ]
    )

    assert len(plan.steps) == 2


def test_research_plan_requires_at_least_two_steps():
    with pytest.raises(ValidationError):
        ResearchPlan(
            steps=[
                ResearchStep(
                    id="step-1",
                    question="Which SLMs are currently available?",
                    rationale="Identify current model families.",
                )
            ]
        )


def test_research_plan_allows_maximum_five_steps():
    steps = [
        ResearchStep(
            id=f"step-{index}",
            question=f"Research question number {index}?",
            rationale=f"Research rationale number {index}.",
        )
        for index in range(1, 6)
    ]

    plan = ResearchPlan(steps=steps)

    assert len(plan.steps) == 5


def test_research_plan_rejects_more_than_five_steps():
    steps = [
        ResearchStep(
            id=f"step-{index}",
            question=f"Research question number {index}?",
            rationale=f"Research rationale number {index}.",
        )
        for index in range(1, 7)
    ]

    with pytest.raises(ValidationError):
        ResearchPlan(steps=steps)
