"""Prompt template builders for each specialized interview agent.

Centralizing prompt construction here keeps agent node code small and makes prompts
easy to audit/version (mirrored for documentation purposes in docs/prompts/).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _skills_block(skills: List[Dict[str, str]]) -> str:
    return "\n".join(f"- {s['name']}: {s['level']}" for s in skills) or "- (none provided)"


def _resume_block(resume_context: Optional[Dict[str, Any]]) -> str:
    if not resume_context:
        return "No resume was provided; rely on the declared skills/experience only."
    lines = []
    if resume_context.get("skills"):
        lines.append(f"Resume skills: {', '.join(resume_context['skills'])}")
    if resume_context.get("projects"):
        proj = "; ".join(p.get("name", "") for p in resume_context["projects"])
        lines.append(f"Resume projects: {proj}")
    if resume_context.get("certifications"):
        lines.append(f"Certifications: {', '.join(resume_context['certifications'])}")
    return "\n".join(lines) or "Resume provided but no structured data extracted."


def _history_block(history: List[Dict[str, Any]]) -> str:
    if not history:
        return "This is the first question of the interview."
    lines = []
    for i, h in enumerate(history[-5:], 1):
        lines.append(
            f"Q{i} [{h.get('agent_type')}/{h.get('difficulty')}]: {h.get('question')}\n"
            f"A{i}: {h.get('answer', '')[:400]}"
        )
    return "\n".join(lines)


QUESTION_GEN_SYSTEM = """You are a senior, no-nonsense technical interviewer at a top-tier tech company, \
conducting a live {category} interview for a candidate targeting {target_company}. \
You behave like a real human interviewer: professional, precise, and adaptive. \
You must respond ONLY with the structured fields requested — no extra commentary."""


def build_technical_question_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    system = QUESTION_GEN_SYSTEM.format(
        category=state.get("category", "Software Engineer"),
        target_company=state.get("target_company", "Generic"),
    )
    user = f"""Generate ONE technical interview question at difficulty '{state.get('current_difficulty')}'.

Candidate profile:
- Years of experience: {state.get('years_of_experience')}
- Skills:
{_skills_block(state.get('skills', []))}

Resume context:
{_resume_block(state.get('resume_context'))}

Recent conversation so far:
{_history_block(state.get('history', []))}

Rules:
- Prefer a skill from the candidate's resume/skills that has not been deeply probed yet.
- If the resume mentions a specific technology (e.g. Azure, Microservices), ask something concrete and \
personalized about it (e.g. "Explain how you implemented managed identities in Azure" or \
"How did you handle distributed transactions?").
- Do not repeat a question already asked.
- Set 'skill' to the single most relevant skill name.
- Set 'difficulty' to exactly '{state.get('current_difficulty')}'.
"""
    return system, user


def build_behavioral_question_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    system = QUESTION_GEN_SYSTEM.format(
        category=state.get("category", "Software Engineer"),
        target_company=state.get("target_company", "Generic"),
    )
    user = f"""Generate ONE behavioral interview question suitable for evaluation using the STAR framework \
(Situation, Task, Action, Result). Target difficulty: '{state.get('current_difficulty')}'.

Focus areas to rotate across the interview: Leadership, Ownership, Communication, Conflict Resolution, \
Team Collaboration. Choose whichever has been probed least so far.

Candidate profile: {state.get('years_of_experience')} years of experience, category: {state.get('category')}.

Recent conversation so far:
{_history_block(state.get('history', []))}

Rules:
- Phrase the question to naturally elicit a STAR-structured answer (e.g. "Tell me about a time when...").
- Set 'skill' to the behavioral competency being probed (e.g. "Leadership").
- Set 'difficulty' to exactly '{state.get('current_difficulty')}'.
"""
    return system, user


SYSTEM_DESIGN_EXAMPLES = ["Design Netflix", "Design Uber", "Design WhatsApp", "Design Banking Platform", "Design Airline Booking System"]


def build_system_design_question_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    system = QUESTION_GEN_SYSTEM.format(
        category=state.get("category", "Software Engineer"),
        target_company=state.get("target_company", "Generic"),
    )
    user = f"""Generate ONE system design interview question at difficulty '{state.get('current_difficulty')}'. \
