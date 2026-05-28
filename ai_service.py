"""
AI service layer for Work Mirror.
All OpenAI calls go through this module.
The app works without AI — every function returns a fallback prompt when AI is disabled.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

ADVISOR_DESCRIPTIONS = {
    "strategist": "You are a strategic advisor. Focus on incentives, power dynamics, timing, sequencing, and the best next move. Think in terms of what each player wants and how the system is behaving.",
    "reflector": "You are a therapist-informed reflector. Focus on emotional patterns, shrink/expand behaviour, avoidance, over-explaining, fear of overstepping, and boundary-holding. Do not provide clinical advice. Use plain language.",
    "operator": "You are an operator. Focus on execution, next steps, ownership, decisions, documentation, and follow-through. Be specific about what needs to happen and who needs to do it.",
    "executive": "You are an executive advisor. Focus on senior framing, business impact, risk, operating model clarity, and decision rights. Help the user speak and act at the right level.",
    "friend": "You are a no-bullshit friend. Be direct and honest. Not cruel, but clear. Cut through the noise. Say what you actually think.",
    "future_self": "You are the user's future self — a stronger, clearer, more senior leader. Focus on what supports that growth. What would you wish you had done?",
}

SYSTEM_BASE = """You are an advisor embedded in Work Mirror, a private leadership intelligence tool.

Rules:
- Be grounded in the data provided. Separate fact from inference. Label inferences clearly.
- Do not diagnose stakeholders. Describe observable behaviour only.
- Do not encourage paranoia or excessive analysis.
- Always end with a concrete next move.
- If evidence is thin, say so explicitly.
- Use direct, thoughtful language. No motivational fluff.
- Avoid generic productivity advice.
- Avoid fake certainty.
- Encourage clean leadership: clarity, boundaries, documentation, courage, strategic empathy.
- Format output using clear section headers.
"""


def _call_openai(system: str, user: str, model: str = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[no-api-key]"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[AI error: {str(e)}]"


def generate_stakeholder_update(
    stakeholder: dict,
    recent_interactions: list,
    ai_enabled: bool = True,
    model: str = None,
) -> str:
    if not ai_enabled:
        return _fallback_stakeholder_update()

    stakeholder_text = "\n".join(f"{k}: {v}" for k, v in stakeholder.items() if v)
    interactions_text = _format_interactions(recent_interactions)

    prompt = f"""Existing stakeholder profile:
{stakeholder_text}

Recent interactions involving this stakeholder:
{interactions_text}

Generate a stakeholder profile update with these sections:
1. Observed behaviours (facts from logs only)
2. Likely incentives (label as inference)
3. Communication preferences (observed patterns)
4. Trust-building patterns
5. Tension triggers
6. Recommended approach for next interaction
7. Evidence from logs (quote specific interactions)
8. Confidence level: low / medium / high and why

Keep it behaviour-based. Do not diagnose. Do not judge. Describe what was observed."""

    result = _call_openai(SYSTEM_BASE, prompt, model)
    if result == "[no-api-key]":
        return _fallback_no_key()
    return result or _fallback_stakeholder_update()


def generate_political_weather(
    project: dict,
    stakeholders: list,
    recent_interactions: list,
    ai_enabled: bool = True,
    model: str = None,
) -> str:
    if not ai_enabled:
        return _fallback_political_weather()

    project_text = "\n".join(f"{k}: {v}" for k, v in project.items() if v)
    stakeholders_text = "\n\n".join(
        "\n".join(f"{k}: {v}" for k, v in s.items() if v) for s in stakeholders
    )
    interactions_text = _format_interactions(recent_interactions)

    prompt = f"""Project / Context:
{project_text}

Key stakeholders:
{stakeholders_text}

Recent interactions:
{interactions_text}

Generate a political weather report with these sections:
1. What the visible issue appears to be
2. What the underlying tension may be (label as inference)
3. Key stakeholders and their likely incentives
4. Current risks
5. Alignment gaps
6. Recommended next move
7. What to document now
8. What not to over-focus on

