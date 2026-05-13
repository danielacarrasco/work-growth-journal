import json
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud
import ai_service
from database import Base, engine, get_db
from models import (
    AppSettings, Interaction, MeetingPrep, PatternInsight,
    Project, Stakeholder
)

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Work Mirror")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

AI_ENABLED_ENV = os.getenv("AI_ENABLED", "true").lower() == "true"


def flash(request: Request, message: str, category: str = "info"):
    if not hasattr(request.state, "flash_messages"):
        request.state.flash_messages = []
    request.state.flash_messages.append({"message": message, "category": category})


def get_ai_enabled(db: Session) -> bool:
    if not AI_ENABLED_ENV:
        return False
    settings = crud.get_settings(db)
    return settings.ai_enabled


def common_context(request: Request, db: Session) -> dict:
    settings = crud.get_settings(db)
    return {
        "request": request,
        "ai_enabled": get_ai_enabled(db),
        "settings": settings,
        "now": datetime.utcnow(),
    }


# ============================================================
# HOME
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["recent_interactions"] = crud.get_interactions(db, limit=5)
    ctx["upcoming_preps"] = crud.get_meeting_preps(db)[:3]
    ctx["latest_insights"] = crud.get_insights(db)[:3]
    return templates.TemplateResponse("home.html", ctx)


# ============================================================
# STAKEHOLDERS
# ============================================================