Examples of the style expected: {', '.join(SYSTEM_DESIGN_EXAMPLES)} (pick a similar but not-yet-asked prompt, \
or a variant tailored to the candidate's domain: {state.get('category')}).

The candidate will be evaluated on: Scalability, Availability, Reliability, Security, Cost Optimization — \
set 'expected_topics' to a subset of these that this specific design problem should emphasize.

Recent conversation so far:
{_history_block(state.get('history', []))}

Rules:
- Do not repeat a design prompt already asked.
- Set 'skill' to "System Design".
- Set 'difficulty' to exactly '{state.get('current_difficulty')}'.
"""
    return system, user


def build_coding_question_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    system = QUESTION_GEN_SYSTEM.format(
        category=state.get("category", "Software Engineer"),
        target_company=state.get("target_company", "Generic"),
    )
    user = f"""Generate ONE coding interview problem at difficulty '{state.get('current_difficulty')}' relevant to \
a {state.get('category')} role. The candidate will be evaluated on: Correctness, Time Complexity, Space \
Complexity, Edge Cases, Optimization.

Recent conversation so far:
{_history_block(state.get('history', []))}

Rules:
- State the problem clearly with a small example input/output.
- Set 'expected_topics' to the key algorithmic concepts/edge cases expected in a strong solution.
- Set 'skill' to the primary data-structure/algorithm category (e.g. "Graphs", "Dynamic Programming").
- Set 'difficulty' to exactly '{state.get('current_difficulty')}'.
"""
    return system, user


EVALUATION_SYSTEM = """You are the Evaluation Agent for an AI mock interview platform. You score candidate \
answers rigorously and fairly, like an experienced hiring committee member. Always respond ONLY with the \
structured fields requested."""


def build_evaluation_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    question = state.get("last_question", {}) or {}
    user = f"""Evaluate the candidate's answer to the following interview question.

Question ({question.get('type', question.get('agent_type'))}, difficulty={question.get('difficulty')}, \
skill={question.get('skill')}):
{question.get('text', question.get('question'))}

Expected topics: {', '.join(question.get('expected_topics', []) or [])}

Candidate's answer:
\"\"\"{state.get('candidate_answer', '')}\"\"\"

Score each dimension from 1 (poor) to 10 (excellent):
- technical_score: correctness/accuracy of technical content
- communication_score: clarity, structure, articulation
- confidence_score: assuredness and decisiveness in the response
- problem_solving_score: reasoning process and trade-off analysis
- depth_score: depth of knowledge beyond the surface answer
- completeness_score: how completely the expected topics were covered

Also produce:
- missing_points: expected topics/considerations the candidate did not mention
- strengths: specific things the candidate did well
- followup_question: ONE natural follow-up question probing a gap or going deeper (or null if none is warranted)
"""
    return EVALUATION_SYSTEM, user


FEEDBACK_SYSTEM = """You are the Feedback Agent for an AI mock interview platform, producing the final hiring-style \
report a candidate receives after their mock interview. Be constructive, specific, and honest."""


def build_feedback_prompt(state: Dict[str, Any]) -> tuple[str, str]:
    history = state.get("history", [])
    transcript_lines = []
    for i, h in enumerate(history, 1):
        transcript_lines.append(
            f"Q{i} [{h.get('agent_type')}/{h.get('difficulty')}/{h.get('skill')}]: {h.get('question')}\n"
            f"A{i}: {h.get('answer', '')}\n"
            f"Scores: technical={h.get('technical_score')}, communication={h.get('communication_score')}, "
            f"confidence={h.get('confidence_score')}, problem_solving={h.get('problem_solving_score')}, "
            f"depth={h.get('depth_score')}"
        )
    transcript = "\n\n".join(transcript_lines) or "No questions were answered."

    user = f"""Candidate: {state.get('candidate_name', 'Candidate')} | Category: {state.get('category')} | \
Target company: {state.get('target_company')} | Interview type: {state.get('interview_type')}

Full interview transcript with per-answer scores:
{transcript}

Produce a final report with:
- executive_summary: 3-5 sentence overview of overall performance
- strengths: bullet list of concrete strengths observed
- weaknesses: bullet list of concrete weaknesses observed
- learning_path: ordered list of specific topics/resources to study next
- communication_assessment: 2-4 sentences
- technical_assessment: 2-4 sentences
- behavioral_assessment: 2-4 sentences (state "Not assessed" if no behavioral questions were asked)
- hiring_recommendation: one of "Outstanding", "Strong Hire", "Hire", "Borderline", "Needs Improvement" plus a \
one-sentence justification
- sample_ideal_answers: for the 2 lowest-scoring questions, provide [{{"question": ..., "ideal_answer": ...}}]
"""
    return FEEDBACK_SYSTEM, user