Be direct. If the evidence is thin, say so. End with one clear action."""

    result = _call_openai(SYSTEM_BASE, prompt, model)
    if result == "[no-api-key]":
        return _fallback_no_key()
    return result or _fallback_political_weather()


def generate_self_pattern_insight(
    recent_interactions: list,
    ai_enabled: bool = True,
    model: str = None,
) -> str:
    if not ai_enabled:
        return _fallback_self_pattern()

    interactions_text = _format_interactions(recent_interactions)

    prompt = f"""Recent interaction logs:
{interactions_text}

Generate a self-pattern insight with these sections:
1. Shrink / expand patterns (when does the user expand vs shrink?)
2. Situations where communication is clear and direct
3. Situations where the user softens, over-explains, avoids, or under-claims authority
4. Recurring emotional triggers
5. Strengths observed in the data
6. One growth edge (specific, not generic)
7. One practical experiment for next week

Be honest and direct. Label inferences. Ground every point in the logged data.
Use the phrasing: "Possible pattern" or "Based on interactions logged so far" where appropriate.
Do not moralize. This is strategic self-awareness, not self-improvement."""

    result = _call_openai(SYSTEM_BASE, prompt, model)
    if result == "[no-api-key]":
        return _fallback_no_key()
    return result or _fallback_self_pattern()


def generate_meeting_prep(
    meeting: dict,
    stakeholders: list,
    project: Optional[dict],
    recent_interactions: list,
    advisor_voices: list,
    ai_enabled: bool = True,
    model: str = None,
) -> str:
    if not ai_enabled:
        return _fallback_meeting_prep(meeting)

    # Build advisor system prompt
    voice_descriptions = []
    for voice in advisor_voices:
        if voice in ADVISOR_DESCRIPTIONS:
            voice_descriptions.append(f"[{voice.upper()}] {ADVISOR_DESCRIPTIONS[voice]}")
    if not voice_descriptions:
        voice_descriptions = [ADVISOR_DESCRIPTIONS["strategist"]]

    advisor_system = SYSTEM_BASE + "\n\nActive advisor voices for this response:\n" + "\n".join(voice_descriptions)

    meeting_text = "\n".join(f"{k}: {v}" for k, v in meeting.items() if v)
    stakeholders_text = "\n\n".join(
        "\n".join(f"{k}: {v}" for k, v in s.items() if v) for s in stakeholders
    ) if stakeholders else "No stakeholders specified."
    project_text = "\n".join(f"{k}: {v}" for k, v in project.items() if v) if project else "No project context."
    interactions_text = _format_interactions(recent_interactions)

    prompt = f"""Meeting details:
{meeting_text}

Stakeholders attending:
{stakeholders_text}

Project / Context:
{project_text}

Relevant past interactions:
{interactions_text}

Generate a full meeting prep brief with these sections:
1. Strategic objective (one sentence)
2. System read — what is the broader dynamic going into this meeting?
3. Stakeholder read — what does each person likely want from this meeting?
4. User pattern risk — based on past logs, where might the user shrink, over-explain, or avoid?
5. Suggested opening (specific, not generic)
6. Three key points to land
7. Questions to ask
8. Likely objections and how to respond
9. What to avoid saying or doing
10. Where to hold firm
11. Where to stay flexible
12. Recommended next action after the meeting

Be specific. Ground every point in the data provided.
If evidence is thin on any section, say so rather than speculating."""

    result = _call_openai(advisor_system, prompt, model)
    if result == "[no-api-key]":
        return _fallback_no_key()
    return result or _fallback_meeting_prep(meeting)


def generate_advisor_response(
    context: str,
    question: str,
    advisor_voices: list,
    ai_enabled: bool = True,
    model: str = None,
) -> str:
    if not ai_enabled:
        return "AI is disabled. Enable AI in Settings to use Advisor Mode."

    voice_descriptions = []
    for voice in advisor_voices:
        if voice in ADVISOR_DESCRIPTIONS:
            voice_descriptions.append(f"[{voice.upper()}] {ADVISOR_DESCRIPTIONS[voice]}")
    if not voice_descriptions:
        voice_descriptions = [ADVISOR_DESCRIPTIONS["strategist"]]

    advisor_system = SYSTEM_BASE + "\n\nActive advisor voices:\n" + "\n".join(voice_descriptions)

    prompt = f"""Context from recent logs:
{context}

Question / situation:
{question}

