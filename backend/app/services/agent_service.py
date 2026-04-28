"""
LangChain ReAct Agent — AI Study Coach
=======================================
A true tool-using agent (not just a prompt).  The agent autonomously decides
which tools to call, calls them, observes results, and continues reasoning
until it has a complete answer.

LLM: Gemini 2.5 Flash via langchain-google-genai
Agent type: Tool-calling (function-calling) agent with ReAct reasoning

Tools available:
  1. search_visa_requirements   — RAG query on ChromaDB visa docs
  2. search_universities        — live DB query for matching universities
  3. calculate_financial_roi    — ROI / break-even maths
  4. schedule_calendar_event    — creates a real Google Calendar event
  5. get_scholarship_info       — RAG query focused on scholarships

The public entry point is:
    agent_coach_chat(message, profile, history, db) → dict
        {
          "reply":       str,      # final answer
          "tool_calls":  list,     # which tools were invoked (for UI display)
          "agent_used":  bool,     # True always from this module
        }
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── LangChain imports ──────────────────────────────────────────────────────────
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain.tools import tool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import AIMessage, HumanMessage
    _LANGCHAIN_OK = True
except ImportError as e:
    logger.warning("LangChain import failed — agent will degrade gracefully: %s", e)
    _LANGCHAIN_OK = False


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# Each tool is a Python function decorated with @tool.
# The agent reads the docstring to decide when to call the tool.
# ═══════════════════════════════════════════════════════════════════════════════

def _make_tools(profile: dict, db_session=None):
    """
    Factory that creates tool instances with the user's profile and DB session
    captured in their closure.  Called once per agent invocation.
    """

    # ── Tool 1: Visa Requirements ────────────────────────────────────────────

    @tool
    def search_visa_requirements(country: str) -> str:
        """
        Search the visa requirements database for a specific country.
        Use this when the user asks about visa documents, fees, processing time,
        financial requirements, language tests, or any other visa-related question
        for a specific country.

        Args:
            country: The destination country (e.g. 'UK', 'USA', 'Canada', 'Germany')
        """
        try:
            from app.services.rag import get_visa_assistant_chain
            chain = get_visa_assistant_chain()
            query = f"What are the student visa requirements for {country}? Include documents, fees, processing time, financial requirements."
            result = chain.invoke({"input": query, "country": country, "session_id": "agent"})
            if isinstance(result, dict):
                return result.get("answer", str(result))
            return str(result)
        except Exception as e:
            logger.error("Visa RAG tool error: %s", e)
            # Fallback to static data from ai_agent.py
            try:
                from app.services.ai_agent import VISA_DOCUMENTS
                norm = country.strip().title()
                if norm in VISA_DOCUMENTS:
                    vd = VISA_DOCUMENTS[norm]
                    cats = vd.get("categories", {})
                    lines = [f"Visa type: {vd.get('visa_type', 'Student Visa')}",
                             f"Fee: ~${vd.get('visa_fee_usd', 'N/A')} USD",
                             f"Processing: ~{vd.get('timeline_weeks', 'N/A')} weeks"]
                    for cat, items in cats.items():
                        lines.append(f"\n{cat}:")
                        lines.extend(f"  - {item}" for item in items[:4])
                    return "\n".join(lines)
                return f"No visa data found for {country}. Please check official embassy website."
            except Exception:
                return f"Could not retrieve visa requirements for {country}."

    # ── Tool 2: University Search ────────────────────────────────────────────

    @tool
    def search_universities(
        field_of_study: str = "",
        country: str = "",
        max_budget_usd: float = 0,
        limit: int = 5,
    ) -> str:
        """
        Search for universities that match specified criteria.
        Use this when the user asks about universities, rankings, tuition fees,
        which universities are good for their profile, or needs recommendations.

        Args:
            field_of_study: Subject area (e.g. 'Computer Science', 'MBA', 'Data Science')
            country:        Filter by country (e.g. 'United Kingdom', 'USA')
            max_budget_usd: Maximum annual total cost in USD (0 = no limit)
            limit:          Number of results to return (default 5)
        """
        try:
            if db_session is None:
                return "Database not available in this context."

            from app.models.university import University
            from sqlalchemy import or_
            import re

            query = db_session.query(University)

            if country:
                query = query.filter(University.country.ilike(f"%{country}%"))

            if field_of_study:
                kw = field_of_study.replace(" ", "%")
                query = query.filter(University.subject.ilike(f"%{kw}%"))

            if max_budget_usd and max_budget_usd > 0:
                # DB stores costs in INR; convert threshold to INR
                # Use COALESCE to treat NULL as 0 so rows with missing costs are included
                from sqlalchemy import func as _func
                max_inr = max_budget_usd * 83.0
                query = query.filter(
                    or_(
                        University.tuition.is_(None),
                        (
                            _func.coalesce(University.tuition, 0) +
                            _func.coalesce(University.living_cost, 0)
                        ) <= max_inr,
                    )
                )

            unis = query.order_by(University.ranking.asc()).limit(limit).all()

            if not unis:
                return f"No universities found matching those criteria. Try broader parameters."

            lines = [f"Found {len(unis)} universities:\n"]
            for u in unis:
                tuition_usd = round((u.tuition or 0) / 83) if u.tuition else None
                living_usd  = round((u.living_cost or 0) / 83) if u.living_cost else None
                total_usd   = (tuition_usd or 0) + (living_usd or 0)
                lines.append(
                    f"• {u.name} ({u.country})"
                    f" | Rank #{u.ranking or '?'}"
                    f" | Subject: {(u.subject or '').split('|')[0].strip()}"
                    f" | Total cost: ~${total_usd:,}/yr"
                    f" | CGPA req: {u.requirements_cgpa or 'N/A'}"
                    f" | IELTS: {u.ielts or 'N/A'}"
                )
            return "\n".join(lines)

        except Exception as e:
            logger.error("University search tool error: %s", e)
            return f"Could not search universities: {e}"

    # ── Tool 3: Financial ROI Calculator ────────────────────────────────────

    @tool
    def calculate_financial_roi(
        country: str,
        annual_cost_usd: float,
        degree_years: int = 2,
    ) -> str:
        """
        Calculate the financial return on investment (ROI) for studying in a country.
        Use this when the user asks about whether studying abroad is worth it financially,
        how long to pay back student loans, expected salaries, or cost-benefit analysis.

        Args:
            country:         Destination country (e.g. 'United Kingdom', 'Canada')
            annual_cost_usd: Total annual cost (tuition + living) in USD
            degree_years:    Duration of degree in years (default 2)
        """
        try:
            from app.services.recommendation import GRAD_SALARY_USD, JOB_SCORE, POST_STUDY_WORK

            salary  = GRAD_SALARY_USD.get(country, 55000)
            js      = JOB_SCORE.get(country, 7.0)
            psw     = POST_STUDY_WORK.get(country, 0.75)

            total_cost = annual_cost_usd * degree_years
            net_salary = salary * 0.72   # after-tax ~28%
            annual_repay = net_salary * 0.30  # 30% disposable income

            break_even = round(total_cost / annual_repay, 1) if annual_repay > 0 else None
            roi_5yr    = round(((net_salary * 5) - total_cost) / total_cost * 100, 1)

            return (
                f"Financial ROI Analysis — Studying in {country}:\n"
                f"  Total degree cost:       ${total_cost:,.0f} USD (${annual_cost_usd:,.0f}/yr × {degree_years} yrs)\n"
                f"  Expected grad salary:    ${salary:,}/yr\n"
                f"  After-tax take-home:     ${net_salary:,.0f}/yr\n"
                f"  Break-even period:       {break_even} years (at 30% of take-home)\n"
                f"  5-year net ROI:          {roi_5yr}%\n"
                f"  Job market score:        {js}/10\n"
                f"  Post-study work access:  {int(psw * 100)}% of student-visa holders can extend\n"
                f"\n"
                f"  {'Strong ROI' if roi_5yr > 50 else 'Moderate ROI' if roi_5yr > 0 else 'Negative ROI at 5 years'} — "
                f"degree pays back in {break_even} years."
            )
        except Exception as e:
            return f"Could not compute ROI: {e}"

    # ── Tool 4: Google Calendar ──────────────────────────────────────────────

    @tool
    def schedule_calendar_event(
        title: str,
        days_from_today: int,
        description: str = "",
        duration_minutes: int = 30,
    ) -> str:
        """
        Create a real Google Calendar event / reminder for the user.
        Use this when the user asks to set a reminder, schedule a deadline,
        add something to their calendar, or plan application tasks.

        Args:
            title:            Calendar event title (e.g. 'Submit UK visa application')
            days_from_today:  When to schedule it (1 = tomorrow, 7 = next week, etc.)
            description:      Optional notes for the event
            duration_minutes: Event duration in minutes (default 30)
        """
        try:
            from app.services.calendar_service import create_calendar_event

            start = datetime.now() + timedelta(days=days_from_today)
            start = start.replace(hour=10, minute=0, second=0, microsecond=0)

            result = create_calendar_event(
                title=f"[udaan] {title}",
                start_datetime=start,
                description=description or f"Study abroad reminder set by udaan AI Coach.\n\n{description}",
                duration_minutes=duration_minutes,
            )

            if result.get("success"):
                return (
                    f"Calendar event created successfully!\n"
                    f"  Title: {title}\n"
                    f"  Date:  {start.strftime('%B %d, %Y at %I:%M %p')}\n"
                    f"  Link:  {result.get('event_link', 'Check your Google Calendar')}\n"
                    f"\nThe event will appear in your Google Calendar with reminders at 24h and 30min before."
                )
            else:
                # Calendar not configured — give helpful fallback
                msg = result.get("message", result.get("error", "Unknown error"))
                return (
                    f"Note: Google Calendar integration requires setup. {msg}\n"
                    f"In the meantime, here's your reminder:\n"
                    f"  Task:   {title}\n"
                    f"  Target: {(datetime.now() + timedelta(days=days_from_today)).strftime('%B %d, %Y')}"
                )
        except Exception as e:
            logger.error("Calendar tool error: %s", e)
            return f"Could not create calendar event: {e}"

    # ── Tool 5: Scholarship Info ─────────────────────────────────────────────

    @tool
    def get_scholarship_info(query: str) -> str:
        """
        Search for scholarship opportunities related to the query.
        Use this when the user asks about funding, scholarships, grants, fellowships,
        financial aid, or how to reduce study abroad costs.

        Args:
            query: Scholarship search query (e.g. 'scholarships for Indian students in UK')
        """
        try:
            from app.services.rag import get_visa_assistant_chain
            chain = get_visa_assistant_chain()
            result = chain.invoke({
                "input": f"scholarships and funding: {query}",
                "country": "General",
                "session_id": "agent_scholarship",
            })
            if isinstance(result, dict):
                return result.get("answer", str(result))
            return str(result)
        except Exception as e:
            return (
                "Popular scholarships for Indian students:\n"
                "• Chevening Scholarship (UK) — fully funded, merit-based\n"
                "• Commonwealth Scholarship (UK/Canada/Australia) — for developing countries\n"
                "• DAAD Scholarship (Germany) — fully funded, research focus\n"
                "• Fulbright-Nehru Fellowships (USA) — prestigious, covers all costs\n"
                "• Australia Awards — Australian government, STEM focus\n"
                "• Erasmus Mundus (Europe) — EU-funded, multiple country programmes\n"
                "• Inlaks Shivdasani Foundation (UK/USA/Europe) — Indian students only\n"
                "Visit the official scholarship websites for current deadlines."
            )

    return [
        search_visa_requirements,
        search_universities,
        calculate_financial_roi,
        schedule_calendar_event,
        get_scholarship_info,
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """You are udaan's AI Study Coach — an expert, warm, and practical advisor
for Indian students planning to study abroad.

