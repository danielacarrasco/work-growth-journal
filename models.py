from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Table, Text
)
from sqlalchemy.orm import relationship
from database import Base

# --- Association tables ---

interaction_stakeholders = Table(
    "interaction_stakeholders",
    Base.metadata,
    Column("interaction_id", Integer, ForeignKey("interactions.id", ondelete="CASCADE")),
    Column("stakeholder_id", Integer, ForeignKey("stakeholders.id", ondelete="CASCADE")),
)

meeting_prep_stakeholders = Table(
    "meeting_prep_stakeholders",
    Base.metadata,
    Column("meeting_prep_id", Integer, ForeignKey("meeting_preps.id", ondelete="CASCADE")),
    Column("stakeholder_id", Integer, ForeignKey("stakeholders.id", ondelete="CASCADE")),
)

pattern_stakeholders = Table(
    "pattern_stakeholders",
    Base.metadata,
    Column("pattern_id", Integer, ForeignKey("pattern_insights.id", ondelete="CASCADE")),
    Column("stakeholder_id", Integer, ForeignKey("stakeholders.id", ondelete="CASCADE")),
)

pattern_interactions = Table(
    "pattern_interactions",
    Base.metadata,
    Column("pattern_id", Integer, ForeignKey("pattern_insights.id", ondelete="CASCADE")),
    Column("interaction_id", Integer, ForeignKey("interactions.id", ondelete="CASCADE")),
)


# --- Models ---

class Stakeholder(Base):
    __tablename__ = "stakeholders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    role_title = Column(String(200))
    team_or_area = Column(String(200))
    influence_level = Column(Enum("low", "medium", "high", "very_high", name="influence_level"), default="medium")
    trust_level = Column(Enum("low", "medium", "high", "unknown", name="trust_level"), default="unknown")
    relationship_type = Column(
        Enum("ally", "sponsor", "blocker", "operator", "interpreter", "peer",
             "manager", "direct_report", "unknown", name="relationship_type"),
        default="unknown"
    )
    stated_goals = Column(Text)
    likely_incentives = Column(Text)
    communication_style = Column(Text)
    what_they_care_about = Column(Text)
    what_they_resist = Column(Text)
    what_earns_trust = Column(Text)
    tension_triggers = Column(Text)
    preferred_detail_level = Column(
        Enum("low", "medium", "high", "unknown", name="detail_level"),
        default="unknown"
    )
    ambiguity_tolerance = Column(
        Enum("low", "medium", "high", "unknown", name="ambiguity_tolerance"),
        default="unknown"
    )
    notes = Column(Text)
    ai_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship(
        "Interaction",
        secondary=interaction_stakeholders,
        back_populates="stakeholders",
    )
    meeting_preps = relationship(
        "MeetingPrep",
        secondary=meeting_prep_stakeholders,
        back_populates="stakeholders",
    )
    pattern_insights = relationship(
        "PatternInsight",
        secondary=pattern_stakeholders,
        back_populates="stakeholders",
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    strategic_importance = Column(
        Enum("low", "medium", "high", name="strategic_importance"),
        default="medium"
    )
    current_status = Column(Text)
    main_tensions = Column(Text)
    desired_outcome = Column(Text)
    risks = Column(Text)
    political_weather = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="project")
    meeting_preps = relationship("MeetingPrep", back_populates="project")
    pattern_insights = relationship("PatternInsight", back_populates="project")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    title = Column(String(300), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    interaction_type = Column(
        Enum("meeting", "1:1", "slack", "email", "workshop", "presentation", "informal", "other",
             name="interaction_type"),
        default="meeting"
    )
    what_happened = Column(Text)
    what_was_said = Column(Text)
    what_was_unsaid = Column(Text)
    user_goal = Column(Text)
    actual_outcome = Column(Text)
    tension_level = Column(Integer)  # 1-5
    confidence_level = Column(Integer)  # 1-5
    clarity_level = Column(Integer)  # 1-5
    emotional_response = Column(Text)
    leadership_behaviour = Column(Text)
    shrink_expand_rating = Column(
        Enum("strongly_shrank", "shrank", "neutral", "expanded", "strongly_expanded",
             name="shrink_expand"),
        default="neutral"
    )
    did_overexplain = Column(Boolean, default=False)
    did_soften_message = Column(Boolean, default=False)
    did_hold_boundary = Column(Boolean, default=False)
    did_avoid_ask = Column(Boolean, default=False)
    did_claim_authority = Column(Boolean, default=False)
    what_i_wanted_to_say = Column(Text)
    what_i_actually_said = Column(Text)
    what_i_would_do_next_time = Column(Text)
    next_action = Column(Text)
    needs_documentation = Column(Boolean, default=False)
    ai_insight = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="interactions")
    stakeholders = relationship(
        "Stakeholder",
        secondary=interaction_stakeholders,
        back_populates="interactions",
    )
    pattern_insights = relationship(
        "PatternInsight",
        secondary=pattern_interactions,
        back_populates="interactions",
    )


class PatternInsight(Base):
    __tablename__ = "pattern_insights"

    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(
        Enum("stakeholder_pattern", "self_pattern", "project_pattern",
             "political_weather", "recommendation", name="insight_type"),
        nullable=False
    )
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=False)
    evidence = Column(Text)
    related_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Enum("low", "medium", "high", name="confidence"), default="medium")
    status = Column(Enum("active", "archived", name="insight_status"), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="pattern_insights")
    stakeholders = relationship(
        "Stakeholder",
        secondary=pattern_stakeholders,
        back_populates="pattern_insights",
    )
    interactions = relationship(
        "Interaction",
        secondary=pattern_interactions,
        back_populates="pattern_insights",
    )


class MeetingPrep(Base):
    __tablename__ = "meeting_preps"

    id = Column(Integer, primary_key=True, index=True)
    meeting_title = Column(String(300), nullable=False)
    meeting_date = Column(DateTime)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    desired_outcome = Column(Text)
    likely_resistance = Column(Text)
    emotional_risk = Column(Text)
    what_i_am_tempted_to_do_badly = Column(Text)
    advisor_voices = Column(String(500))  # comma-separated list
    generated_strategy = Column(Text)
    suggested_talking_points = Column(Text)
    what_to_avoid = Column(Text)
    where_to_hold_firm = Column(Text)
    where_to_stay_flexible = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="meeting_preps")
    stakeholders = relationship(
        "Stakeholder",
        secondary=meeting_prep_stakeholders,
        back_populates="meeting_preps",
    )


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    ai_enabled = Column(Boolean, default=True)
    openai_model = Column(String(100), default="gpt-4o")