Respond drawing on the advisor voices specified. Be direct. End with a concrete next move."""

    result = _call_openai(advisor_system, prompt, model)
    if result == "[no-api-key]":
        return _fallback_no_key()
    return result or "No response returned. Check your API key and model in Settings."


def _format_interactions(interactions: list) -> str:
    if not interactions:
        return "No interactions logged yet."
    parts = []
    for i in interactions:
        lines = [f"Date: {i.get('date', 'unknown')} | {i.get('title', 'untitled')}"]
        for field in ["what_happened", "what_was_said", "what_was_unsaid", "actual_outcome",
                      "emotional_response", "leadership_behaviour", "shrink_expand_rating",
                      "what_i_wanted_to_say", "what_i_actually_said", "what_i_would_do_next_time"]:
            if i.get(field):
                lines.append(f"  {field}: {i[field]}")
        parts.append("\n".join(lines))
    return "\n\n---\n\n".join(parts)


def _fallback_stakeholder_update() -> str:
    return """AI is disabled. To update this stakeholder profile manually, review recent interactions and consider:

**Observed behaviours**
What specific behaviours have you observed? (Not judgements — actions and patterns.)

**Likely incentives**
What does this person appear to care about most? What pressures are they under?

**Communication preferences**
How do they prefer to receive information? What triggers defensiveness?

**Trust-building patterns**
What actions have built or damaged trust in your experience?

**Tension triggers**
In which situations does friction tend to appear?

**Recommended approach**
Given all of the above, what is the clearest way to work with this person right now?

Enable AI in Settings to generate this automatically from your interaction logs."""


def _fallback_political_weather() -> str:
    return """AI is disabled. To assess the political weather manually, consider:

**What the visible issue appears to be**
What is being discussed openly?

**What the underlying tension may be**
What is not being named? What are the competing interests?

**Key stakeholders and incentives**
Who has the most at stake? What do they need this to look like?

**Current risks**
What could go wrong? What is the most fragile assumption?

**Alignment gaps**
Where are people working from different assumptions?

**Recommended next move**
What is the one thing that would most move this forward?

**What to document**
What decisions or commitments need a paper trail?

Enable AI in Settings to generate this automatically from your logs."""


def _fallback_self_pattern() -> str:
    return """AI is disabled. To reflect on your patterns manually, review your recent interaction logs and ask:

**When did I communicate clearly and directly?**
What were the conditions? What made it easier?

**When did I shrink, soften, or avoid?**
What triggered that? What was I trying to protect?

**When did I over-explain?**
Was it anxiety, a need to justify, or something else?

**When did I avoid making an ask or claiming authority?**
What was the cost of that?

**What is one pattern I notice?**
Be specific. Not "I need to be more confident" — something observable.

**One experiment for next week**
A specific, small thing to try differently.

Enable AI in Settings to generate this from your logged interactions."""


def _fallback_meeting_prep(meeting: dict) -> str:
    title = meeting.get("meeting_title", "this meeting")
    return f"""AI is disabled. Use these prompts to prepare for {title}:

**Strategic objective**
What is the one thing you need to leave this meeting having achieved?

**System read**
What is the broader dynamic going into this meeting? What is the system trying to do?

**Stakeholder read**
For each person in the room: what do they want from this meeting? What are they protecting?

**Your pattern risk**
Where have you shrunk or avoided in similar situations before? Name it.

**Opening**
How will you open? What framing will set the right tone?

**Three key points**
What are the three things you need to land, in order of priority?

**Questions to ask**
What do you need to understand that you don't yet?

**Likely objections**
What will be pushed back on? How will you respond without over-explaining?

**Where to hold firm**
What is non-negotiable?

**Where to stay flexible**
Where can you genuinely move?

**Next action**
What will you do in the 24 hours after this meeting?

Enable AI in Settings to generate a full brief automatically."""


def _fallback_no_key() -> str:
    return """**OpenAI API key not configured.**

AI is enabled in your settings, but no API key has been found.

To fix this on Render:
1. Go to your Render service → Environment
2. Add the environment variable: `OPENAI_API_KEY` = your key from platform.openai.com
3. Redeploy the service

To fix this locally:
1. Open your `.env` file
2. Add: `OPENAI_API_KEY=sk-...`
3. Restart the server"""
