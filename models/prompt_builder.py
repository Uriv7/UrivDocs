"""UrivDocs — models/prompt_builder.py"""
from typing import List

SYSTEM = """You are UrivDocs, a precise document Q&A assistant.

STRICT RULES:
1. Answer ONLY from the CONTEXT provided below — do NOT use outside knowledge.
2. If the answer exists in context, give it directly and cite [Source N: file p.X].
3. If the answer is NOT in the context, respond: "I cannot find this in the uploaded documents."
4. For factual questions (names, dates, numbers, codes), quote exactly from context.
5. Use the CONVERSATION HISTORY to understand follow-up questions and references like "that", "it", "the above".
6. Never guess, infer, or make up information not explicitly stated in context.
7. Keep answers concise and accurate."""


def build_rag_prompt(question: str, chunks: List[dict],
                     history: List[dict] = None) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        text  = c["text"][:600].strip()
        label = f"[Source {i}: {c['source']} p.{c['page_number']}]"
        parts.append(f"{label}\n{text}")
    context = "\n\n---\n\n".join(parts)

    history_text = ""
    if history:
        recent = history[-6:]
        lines  = []
        for msg in recent:
            role    = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        if lines:
            history_text = "\n\nCONVERSATION HISTORY:\n" + "\n".join(lines)

    return f"""{SYSTEM}

CONTEXT FROM DOCUMENTS:
{context}
{history_text}

CURRENT QUESTION: {question}

ANSWER (cite sources, or say not found):"""
