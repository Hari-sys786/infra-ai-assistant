"""
LLM generation using Anthropic Claude API.
"""

from typing import List, Dict, Optional
import anthropic

from rag_bot.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def get_client() -> anthropic.Anthropic:
    """Get Anthropic client."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def build_system_prompt() -> str:
    """System prompt for the RAG assistant."""
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
    """
    Generate an answer using Claude with context and optional conversation history.
    """
    client = get_client()

    # Build context string with source info
    context_parts = []
    for i, (chunk, meta) in enumerate(zip(context_chunks, metadatas)):
        vendor = meta.get("vendor", "Unknown")
        doc = meta.get("document", "Unknown")
        page = meta.get("page", "n/a")
        context_parts.append(
            f"[Source {i+1}: {vendor} - {doc}, Page {page}]\n{chunk}"
        )
    context_str = "\n\n".join(context_parts)

    # Build messages
    messages = []
    if conversation_history:
        messages.extend(conversation_history)

    # Add current question with context
    user_message = (
        f"Context from documentation:\n\n{context_str}\n\n"
        f"Question: {question}\n\n"
        "Please answer based on the context above. Cite sources when relevant."
    )
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt or build_system_prompt(),
        messages=messages,
    )
    return response.content[0].text


def generate_comparison(
    vendors: List[str],
    vendor_contexts: Dict[str, List[str]],
    vendor_metadatas: Dict[str, List[Dict]],
    topic: str,
) -> str:
    """Generate a structured comparison table between vendors."""
    client = get_client()

    context_parts = []
    for vendor in vendors:
        chunks = vendor_contexts.get(vendor, [])
        metas = vendor_metadatas.get(vendor, [])
        if chunks:
            vendor_context = "\n".join(chunks[:5])
            context_parts.append(f"=== {vendor} Documentation ===\n{vendor_context}")

    context_str = "\n\n".join(context_parts)

    system = (
        "You are an expert IT infrastructure analyst. Create detailed, structured "
        "comparisons between vendors/products based on documentation. "
        "Always produce a markdown table with clear categories."
    )

    user_message = (
        f"Compare the following vendors/topics: {', '.join(vendors)}\n\n"
        f"Topic: {topic}\n\n"
        f"Documentation context:\n\n{context_str}\n\n"
        "Create a structured comparison table with these categories where applicable:\n"
        "- Features\n- Performance\n- Security\n- Management/Administration\n"
        "- Scalability\n- Pricing Notes\n- Key Strengths\n- Key Limitations\n\n"
        "Use a markdown table format. If information is not available in the docs, note it."
    )

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_config(
    context_chunks: List[str],
    metadatas: List[Dict],
    config_request: str,
) -> str:
    """Generate configuration snippets based on documentation context."""
    client = get_client()

    context_str = "\n\n".join(context_chunks[:5])

    system = (
        "You are an expert network/systems engineer. Generate accurate, production-ready "
        "configuration snippets based on vendor documentation. Include comments explaining "
        "each section. If the docs don't cover the exact config requested, provide the closest "
        "match with appropriate warnings."
    )

    user_message = (
        f"Configuration request: {config_request}\n\n"
        f"Relevant documentation:\n\n{context_str}\n\n"
        "Generate the requested configuration. Include:\n"
        "1. The configuration snippet in a code block\n"
        "2. Brief explanation of each section\n"
        "3. Any prerequisites or important notes\n"
        "4. Common variations or options"
    )

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_troubleshoot(
    context_chunks: List[str],
    metadatas: List[Dict],
    problem_description: str,
    conversation_history: Optional[List[Dict]] = None,
) -> str:
    """Generate troubleshooting steps based on documentation and problem description."""
    client = get_client()

    context_str = "\n\n".join(context_chunks[:5])

    system = (
        "You are an expert IT troubleshooting assistant. Help diagnose and resolve "
        "IT infrastructure issues step by step. Be methodical:\n"
        "1. First, clarify the problem if needed by asking specific questions\n"
        "2. Identify potential root causes\n"
        "3. Suggest diagnostic commands/steps\n"
        "4. Provide solutions based on the documentation\n"
        "5. Suggest preventive measures\n\n"
        "If you need more information, ask clarifying questions."
    )

    messages = []
    if conversation_history:
        messages.extend(conversation_history)

    user_message = (
        f"Problem: {problem_description}\n\n"
        f"Relevant documentation:\n\n{context_str}\n\n"
        "Please help diagnose and resolve this issue."
    )
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=messages,
    )
    return response.content[0].text
