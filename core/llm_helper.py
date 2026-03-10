"""
LLM Helper -- Groq-powered field clarification for legal form filling.
Provides procedural guidance ONLY. Never provides legal advice.
"""

import os
from groq import Groq

# ── System prompt with strict guardrails ─────────────────────────────────────
SYSTEM_PROMPT = """You are a Legal Form Filling Assistant integrated into a Legal Aid Bot.

YOUR ROLE:
- Help users understand what information to write in legal form fields.
- Explain the PURPOSE of each field in simple, easy-to-understand language.
- Describe the FORMAT and TYPE of information expected (dates, names, addresses, amounts, etc.).
- Give examples of what a typical entry looks like.

STRICT RULES YOU MUST FOLLOW:
1. You MUST NOT provide legal advice, legal strategies, or legal recommendations.
2. You MUST NOT suggest what decision the user should take in their legal matter.
3. You MUST NOT interpret laws, court rulings, or legal precedents.
4. You MUST NOT recommend whether to file or not file a case.
5. You MUST NOT draft legal arguments or suggest how to present a case.
6. You MUST only explain what information goes in the field and why it is collected.
7. Keep responses concise (3-5 sentences max).
8. Use simple language that a common citizen can understand.
9. If the user asks for legal advice, politely decline and remind them to consult a qualified advocate.

RESPONSE FORMAT:
- Start with a brief explanation of the field.
- Give the expected format or an example.
- Keep it short and helpful."""

DISCLAIMER = (
    "\n\n_Disclaimer: This is procedural guidance only, not legal advice. "
    "Please consult a qualified legal professional for legal advice._"
)


def _build_context_message(
    dispute_category: str,
    workflow_title: str,
    current_field_key: str,
    current_field_label: str,
    previous_answers: dict,
    questions: list,
    user_query: str,
) -> str:
    """Build the user message with full case context for the LLM."""

    # Build previous Q&A context
    prev_qa_lines = []
    for key, label in questions:
        if key in previous_answers:
            prev_qa_lines.append(f"  - {label}: {previous_answers[key]}")

    prev_context = "\n".join(prev_qa_lines) if prev_qa_lines else "  (No answers yet)"

    message = (
        f"CASE CONTEXT:\n"
        f"- Dispute Type: {dispute_category}\n"
        f"- Procedure: {workflow_title}\n"
        f"\nPREVIOUS ANSWERS GIVEN:\n{prev_context}\n"
        f"\nCURRENT FIELD THE USER NEEDS HELP WITH:\n"
        f"- Field Name: {current_field_label}\n"
        f"- Field Key: {current_field_key}\n"
    )

    if user_query:
        message += f"\nUSER'S SPECIFIC QUESTION:\n{user_query}\n"
    else:
        message += "\nThe user wants to know what to fill in this field.\n"

    return message


def get_field_help(
    dispute_category: str,
    workflow_title: str,
    current_field_key: str,
    current_field_label: str,
    previous_answers: dict,
    questions: list,
    user_query: str = "",
) -> str:
    """
    Query Groq LLM to explain a form field, with full case context.
    Returns the explanation text with disclaimer appended.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "LLM assistance is not available (API key not configured).\n"
            "Please try filling in the field based on the label, "
            "or type 'skip' to skip it." + DISCLAIMER
        )

    try:
        client = Groq(api_key=api_key)

        user_message = _build_context_message(
            dispute_category=dispute_category,
            workflow_title=workflow_title,
            current_field_key=current_field_key,
            current_field_label=current_field_label,
            previous_answers=previous_answers,
            questions=questions,
            user_query=user_query,
        )

        # Terminal logging — show what we're sending to the LLM
        print(f"\n  [LLM] Sending context to Groq (llama-3.3-70b-versatile)...")
        print(f"  [LLM] Context:\n{user_message}")

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=300,
        )

        response = chat_completion.choices[0].message.content.strip()

        # Terminal logging — show LLM response
        print(f"  [LLM] Response received:")
        print(f"  {response}")

        return response + DISCLAIMER

    except Exception as e:
        print(f"  [LLM ERROR] {type(e).__name__}: {e}")
        return (
            f"Sorry, I could not get help for this field right now.\n"
            f"Please try filling it based on the label, or type 'skip' to skip.\n"
            f"(Error: {type(e).__name__})" + DISCLAIMER
        )