"""
Multi-model LLM generation — supports Groq, Anthropic, Gemini, OpenAI.
"""

from typing import List, Dict, Optional
from rag_bot.config import LLM_PROVIDER, LLM_MODEL, LLM_API_KEY


def _call_llm(system: str, messages: List[Dict], max_tokens: int = 4096) -> str:
    """Route to the correct LLM provider."""
    provider = LLM_PROVIDER.lower()

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=LLM_API_KEY)
        full_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=LLM_API_KEY)
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=LLM_API_KEY)
        model = genai.GenerativeModel(LLM_MODEL, system_instruction=system)
        prompt = "\n\n".join(m["content"] for m in messages)
        response = model.generate_content(prompt)
        return response.text

    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=LLM_API_KEY)
        full_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def build_system_prompt() -> str:
    return (
        "You are an expert IT infrastructure assistant specializing in enterprise networking, "
        "servers, firewalls, and end-user computing. You have access to documentation from vendors "
        "including Cisco, Juniper, Fortinet, Dell, IBM, and others.\n\n"
        "Guidelines:\n"
        "- Answer questions clearly and concisely based on the provided context\n"
        "- Cite specific documents and pages when possible\n"
        "- If the context doesn't contain enough information, say so honestly\n"
        "- Use technical terminology appropriately\n"
        "- Format responses with markdown when helpful (headers, lists, code blocks)\n"
    )


def generate_answer(
    question: str,
    context_chunks: List[str],
    metadatas: List[Dict],
    conversation_history: Optional[List[Dict]] = None,
    system_prompt: Optional[str] = None,
) -> str:
    context_parts = []
    for i, (chunk, meta) in enumerate(zip(context_chunks, metadatas)):
        vendor = meta.get("vendor", "Unknown")
        doc = meta.get("document", "Unknown")
        page = meta.get("page", "n/a")
        context_parts.append(f"[Source {i+1}: {vendor} - {doc}, Page {page}]\n{chunk}")
    context_str = "\n\n".join(context_parts)

    messages = []
    if conversation_history:
        messages.extend(conversation_history)

    user_message = (
        f"Context from documentation:\n\n{context_str}\n\n"
        f"Question: {question}\n\n"
        "Please answer based on the context above. Cite sources when relevant."
    )
    messages.append({"role": "user", "content": user_message})

    return _call_llm(system_prompt or build_system_prompt(), messages)