You have access to specialised tools:
- search_visa_requirements: Get accurate visa document/fee/timeline info
- search_universities: Find universities matching study field, country, budget
- calculate_financial_roi: Compute ROI, break-even, salary projections
- schedule_calendar_event: Create REAL events in the user's Google Calendar
- get_scholarship_info: Find scholarships and funding options

STUDENT PROFILE (use this to personalise every response):
{profile_summary}

INSTRUCTIONS:
1. Always use tools when you need factual data — don't guess visa fees or deadlines
2. When the user asks to set a reminder or add something to calendar, ALWAYS use schedule_calendar_event
3. If the user asks about a university in a specific country, use search_universities first
4. Combine tool results into a concise, actionable answer
5. Write in clear, friendly English — avoid jargon
6. End with 1-2 concrete next steps the student should take
7. Never fabricate statistics; use the tool results"""


def _build_profile_summary(profile: dict) -> str:
    """Convert profile dict to a readable summary for the system prompt."""
    if not profile:
        return "No profile information provided."

    lines = []
    if profile.get("name"):
        lines.append(f"Name: {profile['name']}")
    if profile.get("field_of_study"):
        lines.append(f"Field: {profile['field_of_study']}")
    if profile.get("preferred_degree"):
        lines.append(f"Degree: {profile['preferred_degree']}")
    if profile.get("cgpa"):
        lines.append(f"CGPA: {profile['cgpa']}/10")
    if profile.get("english_score"):
        test = profile.get("english_test", "IELTS")
        lines.append(f"English: {test} {profile['english_score']}")
    if profile.get("target_countries"):
        countries = profile["target_countries"]
        if isinstance(countries, list):
            lines.append(f"Target countries: {', '.join(countries)}")
        else:
            lines.append(f"Target countries: {countries}")
    if profile.get("budget"):
        lines.append(f"Budget: ${profile['budget']:,}/yr USD")
    elif profile.get("budget_inr"):
        lines.append(f"Budget: ₹{profile['budget_inr']:,.0f}/yr")
    if profile.get("career_goal"):
        lines.append(f"Career goal: {profile['career_goal']}")
    if profile.get("work_experience_years"):
        lines.append(f"Work experience: {profile['work_experience_years']} years")
    if profile.get("intake_preference"):
        lines.append(f"Preferred intake: {profile['intake_preference']}")

    return "\n".join(lines) if lines else "Basic profile — encourage user to complete their profile."


def _convert_history(history: list) -> list:
    """Convert API history format [{"role": "user", "content": "..."}] to LangChain messages."""
    messages = []
    for msg in history[-10:]:   # last 10 messages to keep context window manageable
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role in ("assistant", "model"):
            messages.append(AIMessage(content=content))
    return messages


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def agent_coach_chat(
    message: str,
    profile: dict,
    history: list,
    db=None,
) -> dict:
    """
    Run the LangChain ReAct agent and return a structured response.

    Returns:
        {
            "reply":      str,   # the agent's final answer
            "tool_calls": list,  # [{"tool": name, "input": ..., "output": ...}]
            "agent_used": bool,  # True when agent ran successfully
        }
    """
    if not _LANGCHAIN_OK:
        return _fallback_chat(message, profile)

    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return _fallback_chat(message, profile)

    try:
        # Build LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.3,
            max_output_tokens=2048,
        )

        # Build tools (with profile + db captured in closure)
        tools = _make_tools(profile=profile, db_session=db)

        # Build prompt
        profile_summary = _build_profile_summary(profile)
        system_content  = _SYSTEM_PROMPT.format(profile_summary=profile_summary)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=6,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        # Convert history
        chat_history = _convert_history(history)

        # Run
        result = executor.invoke({
            "input": message,
            "chat_history": chat_history,
        })

        # Extract tool calls from intermediate steps
        tool_calls = []
        for step in result.get("intermediate_steps", []):
            if len(step) >= 2:
                action, observation = step[0], step[1]
                tool_calls.append({
                    "tool":        action.tool if hasattr(action, "tool") else str(action),
                    "input":       action.tool_input if hasattr(action, "tool_input") else {},
                    "output":      str(observation)[:500],   # truncate long outputs
                })

        return {
            "reply":      result.get("output", "I couldn't generate a response. Please try again."),
            "tool_calls": tool_calls,
            "agent_used": True,
        }

    except Exception as e:
        logger.error("Agent execution error: %s", e, exc_info=True)
        # Graceful fallback — call the old non-agent function
        return _fallback_chat(message, profile, error=str(e))


def _fallback_chat(message: str, profile: dict, error: str = "") -> dict:
    """
    Fallback when the agent cannot run.
    Delegates to the existing ai_agent.py ai_coach_chat function.
    """
    try:
        from app.services.ai_agent import ai_coach_chat
        reply = ai_coach_chat(message, profile, [])
        return {
            "reply":      reply,
            "tool_calls": [],
            "agent_used": False,
        }
    except Exception as e2:
        return {
            "reply":      "I'm having trouble connecting right now. Please try again in a moment.",
            "tool_calls": [],
            "agent_used": False,
        }
