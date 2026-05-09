from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models import (
    AppSettings, Interaction, MeetingPrep, PatternInsight,
    Project, Stakeholder
)


# --- Settings ---

def get_settings(db: Session) -> AppSettings:
    settings = db.query(AppSettings).first()
    if not settings:
        settings = AppSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, ai_enabled: bool, openai_model: str) -> AppSettings:
    settings = get_settings(db)
    settings.ai_enabled = ai_enabled
    settings.openai_model = openai_model
    db.commit()
    db.refresh(settings)
    return settings


# --- Stakeholders ---

def get_stakeholders(db: Session):
    return db.query(Stakeholder).order_by(Stakeholder.name).all()


def get_stakeholder(db: Session, stakeholder_id: int) -> Optional[Stakeholder]:
    return db.query(Stakeholder).filter(Stakeholder.id == stakeholder_id).first()


def create_stakeholder(db: Session, data: dict) -> Stakeholder:
    s = Stakeholder(**data)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_stakeholder(db: Session, stakeholder_id: int, data: dict) -> Optional[Stakeholder]:
    s = get_stakeholder(db, stakeholder_id)
    if not s:
        return None
    for k, v in data.items():
        setattr(s, k, v)
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return s


def delete_stakeholder(db: Session, stakeholder_id: int) -> bool:
    s = get_stakeholder(db, stakeholder_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


# --- Projects ---

def get_projects(db: Session):
    return db.query(Project).order_by(Project.name).all()


def get_project(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def create_project(db: Session, data: dict) -> Project:
    p = Project(**data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def update_project(db: Session, project_id: int, data: dict) -> Optional[Project]:
    p = get_project(db, project_id)
    if not p:
        return None
    for k, v in data.items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return p


def delete_project(db: Session, project_id: int) -> bool:
    p = get_project(db, project_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True


# --- Interactions ---

def get_interactions(db: Session, limit: int = 50):
    return db.query(Interaction).order_by(Interaction.date.desc()).limit(limit).all()


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def create_interaction(db: Session, data: dict, stakeholder_ids: list, project_id: Optional[int]) -> Interaction:
    data["project_id"] = project_id
    interaction = Interaction(**data)
    if stakeholder_ids:
        stakeholders = db.query(Stakeholder).filter(Stakeholder.id.in_(stakeholder_ids)).all()
        interaction.stakeholders = stakeholders
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def update_interaction(db: Session, interaction_id: int, data: dict, stakeholder_ids: list, project_id: Optional[int]) -> Optional[Interaction]:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return None
    data["project_id"] = project_id
    for k, v in data.items():
        setattr(interaction, k, v)
    if stakeholder_ids is not None:
        interaction.stakeholders = db.query(Stakeholder).filter(Stakeholder.id.in_(stakeholder_ids)).all()
    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return interaction


def delete_interaction(db: Session, interaction_id: int) -> bool:
    i = get_interaction(db, interaction_id)
    if not i:
        return False
    db.delete(i)
    db.commit()
    return True


# --- Pattern Insights ---

def get_insights(db: Session, status: str = "active"):
    return db.query(PatternInsight).filter(
        PatternInsight.status == status
    ).order_by(PatternInsight.created_at.desc()).all()


def get_insight(db: Session, insight_id: int) -> Optional[PatternInsight]:
    return db.query(PatternInsight).filter(PatternInsight.id == insight_id).first()


def create_insight(db: Session, data: dict, stakeholder_ids: list = None, interaction_ids: list = None) -> PatternInsight:
    pi = PatternInsight(**data)
    if stakeholder_ids:
        pi.stakeholders = db.query(Stakeholder).filter(Stakeholder.id.in_(stakeholder_ids)).all()
    if interaction_ids:
        pi.interactions = db.query(Interaction).filter(Interaction.id.in_(interaction_ids)).all()
    db.add(pi)
    db.commit()
    db.refresh(pi)
    return pi


def archive_insight(db: Session, insight_id: int) -> bool:
    pi = get_insight(db, insight_id)
    if not pi:
        return False
    pi.status = "archived"
    db.commit()
    return True


def delete_insight(db: Session, insight_id: int) -> bool:
    pi = get_insight(db, insight_id)
    if not pi:
        return False
    db.delete(pi)
    db.commit()
    return True


# --- Meeting Prep ---

def get_meeting_preps(db: Session):
    return db.query(MeetingPrep).order_by(MeetingPrep.meeting_date.desc()).all()


def get_meeting_prep(db: Session, prep_id: int) -> Optional[MeetingPrep]:
    return db.query(MeetingPrep).filter(MeetingPrep.id == prep_id).first()


def create_meeting_prep(db: Session, data: dict, stakeholder_ids: list, project_id: Optional[int]) -> MeetingPrep:
    data["project_id"] = project_id
    prep = MeetingPrep(**data)
    if stakeholder_ids:
        prep.stakeholders = db.query(Stakeholder).filter(Stakeholder.id.in_(stakeholder_ids)).all()
    db.add(prep)
    db.commit()
    db.refresh(prep)
    return prep


def update_meeting_prep(db: Session, prep_id: int, data: dict, stakeholder_ids: list = None) -> Optional[MeetingPrep]:
    prep = get_meeting_prep(db, prep_id)
    if not prep:
        return None
    for k, v in data.items():
        setattr(prep, k, v)
    if stakeholder_ids is not None:
        prep.stakeholders = db.query(Stakeholder).filter(Stakeholder.id.in_(stakeholder_ids)).all()
    db.commit()
    db.refresh(prep)
    return prep


def delete_meeting_prep(db: Session, prep_id: int) -> bool:
    prep = get_meeting_prep(db, prep_id)
    if not prep:
        return False
    db.delete(prep)
    db.commit()
    return True


# --- Export ---

def export_all_data(db: Session) -> dict:
    from sqlalchemy import inspect

    def to_dict(obj):
        result = {}
        for c in inspect(obj).mapper.column_attrs:
            val = getattr(obj, c.key)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[c.key] = val
        return result

    return {
        "stakeholders": [to_dict(s) for s in db.query(Stakeholder).all()],
        "projects": [to_dict(p) for p in db.query(Project).all()],
        "interactions": [to_dict(i) for i in db.query(Interaction).all()],
        "pattern_insights": [to_dict(pi) for pi in db.query(PatternInsight).all()],
        "meeting_preps": [to_dict(mp) for mp in db.query(MeetingPrep).all()],
    }


def delete_all_data(db: Session):
    db.query(MeetingPrep).delete()
    db.query(PatternInsight).delete()
    db.query(Interaction).delete()
    db.query(Project).delete()
    db.query(Stakeholder).delete()
    db.commit()


# --- Seed data ---

def seed_example_data(db: Session):
    if db.query(Stakeholder).count() > 0:
        return  # already seeded

    s1 = Stakeholder(
        name="Alex Chen",
        role_title="Chief Technology Officer",
        team_or_area="Technology",
        influence_level="very_high",
        trust_level="medium",
        relationship_type="manager",
        stated_goals="Deliver MDG platform by Q3, reduce technical debt",
        likely_incentives="Board visibility, platform credibility, avoiding delivery risk",
        communication_style="Direct in 1:1s, deflects in group settings when stakes are high",
        what_they_care_about="Delivery certainty, clean architecture, not being surprised",
        what_they_resist="Scope changes late in cycle, public escalations, ambiguity about ownership",
        what_earns_trust="Clear written updates before meetings, flagging risks early, owning problems",
        tension_triggers="When delivery risk surfaces in SteerCo without prior notice",
        preferred_detail_level="medium",
        ambiguity_tolerance="low",
        notes="Example stakeholder — delete when you add your own.",
    )

    s2 = Stakeholder(
        name="Jordan Marsh",
        role_title="Head of Product",
        team_or_area="Product",
        influence_level="high",
        trust_level="high",
        relationship_type="peer",
        stated_goals="Ship UGS v2, expand product scope into analytics",
        likely_incentives="Product credibility, roadmap control, user adoption metrics",
        communication_style="Collaborative in planning, becomes territorial when scope overlaps",
        what_they_care_about="Roadmap ownership, user outcomes, recognition at exec level",
        what_they_resist="Being pulled into operational issues, technical complexity dominating product discussions",
        what_earns_trust="Crediting them publicly, protecting their roadmap in cross-functional discussions",
        tension_triggers="When engineering timelines override product commitments without discussion",
        preferred_detail_level="low",
        ambiguity_tolerance="high",
        notes="Example stakeholder — delete when you add your own.",
    )

    db.add_all([s1, s2])
    db.flush()

    p1 = Project(
        name="MDG Platform",
        description="Multi-dimensional growth platform — core data infrastructure for analytics and ML",
        strategic_importance="high",
        current_status="In development, Q3 target",
        main_tensions="Resource allocation between platform and product features; ownership of data quality standards",
        desired_outcome="Production-ready platform with clear data contracts and documented ownership",
        risks="Timeline pressure creating quality shortcuts; unclear decision rights on allocation model",
    )

    p2 = Project(
        name="Team Leadership Transition",
        description="Senior engineer leaving; need to restructure team ownership and fill capability gap",
        strategic_importance="high",
        current_status="Active — senior engineer giving 6 weeks notice",
        main_tensions="Whether to backfill externally or promote internally; timing against delivery commitments",
        desired_outcome="Clear ownership transfer, no delivery disruption, team morale maintained",
        risks="Knowledge concentration risk; team anxiety about change affecting productivity",
    )

    db.add_all([p1, p2])
    db.flush()

    i1 = Interaction(
        date=datetime(2026, 5, 1, 10, 0),
        title="MDG SteerCo — Q2 progress review",
        project_id=p1.id,
        interaction_type="presentation",
        what_happened="Presented Q2 status. Alex asked detailed questions about data quality thresholds. Jordan stayed quiet until the allocation model came up, then pushed back.",
        what_was_said="Alex: 'What's the minimum viable quality standard for production?' Jordan: 'We can't let the model delay the product roadmap again.'",
        what_was_unsaid="Nobody named the underlying tension: who owns the allocation decision.",
        user_goal="Get alignment on Q3 scope and surface the allocation question",
        actual_outcome="Partial. Q3 scope approved. Allocation question deferred again.",
        tension_level=3,
        confidence_level=3,
        clarity_level=2,
        emotional_response="Frustrated by the deferral. Felt I over-explained the technical constraints instead of naming the decision that was needed.",
        leadership_behaviour="Explained the model in detail. Did not directly ask who owns the allocation decision.",
        shrink_expand_rating="shrank",
        did_overexplain=True,
        did_soften_message=True,
        did_hold_boundary=False,
        did_avoid_ask=True,
        did_claim_authority=False,
        what_i_wanted_to_say="We need a decision on who owns allocation — this is the third time it's been deferred.",
        what_i_actually_said="The model requires a minimum quality threshold before we can scale. There are trade-offs we should probably discuss at some point.",
        what_i_would_do_next_time="Name the decision explicitly. Bring a one-page decision framework in advance.",
        next_action="Draft a decision framework on allocation ownership. Send to Alex before next SteerCo.",
        needs_documentation=True,
        stakeholders=[s1, s2],
    )

    db.add(i1)
    db.commit()