@app.get("/stakeholders", response_class=HTMLResponse)
async def stakeholders_list(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["stakeholders"] = crud.get_stakeholders(db)
    return templates.TemplateResponse("stakeholders/list.html", ctx)


@app.get("/stakeholders/new", response_class=HTMLResponse)
async def stakeholder_new(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["stakeholder"] = None
    ctx["form_action"] = "/stakeholders"
    return templates.TemplateResponse("stakeholders/form.html", ctx)


@app.post("/stakeholders", response_class=HTMLResponse)
async def stakeholder_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    role_title: str = Form(""),
    team_or_area: str = Form(""),
    influence_level: str = Form("medium"),
    trust_level: str = Form("unknown"),
    relationship_type: str = Form("unknown"),
    stated_goals: str = Form(""),
    likely_incentives: str = Form(""),
    communication_style: str = Form(""),
    what_they_care_about: str = Form(""),
    what_they_resist: str = Form(""),
    what_earns_trust: str = Form(""),
    tension_triggers: str = Form(""),
    preferred_detail_level: str = Form("unknown"),
    ambiguity_tolerance: str = Form("unknown"),
    notes: str = Form(""),
):
    data = {
        "name": name,
        "role_title": role_title or None,
        "team_or_area": team_or_area or None,
        "influence_level": influence_level,
        "trust_level": trust_level,
        "relationship_type": relationship_type,
        "stated_goals": stated_goals or None,
        "likely_incentives": likely_incentives or None,
        "communication_style": communication_style or None,
        "what_they_care_about": what_they_care_about or None,
        "what_they_resist": what_they_resist or None,
        "what_earns_trust": what_earns_trust or None,
        "tension_triggers": tension_triggers or None,
        "preferred_detail_level": preferred_detail_level,
        "ambiguity_tolerance": ambiguity_tolerance,
        "notes": notes or None,
    }
    s = crud.create_stakeholder(db, data)
    return RedirectResponse(f"/stakeholders/{s.id}", status_code=303)


@app.get("/stakeholders/{stakeholder_id}", response_class=HTMLResponse)
async def stakeholder_detail(
    stakeholder_id: int, request: Request, db: Session = Depends(get_db)
):
    s = crud.get_stakeholder(db, stakeholder_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    ctx = common_context(request, db)
    ctx["stakeholder"] = s
    ctx["interactions"] = sorted(s.interactions, key=lambda i: i.date, reverse=True)[:10]
    return templates.TemplateResponse("stakeholders/detail.html", ctx)


@app.get("/stakeholders/{stakeholder_id}/edit", response_class=HTMLResponse)
async def stakeholder_edit(
    stakeholder_id: int, request: Request, db: Session = Depends(get_db)
):
    s = crud.get_stakeholder(db, stakeholder_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    ctx = common_context(request, db)
    ctx["stakeholder"] = s
    ctx["form_action"] = f"/stakeholders/{stakeholder_id}/edit"
    return templates.TemplateResponse("stakeholders/form.html", ctx)


@app.post("/stakeholders/{stakeholder_id}/edit", response_class=HTMLResponse)
async def stakeholder_update(
    stakeholder_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    role_title: str = Form(""),
    team_or_area: str = Form(""),
    influence_level: str = Form("medium"),
    trust_level: str = Form("unknown"),
    relationship_type: str = Form("unknown"),
    stated_goals: str = Form(""),
    likely_incentives: str = Form(""),
    communication_style: str = Form(""),
    what_they_care_about: str = Form(""),
    what_they_resist: str = Form(""),
    what_earns_trust: str = Form(""),
    tension_triggers: str = Form(""),
    preferred_detail_level: str = Form("unknown"),
    ambiguity_tolerance: str = Form("unknown"),
    notes: str = Form(""),
):
    data = {
        "name": name,
        "role_title": role_title or None,
        "team_or_area": team_or_area or None,
        "influence_level": influence_level,
        "trust_level": trust_level,
        "relationship_type": relationship_type,
        "stated_goals": stated_goals or None,
        "likely_incentives": likely_incentives or None,
        "communication_style": communication_style or None,
        "what_they_care_about": what_they_care_about or None,
        "what_they_resist": what_they_resist or None,
        "what_earns_trust": what_earns_trust or None,
        "tension_triggers": tension_triggers or None,
        "preferred_detail_level": preferred_detail_level,
        "ambiguity_tolerance": ambiguity_tolerance,
        "notes": notes or None,
    }
    crud.update_stakeholder(db, stakeholder_id, data)
    return RedirectResponse(f"/stakeholders/{stakeholder_id}", status_code=303)


@app.post("/stakeholders/{stakeholder_id}/delete")
async def stakeholder_delete(stakeholder_id: int, db: Session = Depends(get_db)):
    crud.delete_stakeholder(db, stakeholder_id)
    return RedirectResponse("/stakeholders", status_code=303)


@app.post("/stakeholders/{stakeholder_id}/generate-update", response_class=HTMLResponse)
async def stakeholder_generate_update(
    stakeholder_id: int, request: Request, db: Session = Depends(get_db)
):
    s = crud.get_stakeholder(db, stakeholder_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)

    stakeholder_dict = {
        "name": s.name,
        "role_title": s.role_title,
        "team_or_area": s.team_or_area,
        "influence_level": s.influence_level,
        "trust_level": s.trust_level,
        "relationship_type": s.relationship_type,
        "stated_goals": s.stated_goals,
        "likely_incentives": s.likely_incentives,
        "communication_style": s.communication_style,
        "what_they_care_about": s.what_they_care_about,
        "what_they_resist": s.what_they_resist,
        "what_earns_trust": s.what_earns_trust,
        "tension_triggers": s.tension_triggers,
        "notes": s.notes,
    }

    recent = sorted(s.interactions, key=lambda i: i.date, reverse=True)[:10]
    interactions_dicts = [
        {
            "date": str(i.date.date()),
            "title": i.title,
            "what_happened": i.what_happened,
            "what_was_said": i.what_was_said,
            "what_was_unsaid": i.what_was_unsaid,
            "actual_outcome": i.actual_outcome,
            "emotional_response": i.emotional_response,
            "leadership_behaviour": i.leadership_behaviour,
            "shrink_expand_rating": i.shrink_expand_rating,
            "what_i_wanted_to_say": i.what_i_wanted_to_say,
            "what_i_actually_said": i.what_i_actually_said,
        }
        for i in recent
    ]

    try:
        summary = ai_service.generate_stakeholder_update(
            stakeholder_dict, interactions_dicts, ai_on, settings.openai_model
        )
        crud.update_stakeholder(db, stakeholder_id, {"ai_summary": summary})
    except Exception:
        pass
    return RedirectResponse(f"/stakeholders/{stakeholder_id}", status_code=303)


# ============================================================
# PROJECTS
# ============================================================

@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["projects"] = crud.get_projects(db)
    return templates.TemplateResponse("projects/list.html", ctx)


@app.get("/projects/new", response_class=HTMLResponse)
async def project_new(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["project"] = None
    ctx["form_action"] = "/projects"
    return templates.TemplateResponse("projects/form.html", ctx)


@app.post("/projects", response_class=HTMLResponse)
async def project_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(""),
    strategic_importance: str = Form("medium"),
    current_status: str = Form(""),
    main_tensions: str = Form(""),
    desired_outcome: str = Form(""),
    risks: str = Form(""),
):
    data = {
        "name": name,
        "description": description or None,
        "strategic_importance": strategic_importance,
        "current_status": current_status or None,
        "main_tensions": main_tensions or None,
        "desired_outcome": desired_outcome or None,
        "risks": risks or None,
    }
    p = crud.create_project(db, data)
    return RedirectResponse(f"/projects/{p.id}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    project_id: int, request: Request, db: Session = Depends(get_db)
):
    p = crud.get_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    ctx = common_context(request, db)
    ctx["project"] = p
    ctx["interactions"] = sorted(p.interactions, key=lambda i: i.date, reverse=True)[:10]
    # Collect stakeholders from interactions
    stakeholder_ids = set()
    stakeholders = []
    for i in p.interactions:
        for s in i.stakeholders:
            if s.id not in stakeholder_ids:
                stakeholder_ids.add(s.id)
                stakeholders.append(s)
    ctx["stakeholders"] = stakeholders
    return templates.TemplateResponse("projects/detail.html", ctx)


@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def project_edit(
    project_id: int, request: Request, db: Session = Depends(get_db)
):
    p = crud.get_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    ctx = common_context(request, db)
    ctx["project"] = p
    ctx["form_action"] = f"/projects/{project_id}/edit"
    return templates.TemplateResponse("projects/form.html", ctx)


@app.post("/projects/{project_id}/edit", response_class=HTMLResponse)
async def project_update(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(""),
    strategic_importance: str = Form("medium"),
    current_status: str = Form(""),
    main_tensions: str = Form(""),
    desired_outcome: str = Form(""),
    risks: str = Form(""),
):
    data = {
        "name": name,
        "description": description or None,
        "strategic_importance": strategic_importance,
        "current_status": current_status or None,
        "main_tensions": main_tensions or None,
        "desired_outcome": desired_outcome or None,
        "risks": risks or None,
    }
    crud.update_project(db, project_id, data)
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/delete")
async def project_delete(project_id: int, db: Session = Depends(get_db)):
    crud.delete_project(db, project_id)
    return RedirectResponse("/projects", status_code=303)


@app.post("/projects/{project_id}/generate-weather", response_class=HTMLResponse)
async def project_generate_weather(
    project_id: int, request: Request, db: Session = Depends(get_db)
):
    p = crud.get_project(db, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)

    project_dict = {
        "name": p.name,
        "description": p.description,
        "strategic_importance": p.strategic_importance,
        "current_status": p.current_status,
        "main_tensions": p.main_tensions,
        "desired_outcome": p.desired_outcome,
        "risks": p.risks,
    }

    stakeholder_ids = set()
    stakeholders_dicts = []
    interactions_dicts = []

    for i in sorted(p.interactions, key=lambda x: x.date, reverse=True)[:15]:
        interactions_dicts.append({
            "date": str(i.date.date()),
            "title": i.title,
            "what_happened": i.what_happened,
            "what_was_said": i.what_was_said,
            "what_was_unsaid": i.what_was_unsaid,
            "actual_outcome": i.actual_outcome,
            "shrink_expand_rating": i.shrink_expand_rating,
        })
        for s in i.stakeholders:
            if s.id not in stakeholder_ids:
                stakeholder_ids.add(s.id)
                stakeholders_dicts.append({
                    "name": s.name,
                    "role_title": s.role_title,
                    "relationship_type": s.relationship_type,
                    "influence_level": s.influence_level,
                    "likely_incentives": s.likely_incentives,
                    "what_they_care_about": s.what_they_care_about,
                    "what_they_resist": s.what_they_resist,
                })

    try:
        weather = ai_service.generate_political_weather(
            project_dict, stakeholders_dicts, interactions_dicts, ai_on, settings.openai_model
        )
        crud.update_project(db, project_id, {"political_weather": weather})
    except Exception:
        pass
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


# ============================================================
# INTERACTIONS
# ============================================================

@app.get("/interactions", response_class=HTMLResponse)
async def interactions_list(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["interactions"] = crud.get_interactions(db, limit=50)
    return templates.TemplateResponse("interactions/list.html", ctx)


@app.get("/interactions/new", response_class=HTMLResponse)
async def interaction_new(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["interaction"] = None
    ctx["stakeholders"] = crud.get_stakeholders(db)
    ctx["projects"] = crud.get_projects(db)
    ctx["form_action"] = "/interactions"
    ctx["selected_stakeholder_ids"] = []
    ctx["selected_project_id"] = None
    return templates.TemplateResponse("interactions/form.html", ctx)


@app.post("/interactions", response_class=HTMLResponse)
async def interaction_create(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    data, stakeholder_ids, project_id = _parse_interaction_form(form)
    i = crud.create_interaction(db, data, stakeholder_ids, project_id)
    return RedirectResponse(f"/interactions/{i.id}", status_code=303)


@app.get("/interactions/{interaction_id}", response_class=HTMLResponse)
async def interaction_detail(
    interaction_id: int, request: Request, db: Session = Depends(get_db)
):
    i = crud.get_interaction(db, interaction_id)
    if not i:
        raise HTTPException(status_code=404, detail="Interaction not found")
    ctx = common_context(request, db)
    ctx["interaction"] = i
    return templates.TemplateResponse("interactions/detail.html", ctx)


@app.get("/interactions/{interaction_id}/edit", response_class=HTMLResponse)
async def interaction_edit(
    interaction_id: int, request: Request, db: Session = Depends(get_db)
):
    i = crud.get_interaction(db, interaction_id)
    if not i:
        raise HTTPException(status_code=404, detail="Interaction not found")
    ctx = common_context(request, db)
    ctx["interaction"] = i
    ctx["stakeholders"] = crud.get_stakeholders(db)
    ctx["projects"] = crud.get_projects(db)
    ctx["form_action"] = f"/interactions/{interaction_id}/edit"
    ctx["selected_stakeholder_ids"] = [s.id for s in i.stakeholders]
    ctx["selected_project_id"] = i.project_id
    return templates.TemplateResponse("interactions/form.html", ctx)


@app.post("/interactions/{interaction_id}/edit", response_class=HTMLResponse)
async def interaction_update(
    interaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    data, stakeholder_ids, project_id = _parse_interaction_form(form)
    crud.update_interaction(db, interaction_id, data, stakeholder_ids, project_id)
    return RedirectResponse(f"/interactions/{interaction_id}", status_code=303)


@app.post("/interactions/{interaction_id}/delete")
async def interaction_delete(interaction_id: int, db: Session = Depends(get_db)):
    crud.delete_interaction(db, interaction_id)
    return RedirectResponse("/interactions", status_code=303)


@app.post("/interactions/{interaction_id}/generate-insight", response_class=HTMLResponse)
async def interaction_generate_insight(
    interaction_id: int, request: Request, db: Session = Depends(get_db)
):
    i = crud.get_interaction(db, interaction_id)
    if not i:
        raise HTTPException(status_code=404, detail="Interaction not found")
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)

    # Get recent interactions for context
    recent = crud.get_interactions(db, limit=10)
    interactions_dicts = [
        {
            "date": str(x.date.date()),
            "title": x.title,
            "what_happened": x.what_happened,
            "what_was_said": x.what_was_said,
            "what_was_unsaid": x.what_was_unsaid,
            "actual_outcome": x.actual_outcome,
            "emotional_response": x.emotional_response,
            "leadership_behaviour": x.leadership_behaviour,
            "shrink_expand_rating": x.shrink_expand_rating,
            "did_overexplain": x.did_overexplain,
            "did_soften_message": x.did_soften_message,
            "did_hold_boundary": x.did_hold_boundary,
            "did_avoid_ask": x.did_avoid_ask,
            "did_claim_authority": x.did_claim_authority,
            "what_i_wanted_to_say": x.what_i_wanted_to_say,
            "what_i_actually_said": x.what_i_actually_said,
        }
        for x in recent
    ]

    try:
        insight_text = ai_service.generate_self_pattern_insight(
            interactions_dicts, ai_on, settings.openai_model
        )
        crud.update_interaction(db, interaction_id, {"ai_insight": insight_text})
        crud.create_insight(
            db,
            data={
                "insight_type": "self_pattern",
                "title": f"Self-pattern from {i.date.strftime('%d %b %Y')} interactions",
                "summary": insight_text[:500] + ("..." if len(insight_text) > 500 else ""),
                "evidence": insight_text,
                "confidence": "medium",
            },
            interaction_ids=[i.id],
        )
    except Exception:
        pass

    return RedirectResponse(f"/interactions/{interaction_id}", status_code=303)


def _parse_interaction_form(form) -> tuple:
    def get(key, default=""):
        val = form.get(key, default)
        return val if val else default

    def get_int(key):
        val = form.get(key)
        try:
            return int(val) if val else None
        except ValueError:
            return None

    def get_bool(key):
        return form.get(key) == "on"

    date_str = get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()
    except ValueError:
        date = datetime.utcnow()

    data = {
        "date": date,
        "title": get("title", "Untitled interaction"),
        "interaction_type": get("interaction_type", "meeting"),
        "what_happened": get("what_happened") or None,
        "what_was_said": get("what_was_said") or None,
        "what_was_unsaid": get("what_was_unsaid") or None,
        "user_goal": get("user_goal") or None,
        "actual_outcome": get("actual_outcome") or None,
        "tension_level": get_int("tension_level"),
        "confidence_level": get_int("confidence_level"),
        "clarity_level": get_int("clarity_level"),
        "emotional_response": get("emotional_response") or None,
        "leadership_behaviour": get("leadership_behaviour") or None,
        "shrink_expand_rating": get("shrink_expand_rating", "neutral"),
        "did_overexplain": get_bool("did_overexplain"),
        "did_soften_message": get_bool("did_soften_message"),
        "did_hold_boundary": get_bool("did_hold_boundary"),
        "did_avoid_ask": get_bool("did_avoid_ask"),
        "did_claim_authority": get_bool("did_claim_authority"),
        "what_i_wanted_to_say": get("what_i_wanted_to_say") or None,
        "what_i_actually_said": get("what_i_actually_said") or None,
        "what_i_would_do_next_time": get("what_i_would_do_next_time") or None,
        "next_action": get("next_action") or None,
        "needs_documentation": get_bool("needs_documentation"),
    }

    stakeholder_ids = [int(x) for x in form.getlist("stakeholder_ids") if x.isdigit()]
    project_id_raw = form.get("project_id")
    project_id = int(project_id_raw) if project_id_raw and project_id_raw.isdigit() else None

    return data, stakeholder_ids, project_id


# ============================================================
# PATTERNS
# ============================================================

@app.get("/patterns", response_class=HTMLResponse)
async def patterns_list(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    active = crud.get_insights(db, status="active")
    archived = crud.get_insights(db, status="archived")

    grouped = {}
    for insight in active:
        grouped.setdefault(insight.insight_type, []).append(insight)

    ctx["grouped_insights"] = grouped
    ctx["archived_insights"] = archived
    return templates.TemplateResponse("patterns/list.html", ctx)


@app.post("/patterns/{insight_id}/archive")
async def pattern_archive(insight_id: int, db: Session = Depends(get_db)):
    crud.archive_insight(db, insight_id)
    return RedirectResponse("/patterns", status_code=303)


@app.post("/patterns/{insight_id}/delete")
async def pattern_delete(insight_id: int, db: Session = Depends(get_db)):
    crud.delete_insight(db, insight_id)
    return RedirectResponse("/patterns", status_code=303)


@app.get("/patterns/generate-self", response_class=HTMLResponse)
async def pattern_generate_self(request: Request, db: Session = Depends(get_db)):
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)
    recent = crud.get_interactions(db, limit=15)

    interactions_dicts = [
        {
            "date": str(x.date.date()),
            "title": x.title,
            "what_happened": x.what_happened,
            "actual_outcome": x.actual_outcome,
            "emotional_response": x.emotional_response,
            "leadership_behaviour": x.leadership_behaviour,
            "shrink_expand_rating": x.shrink_expand_rating,
            "did_overexplain": x.did_overexplain,
            "did_soften_message": x.did_soften_message,
            "did_hold_boundary": x.did_hold_boundary,
            "did_avoid_ask": x.did_avoid_ask,
            "did_claim_authority": x.did_claim_authority,
            "what_i_wanted_to_say": x.what_i_wanted_to_say,
            "what_i_actually_said": x.what_i_actually_said,
        }
        for x in recent
    ]

    try:
        insight_text = ai_service.generate_self_pattern_insight(
            interactions_dicts, ai_on, settings.openai_model
        )
        crud.create_insight(
            db,
            data={
                "insight_type": "self_pattern",
                "title": f"Self-pattern analysis — {datetime.utcnow().strftime('%d %b %Y')}",
                "summary": insight_text[:500] + ("..." if len(insight_text) > 500 else ""),
                "evidence": insight_text,
                "confidence": "medium",
            },
            interaction_ids=[i.id for i in recent[:5]],
        )
    except Exception:
        pass
    return RedirectResponse("/patterns", status_code=303)


# ============================================================
# MEETING PREP
# ============================================================

@app.get("/meeting-prep", response_class=HTMLResponse)
async def meeting_prep_list(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["preps"] = crud.get_meeting_preps(db)
    return templates.TemplateResponse("meeting_prep/list.html", ctx)


@app.get("/meeting-prep/new", response_class=HTMLResponse)
async def meeting_prep_new(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["prep"] = None
    ctx["stakeholders"] = crud.get_stakeholders(db)
    ctx["projects"] = crud.get_projects(db)
    ctx["advisor_voices"] = list(ai_service.ADVISOR_DESCRIPTIONS.keys())
    ctx["form_action"] = "/meeting-prep"
    ctx["selected_stakeholder_ids"] = []
    ctx["selected_project_id"] = None
    ctx["selected_voices"] = ["strategist"]
    return templates.TemplateResponse("meeting_prep/form.html", ctx)


@app.post("/meeting-prep", response_class=HTMLResponse)
async def meeting_prep_create(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    data, stakeholder_ids, project_id = _parse_meeting_prep_form(form)
    prep = crud.create_meeting_prep(db, data, stakeholder_ids, project_id)
    return RedirectResponse(f"/meeting-prep/{prep.id}", status_code=303)


@app.get("/meeting-prep/{prep_id}", response_class=HTMLResponse)
async def meeting_prep_detail(
    prep_id: int, request: Request, db: Session = Depends(get_db)
):
    prep = crud.get_meeting_prep(db, prep_id)
    if not prep:
        raise HTTPException(status_code=404, detail="Meeting prep not found")
    ctx = common_context(request, db)
    ctx["prep"] = prep
    ctx["advisor_voices"] = list(ai_service.ADVISOR_DESCRIPTIONS.keys())
    return templates.TemplateResponse("meeting_prep/detail.html", ctx)


@app.post("/meeting-prep/{prep_id}/generate", response_class=HTMLResponse)
async def meeting_prep_generate(
    prep_id: int, request: Request, db: Session = Depends(get_db)
):
    prep = crud.get_meeting_prep(db, prep_id)
    if not prep:
        raise HTTPException(status_code=404, detail="Meeting prep not found")
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)

    meeting_dict = {
        "meeting_title": prep.meeting_title,
        "meeting_date": str(prep.meeting_date.date()) if prep.meeting_date else None,
        "desired_outcome": prep.desired_outcome,
        "likely_resistance": prep.likely_resistance,
        "emotional_risk": prep.emotional_risk,
        "what_i_am_tempted_to_do_badly": prep.what_i_am_tempted_to_do_badly,
    }

    stakeholders_dicts = [
        {
            "name": s.name,
            "role_title": s.role_title,
            "relationship_type": s.relationship_type,
            "influence_level": s.influence_level,
            "trust_level": s.trust_level,
            "likely_incentives": s.likely_incentives,
            "what_they_care_about": s.what_they_care_about,
            "what_they_resist": s.what_they_resist,
            "what_earns_trust": s.what_earns_trust,
            "tension_triggers": s.tension_triggers,
            "communication_style": s.communication_style,
        }
        for s in prep.stakeholders
    ]

    project_dict = None
    if prep.project:
        p = prep.project
        project_dict = {
            "name": p.name,
            "description": p.description,
            "current_status": p.current_status,
            "main_tensions": p.main_tensions,
            "desired_outcome": p.desired_outcome,
            "risks": p.risks,
        }

    # Get recent interactions involving these stakeholders or this project
    all_interactions = crud.get_interactions(db, limit=20)
    prep_stakeholder_ids = {s.id for s in prep.stakeholders}
    relevant = [
        i for i in all_interactions
        if (prep.project_id and i.project_id == prep.project_id)
        or any(s.id in prep_stakeholder_ids for s in i.stakeholders)
    ][:10]

    interactions_dicts = [
        {
            "date": str(i.date.date()),
            "title": i.title,
            "what_happened": i.what_happened,
            "what_was_said": i.what_was_said,
            "what_was_unsaid": i.what_was_unsaid,
            "actual_outcome": i.actual_outcome,
            "emotional_response": i.emotional_response,
            "shrink_expand_rating": i.shrink_expand_rating,
            "did_overexplain": i.did_overexplain,
            "did_soften_message": i.did_soften_message,
        }
        for i in relevant
    ]

    advisor_voices = prep.advisor_voices.split(",") if prep.advisor_voices else ["strategist"]

    try:
        brief = ai_service.generate_meeting_prep(
            meeting_dict, stakeholders_dicts, project_dict,
            interactions_dicts, advisor_voices, ai_on, settings.openai_model
        )
        crud.update_meeting_prep(db, prep_id, {"generated_strategy": brief})
    except Exception:
        pass
    return RedirectResponse(f"/meeting-prep/{prep_id}", status_code=303)


@app.post("/meeting-prep/{prep_id}/delete")
async def meeting_prep_delete(prep_id: int, db: Session = Depends(get_db)):
    crud.delete_meeting_prep(db, prep_id)
    return RedirectResponse("/meeting-prep", status_code=303)


def _parse_meeting_prep_form(form) -> tuple:
    def get(key, default=""):
        val = form.get(key, default)
        return val if val else default

    date_str = form.get("meeting_date")
    try:
        meeting_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
    except ValueError:
        meeting_date = None

    advisor_voices = form.getlist("advisor_voices")

    data = {
        "meeting_title": get("meeting_title", "Untitled meeting"),
        "meeting_date": meeting_date,
        "desired_outcome": get("desired_outcome") or None,
        "likely_resistance": get("likely_resistance") or None,
        "emotional_risk": get("emotional_risk") or None,
        "what_i_am_tempted_to_do_badly": get("what_i_am_tempted_to_do_badly") or None,
        "advisor_voices": ",".join(advisor_voices) if advisor_voices else "strategist",
    }

    stakeholder_ids = [int(x) for x in form.getlist("stakeholder_ids") if x.isdigit()]
    project_id_raw = form.get("project_id")
    project_id = int(project_id_raw) if project_id_raw and project_id_raw.isdigit() else None

    return data, stakeholder_ids, project_id


# ============================================================
# ADVISOR MODE
# ============================================================

@app.get("/advisor", response_class=HTMLResponse)
async def advisor_page(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx["advisor_voices"] = list(ai_service.ADVISOR_DESCRIPTIONS.keys())
    ctx["advisor_response"] = None
    ctx["recent_interactions"] = crud.get_interactions(db, limit=5)
    ctx["projects"] = crud.get_projects(db)
    return templates.TemplateResponse("advisor.html", ctx)


@app.post("/advisor", response_class=HTMLResponse)
async def advisor_ask(
    request: Request,
    db: Session = Depends(get_db),
    question: str = Form(...),
    advisor_voices: list = Form(default=[]),
):
    settings = crud.get_settings(db)
    ai_on = get_ai_enabled(db)

    recent = crud.get_interactions(db, limit=10)
    context_parts = []
    for i in recent:
        context_parts.append(
            f"{i.date.strftime('%d %b %Y')} — {i.title}\n"
            f"What happened: {i.what_happened or ''}\n"
            f"Outcome: {i.actual_outcome or ''}\n"
            f"How I showed up: {i.shrink_expand_rating or ''}"
        )
    context = "\n\n".join(context_parts) or "No interactions logged yet."

    if not advisor_voices:
        advisor_voices = ["strategist"]

    form_data = await request.form()
    advisor_voices = form_data.getlist("advisor_voices") or ["strategist"]

    response = ai_service.generate_advisor_response(
        context, question, advisor_voices, ai_on, settings.openai_model
    )

    ctx = common_context(request, db)
    ctx["advisor_voices"] = list(ai_service.ADVISOR_DESCRIPTIONS.keys())
    ctx["advisor_response"] = response
    ctx["question"] = question
    ctx["selected_voices"] = advisor_voices
    ctx["recent_interactions"] = recent
    ctx["projects"] = crud.get_projects(db)
    return templates.TemplateResponse("advisor.html", ctx)


# ============================================================
# SETTINGS
# ============================================================

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    return templates.TemplateResponse("settings.html", ctx)


@app.post("/settings", response_class=HTMLResponse)
async def settings_update(
    request: Request,
    db: Session = Depends(get_db),
    ai_enabled: str = Form("off"),
    openai_model: str = Form("gpt-4o"),
):
    crud.update_settings(db, ai_enabled=(ai_enabled == "on"), openai_model=openai_model)
    return RedirectResponse("/settings", status_code=303)


@app.get("/settings/export")
async def settings_export(db: Session = Depends(get_db)):
    data = crud.export_all_data(db)
    json_str = json.dumps(data, indent=2, default=str)
    filename = f"work_mirror_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/settings/delete-all")
async def settings_delete_all(
    request: Request,
    db: Session = Depends(get_db),
    confirm: str = Form(""),
):
    if confirm == "DELETE":
        crud.delete_all_data(db)
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/seed")
async def settings_seed(db: Session = Depends(get_db)):
    crud.seed_example_data(db)
    return RedirectResponse("/", status_code=303)
