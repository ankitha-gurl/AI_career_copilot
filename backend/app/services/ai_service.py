"""
AIService — the single place in the whole application that talks to OpenAI.

Design rules followed here (per project spec):
- No other file calls OpenAI directly.
- Uses the current official OpenAI Python SDK client (openai>=1.x, `OpenAI()` client,
  `client.chat.completions.create(...)`), not the deprecated `openai.ChatCompletion` API.
- Every method asks the model to return ONLY JSON, and every method safely
  parses and validates that JSON, with clear errors if it fails.
- Every method treats API failure, timeout, and malformed JSON as recoverable
  errors — callers get an AIServiceError, never a raw exception/crash.
- Prompts never include password hashes, JWT secrets, or other users' data.
"""
import json
import logging
from typing import Any, Optional

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from app.config import settings

logger = logging.getLogger("ai_service")

MAX_RESUME_CHARS = 12000       # ~ a few thousand tokens, keeps cost/latency sane
MAX_JOB_DESC_CHARS = 6000


class AIServiceError(Exception):
    """Raised whenever the AI call fails or returns unusable output."""


def _get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise AIServiceError(
            "OPENAI_API_KEY is not configured on the server. "
            "Add it to backend/.env and restart the server."
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _chat_json(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> dict:
    """
    Shared low-level helper: calls the chat completions endpoint asking for
    strict JSON output, and parses it. Every AIService method funnels through
    this so error handling / logging / JSON parsing lives in exactly one place.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except RateLimitError as exc:
        logger.warning("OpenAI rate limit hit: %s", exc)
        raise AIServiceError("The AI service is currently rate-limited. Please try again shortly.") from exc
    except APITimeoutError as exc:
        logger.warning("OpenAI timeout: %s", exc)
        raise AIServiceError("The AI service timed out. Please try again.") from exc
    except APIError as exc:
        logger.error("OpenAI API error: %s", exc)
        raise AIServiceError("The AI service returned an error. Please try again later.") from exc
    except Exception as exc:  # noqa: BLE001 - guard against any unexpected SDK failure
        logger.error("Unexpected AI service failure: %s", exc)
        raise AIServiceError("Unexpected AI service failure.") from exc

    raw_content = response.choices[0].message.content if response.choices else None
    if not raw_content:
        raise AIServiceError("The AI service returned an empty response.")

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as exc:
        logger.error("AI returned invalid JSON: %s", raw_content[:500])
        raise AIServiceError("The AI service returned a response we couldn't parse.") from exc


class AIService:
    """Career-intelligence AI operations. All methods are static/stateless."""

    # ---------------------------------------------------------------- resume
    @staticmethod
    def analyze_resume(resume_text: str) -> dict:
        if not resume_text or not resume_text.strip():
            raise AIServiceError("Resume text is empty; nothing to analyze.")

        trimmed = resume_text[:MAX_RESUME_CHARS]

        system_prompt = (
            "You are a precise resume-analysis engine for a career platform. "
            "Extract ONLY information that is explicitly present in the resume text. "
            "Never invent employers, dates, degrees, or skills that are not present. "
            "If something is not present, omit it or use an empty list/string — "
            "do not guess. Respond with ONLY a single JSON object, no markdown, "
            "matching exactly this schema:\n"
            '{"summary": string, "skills": [string], "technical_skills": [string], '
            '"soft_skills": [string], "education": [string], "experience": [string], '
            '"projects": [string], "certifications": [string], "technologies": [string], '
            '"strengths": [string], "weaknesses": [string], "missing_information": [string]}'
        )
        user_prompt = f"Resume text:\n---\n{trimmed}\n---"
        return _chat_json(system_prompt, user_prompt, max_tokens=1800)

    # --------------------------------------------------------- job description
    @staticmethod
    def analyze_job_description(job_text: str) -> dict:
        if not job_text or not job_text.strip():
            raise AIServiceError("Job description text is empty; nothing to analyze.")

        trimmed = job_text[:MAX_JOB_DESC_CHARS]

        system_prompt = (
            "You are a job-description analysis engine. Extract structured "
            "requirements ONLY from the text given. Respond with ONLY a single "
            "JSON object matching exactly this schema:\n"
            '{"job_title": string, "company": string, "required_skills": [string], '
            '"preferred_skills": [string], "experience_requirements": string, '
            '"education_requirements": string, "responsibilities": [string], '
            '"technologies": [string], "keywords": [string], "seniority": string, '
            '"domain": string}'
        )
        user_prompt = f"Job description:\n---\n{trimmed}\n---"
        return _chat_json(system_prompt, user_prompt, max_tokens=1200)

    # -------------------------------------------------------------- matching
    @staticmethod
    def calculate_job_match(resume_analysis: dict, job_analysis: dict) -> dict:
        system_prompt = (
            "You are a career-matching engine. Compare a candidate's resume "
            "analysis against a job's requirements and produce an AI-assisted "
            "estimate of fit. Be honest and specific — do not inflate scores. "
            "Clearly state this is an estimate, not an objective guarantee. "
            "Respond with ONLY a single JSON object matching exactly this schema:\n"
            '{"match_score": number (0-100), "skill_match": number (0-100), '
            '"experience_match": number (0-100), "education_match": number (0-100), '
            '"technology_match": number (0-100), "missing_skills": [string], '
            '"strengths": [string], "weaknesses": [string], "recommendations": [string], '
            '"reasoning": [string]}'
        )
        user_prompt = (
            f"Candidate resume analysis (JSON):\n{json.dumps(resume_analysis)}\n\n"
            f"Job requirements analysis (JSON):\n{json.dumps(job_analysis)}"
        )
        return _chat_json(system_prompt, user_prompt, max_tokens=1200)

    # ------------------------------------------------------------ skill gap
    @staticmethod
    def generate_skill_gap(user_skills: list[str], job_analysis: dict) -> dict:
        system_prompt = (
            "You are a career-development advisor. Given a user's current skills "
            "and a target job's requirements, identify what they already have and "
            "what is missing, with clear priority and reasoning. Respond with ONLY "
            "a single JSON object matching exactly this schema:\n"
            '{"already_possessed": [string], "missing_skills": ['
            '{"skill": string, "priority": "high"|"medium"|"low", "reason": string, '
            '"suggested_action": string}], "suggested_learning_order": [string]}'
        )
        user_prompt = (
            f"Current user skills: {json.dumps(user_skills)}\n\n"
            f"Target job analysis (JSON): {json.dumps(job_analysis)}"
        )
        return _chat_json(system_prompt, user_prompt, max_tokens=1400)

    # ---------------------------------------------------------------- roadmap
    @staticmethod
    def generate_career_roadmap(
        target_role: str, user_skills: list[str], skill_gap: Optional[dict] = None
    ) -> dict:
        system_prompt = (
            "You are a realistic career-roadmap planner for a fresher/early-career "
            "engineer. Do not promise unrealistic timelines. Respond with ONLY a "
            "single JSON object matching exactly this schema:\n"
            '{"phases": [{"order_index": number, "phase_title": string, '
            '"skill": string, "priority": "high"|"medium"|"low", '
            '"difficulty": "beginner"|"intermediate"|"advanced", '
            '"prerequisites": string, "project_task": string, "success_criteria": string}]}'
        )
        user_prompt = (
            f"Target role: {target_role}\n"
            f"Current skills: {json.dumps(user_skills)}\n"
            f"Known skill gap analysis (optional, may be empty): {json.dumps(skill_gap or {})}"
        )
        return _chat_json(system_prompt, user_prompt, max_tokens=1800)

    # -------------------------------------------------------- interview prep
    @staticmethod
    def generate_interview_questions(
        target_role: str,
        resume_summary: str,
        missing_skills: list[str],
        num_questions: int = 5,
    ) -> dict:
        num_questions = max(1, min(num_questions, 12))
        system_prompt = (
            "You generate high-quality interview questions for a fresher/early-career "
            "candidate, mixing technical, coding, behavioral, project-based, and "
            "resume-based questions. For each question give a model answer and "
            "explanation useful for someone learning. Respond with ONLY a single "
            "JSON object matching exactly this schema:\n"
            '{"questions": [{"question_type": '
            '"technical"|"coding"|"behavioral"|"system_design"|"project"|"resume", '
            '"question_text": string, "expected_concepts": string, '
            '"model_answer": string, "explanation": string, '
            '"follow_up_questions": [string]}]}'
        )
        user_prompt = (
            f"Target role: {target_role}\n"
            f"Resume summary: {resume_summary}\n"
            f"Skills the candidate is missing/weak on: {json.dumps(missing_skills)}\n"
            f"Number of questions to generate: {num_questions}"
        )
        return _chat_json(system_prompt, user_prompt, max_tokens=2200)

    @staticmethod
    def evaluate_interview_answer(question_text: str, model_answer: str, user_answer: str) -> dict:
        system_prompt = (
            "You are an interview coach evaluating a candidate's answer. Be "
            "constructive and specific, not harsh. Respond with ONLY a single "
            "JSON object matching exactly this schema:\n"
            '{"score": number (0-100), "correct_points": [string], '
            '"missing_points": [string], "improvement_suggestions": [string], '
            '"overall_feedback": string}'
        )
        user_prompt = (
            f"Question: {question_text}\n\n"
            f"Reference model answer: {model_answer}\n\n"
            f"Candidate's actual answer: {user_answer}"
        )
        return _chat_json(system_prompt, user_prompt, max_tokens=900)

    # -------------------------------------------------------------- chat
    @staticmethod
    def career_chat(user_message: str, context: dict, history: list[dict]) -> str:
        """
        Free-text conversational reply (not JSON) — this is the copilot chat.
        `context` should only contain relevant, already-retrieved user data
        (never the whole database).
        """
        system_prompt = (
            "You are the AI Career Copilot, a helpful, honest career assistant "
            "inside the AI Career Copilot platform. Use ONLY the context provided "
            "below about this specific user — never invent facts about their "
            "background. If you don't have enough information to answer, say so "
            "plainly and suggest what the user could add (e.g. upload a resume, "
            "add a job description) to get a better answer. Be concise and practical.\n\n"
            f"User context (JSON):\n{json.dumps(context)}"
        )

        client = _get_client()
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-10:]:  # only recent turns, to control token usage
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=800,
                temperature=0.5,
                messages=messages,
            )
        except (RateLimitError, APITimeoutError, APIError) as exc:
            logger.error("Copilot chat AI failure: %s", exc)
            raise AIServiceError("The AI Copilot is temporarily unavailable. Please try again.") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise AIServiceError("The AI Copilot returned an empty response.")
        return content
