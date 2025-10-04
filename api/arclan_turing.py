from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import openai
import os
import re
import json
from pathlib import Path
from datetime import datetime

router = APIRouter()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    telegram_user_id: str
    telegram_username: Optional[str] = None
    conversation_history: Optional[str] = ""

class ChatResponse(BaseModel):
    reply: str
    has_answer: bool
    sources_used: List[str]
    category: str

# --- RAG Document Structure ---
RAG_DOCS = {
    "ryzome": {},      # Platform documentation (flagship product)
    "rig": {},         # Framework documentation (flagship product)
    "arc_core": {},    # Core ARC token/project docs
    "arc_ecosystem": {}, # Ecosystem: partnerships, projects, vision
    "news": {},        # Latest updates, announcements
    "roadmap": {},     # Upcoming features, goals, timeline
    "podcasts": {},    # Podcast episodes, interviews, discussions
    "filters": {}      # Telegram filter commands/keywords
}

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠ Warning: File not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠ Warning: Invalid JSON in {file_path}: {e}")
        return {}

def format_filters_for_context(filters_data: Dict[str, Any]) -> str:
    """Format filters JSON into readable context for AI"""
    if not filters_data:
        return ""
    
    formatted = ["AVAILABLE FILTERS/COMMANDS:\n"]
    
    for command, details in filters_data.items():
        formatted.append(f"\nCommand: {command}")
        if details.get("response_text"):
            formatted.append(f"  Response: {details['response_text']}")
        if details.get("media"):
            formatted.append(f"  Media: {details['media']} ({details.get('type', 'unknown')})")
    
    return "\n".join(formatted)

def format_podcasts_for_context(podcasts_data: Dict[str, Any]) -> str:
    """Format podcasts JSON into readable context for AI"""
    if not podcasts_data or not podcasts_data.get("podcasts"):
        return ""
    
    formatted = ["HELLO, COMPLEX PODCAST EPISODES:\n"]
    
    for podcast in podcasts_data["podcasts"]:
        formatted.append(f"\n📻 {podcast.get('title', 'Untitled')}")
        formatted.append(f"   Listen: {podcast.get('url', 'N/A')}")
    
    if podcasts_data.get("last_updated"):
        formatted.append(f"\nLast Updated: {podcasts_data['last_updated']}")
    
    return "\n".join(formatted)

def format_posts_for_context(posts_data: Dict[str, Any]) -> str:
    """Format latest posts JSON into readable context for AI"""
    if not posts_data or not posts_data.get("latest_posts"):
        return ""
    
    formatted = ["LATEST POSTS & ANNOUNCEMENTS:\n"]
    
    for post in posts_data["latest_posts"]:
        formatted.append(f"\n📢 {post.get('summary', 'No summary')[:100]}...")
        formatted.append(f"   Author: @{post.get('author', 'unknown')}")
        formatted.append(f"   Link: {post.get('url', 'N/A')}")
        if post.get("keywords"):
            formatted.append(f"   Tags: {', '.join(post['keywords'])}")
    
    if posts_data.get("last_updated_index"):
        formatted.append(f"\nLast Updated Index: {posts_data['last_updated_index']}")
    
    return "\n".join(formatted)

def format_filters_for_context(filters_data: Dict[str, Any]) -> str:
    """Format filters JSON into readable context for AI"""
    if not filters_data:
        return ""
    
    formatted = ["AVAILABLE FILTERS/COMMANDS:\n"]
    
    for command, details in filters_data.items():
        formatted.append(f"\nCommand: {command}")
        if details.get("response_text"):
            formatted.append(f"  Response: {details['response_text']}")
        if details.get("media"):
            formatted.append(f"  Media: {details['media']} ({details.get('type', 'unknown')})")
    
    return "\n".join(formatted)

def load_rag_documents() -> Dict[str, Any]:
    """Load all RAG documents from organized folders (JSON format)"""
    base_path = Path(__file__).parent.parent  # Gets to project root
    rag_path = base_path / "data" / "rag"     # Add "data" here
    filters_path = base_path / "filters"
    
    loaded_docs = {}
    
    # Define paths - JSON files for embeddings, reference external filters
    doc_files = {
        "ryzome": rag_path / "ryzome" / "platform.json",
        "rig": rag_path / "rig" / "framework.json",
        "arc_core": rag_path / "arc" / "core.json",
        "arc_ecosystem": rag_path / "arc" / "ecosystem.json",
        "news": filters_path / "posts.json",
        "roadmap": rag_path / "roadmap" / "upcoming.json",
        "podcasts": filters_path / "podcasts.json",
        "filters": filters_path / "filters.json"
    }
    
    for key, file_path in doc_files.items():
        data = load_json_file(file_path)
        
        # Format external data sources for AI context
        if key == "filters":
            loaded_docs[key] = format_filters_for_context(data)
            print(f"✓ Loaded {key}: {len(data)} commands")
        elif key == "podcasts":
            loaded_docs[key] = format_podcasts_for_context(data)
            episode_count = len(data.get("podcasts", []))
            print(f"✓ Loaded {key}: {episode_count} episodes")
        elif key == "news":
            loaded_docs[key] = format_posts_for_context(data)
            post_count = len(data.get("latest_posts", []))
            print(f"✓ Loaded {key}: {post_count} posts")
        else:
            loaded_docs[key] = data
            # Calculate size based on JSON structure
            size = len(json.dumps(data)) if data else 0
            print(f"✓ Loaded {key}: {size} chars")
    
    return loaded_docs

# Cache the docs in memory
RAG_DOCS = load_rag_documents()

def categorize_message(message: str) -> str:
    """Categorize message to determine relevant docs"""
    lower_message = message.lower()
    
    # Platform-specific (flagship)
    if re.search(r'\b(ryzome|platform|dashboard|interface|ui)\b', lower_message):
        return 'ryzome'
    
    # Framework-specific (flagship)
    if re.search(r'\b(rig|framework|api|sdk|development|integrate|build)\b', lower_message):
        return 'rig'
    
    # Token/Core project
    if re.search(r'\b(arc|token|price|buy|swap|trade|tokenomics|utility)\b', lower_message):
        return 'arc_core'
    
    # Ecosystem (partnerships, projects, vision)
    if re.search(r'\b(partner|ecosystem|vision|mission|team|community|collab|project)\b', lower_message):
        return 'arc_ecosystem'
    
    # News/updates
    if re.search(r'\b(news|update|announcement|latest|recent|new|launch)\b', lower_message):
        return 'news'
    
    # Podcasts/interviews
    if re.search(r'\b(podcast|episode|interview|listen|audio|talk|discussion|show)\b', lower_message):
        return 'podcasts'
    
    # Roadmap/future
    if re.search(r'\b(roadmap|upcoming|future|plan|when|timeline|release)\b', lower_message):
        return 'roadmap'
    
    # Filter/command related
    if re.search(r'\b(filter|command|bot|help)\b', lower_message):
        return 'filters'
    
    # Greetings
    if re.search(r'\b(hello|hi|hey|gm|wagmi|gn)\b', lower_message):
        return 'greeting'
    
    return 'general'

def get_relevant_docs(category: str, message: str) -> Dict[str, Any]:
    """Get relevant documentation based on message category"""
    relevant = {}
    
    if category == 'greeting':
        # For greetings, provide high-level overview from ARC ecosystem
        relevant['arc_ecosystem'] = RAG_DOCS['arc_ecosystem']
        return relevant
    
    # Always include the primary category docs
    if category in RAG_DOCS and RAG_DOCS[category]:
        relevant[category] = RAG_DOCS[category]
    
    # Add contextual docs based on keywords
    lower_message = message.lower()
    
    # If asking about ecosystem/vision, include all major components
    if 'arc_ecosystem' in category or any(word in lower_message for word in ['ecosystem', 'vision', 'mission', 'about', 'partners']):
        relevant['arc_ecosystem'] = RAG_DOCS['arc_ecosystem']
        # Ecosystem includes overview of flagship products
        if 'ryzome' in lower_message or 'platform' in lower_message:
            relevant['ryzome'] = RAG_DOCS['ryzome']
        if 'rig' in lower_message or 'framework' in lower_message or 'developer' in lower_message:
            relevant['rig'] = RAG_DOCS['rig']
    
    # If asking about ARC core (token), include core + ecosystem context
    if 'arc_core' in category:
        relevant['arc_core'] = RAG_DOCS['arc_core']
        relevant['arc_ecosystem'] = RAG_DOCS['arc_ecosystem']
    
    # If asking about future/plans, include roadmap
    if any(word in lower_message for word in ['future', 'plan', 'upcoming', 'roadmap', 'when']):
        relevant['roadmap'] = RAG_DOCS['roadmap']
    
    # If asking about podcasts/interviews/discussions
    if any(word in lower_message for word in ['podcast', 'episode', 'interview', 'listen', 'talk']):
        relevant['podcasts'] = RAG_DOCS['podcasts']
    
    # Always include filters context if asking about commands
    if 'filters' in category or any(word in lower_message for word in ['command', 'filter', 'slash']):
        relevant['filters'] = RAG_DOCS['filters']
    
    # Remove empty docs
    relevant = {k: v for k, v in relevant.items() if v}
    
    return relevant

# --- Main Chat Endpoint ---

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """
    Handle Telegram chat messages with RAG-based AI responses.
    Only responds if information is available in internal docs.
    """
    try:
        message = chat_request.message
        telegram_user_id = chat_request.telegram_user_id
        telegram_username = chat_request.telegram_username
        conversation_history = chat_request.conversation_history or ""
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="No message provided")
        
        # Categorize message and get relevant docs
        category = categorize_message(message)
        relevant_docs = get_relevant_docs(category, message)
        
        if not relevant_docs and category != 'greeting':
            return ChatResponse(
                reply="don't have that info - @RedCandleGod can help 🤝",
                has_answer=False,
                sources_used=[],
                category=category
            )
        
        # Format docs for context
        docs_context = []
        for source, content in relevant_docs.items():
            if source in ["filters", "podcasts", "news"]:
                # External sources already formatted as string
                docs_context.append(f"=== {source.upper()} ===\n{content}")
            else:
                # JSON data from RAG - convert to readable format
                json_str = json.dumps(content, indent=2)
                docs_context.append(f"=== {source.upper()} DOCUMENTATION ===\n{json_str}")
        
        docs_context = "\n\n".join(docs_context)
        
        # --- Build system prompt ---
        system_prompt = """
You are an AI assistant for the ARC ecosystem - a cutting-edge AI-focused crypto project.

The ARC ecosystem consists of:
- **ARC (Core)**: The main project and token that powers everything
- **RYZOME**: Flagship AI platform/dashboard (part of ARC ecosystem)
- **RIG**: Flagship development framework for builders (part of ARC ecosystem)
- **Ecosystem**: Network of partnerships, projects, and community vision

CRITICAL INSTRUCTIONS:
1. ONLY answer questions using information from the provided documentation
2. Keep responses EXTREMELY brief - as few words as possible (1-2 sentences max)
3. Be casual, friendly, and use crypto community language (gm, wagmi, anon, etc.)
4. For greetings: respond warmly but briefly (e.g., "gm anon! how can i help? 👀")
5. If documentation doesn't have the answer: "don't have that info - @RedCandleGod can help 🤝"
6. NEVER provide price predictions or financial advice
7. Use lowercase for casual vibe unless it's a proper noun or emphasis

FILTER/COMMAND HANDLING:
- If user types a filter/command that doesn't exist, suggest the closest match
- Be helpful and brief: "looks like you meant /[correct_command] 👀" or "try /[similar_command] instead ✨"
- Reference the FILTERS documentation to find similar commands
- Use fuzzy logic - if they type /eco, suggest /arc_ecosystem
- If they type ca suggest showing the contract address
- Always be helpful, never condescending

Examples:
- User: "what is arc?" → "arc is an ai-focused crypto project with flagship products ryzome (platform) and rig (dev framework) 🚀"
- User: "gm" → "gm anon! what brings you here? 👀"
- User: "/tokenomic" → "looks like you meant /tokenomics 👉 https://www.arc.fun/tokenomics"
- User: "/eco" → "try /arc_ecosystem instead ✨"
- User: "when moon?" → "don't have that info - @RedCandleGod can help 🤝"

Tone: Ultra casual, brief, helpful, crypto-native
"""
        
        # --- Build user prompt ---
        user_prompt = f"""
AVAILABLE DOCUMENTATION:
{docs_context if docs_context else "No specific documentation loaded for this query."}

CONVERSATION HISTORY:
{conversation_history[-500:] if conversation_history else "First message"}

USER'S MESSAGE: {message}
MESSAGE CATEGORY: {category}

TASK:
- If greeting: respond warmly but briefly (e.g., "gm! how can i help? 👀")
- If question: use ONLY the documentation to answer in as few words as possible
- If filter/command doesn't exist: suggest the closest match from available filters
- If info not in docs: "don't have that - @RedCandleGod can help 🤝"
- Be ultra casual, brief, and helpful
- Emphasize ARC as main project, Ryzome and RIG as flagship products
- ALWAYS respond with absolute minimum words needed
"""
        
        # --- Generate AI response ---
        completion = await openai.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=150  # Reduced for brevity
        )
        
        ai_message = completion.choices[0].message.content or \
            "having trouble rn, try again? 🔄"
        
        # Determine if we provided an answer or deflected
        deflection_phrases = [
            "don't have",
            "not in my",
            "grab the team",
            "grab someone"
        ]
        has_answer = not any(phrase in ai_message.lower() for phrase in deflection_phrases)
        
        # Track which sources were used
        sources_used = list(relevant_docs.keys()) if has_answer else []
        
        return ChatResponse(
            reply=ai_message,
            has_answer=has_answer,
            sources_used=sources_used,
            category=category
        )
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="I'm experiencing technical difficulties. Please try again! 🔧"
        )


# --- Reload docs endpoint ---
@router.post("/reload-docs")
async def reload_docs():
    """Reload all RAG documentation from files"""
    global RAG_DOCS
    try:
        RAG_DOCS = load_rag_documents()
        
        stats = {
            doc: len(content) for doc, content in RAG_DOCS.items()
        }
        
        return {
            "status": "success",
            "message": "All RAG documents reloaded",
            "timestamp": datetime.utcnow().isoformat(),
            "documents": stats,
            "total_size": sum(stats.values())
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload docs: {str(e)}"
        )


# --- Health check endpoint ---
@router.get("/health")
async def health_check():
    """Health check with RAG status"""
    loaded_docs = {k: len(v) > 0 for k, v in RAG_DOCS.items()}
    
    return {
        "status": "healthy",
        "service": "arc_telegram_ai_chat",
        "rag_system": "active",
        "documents_loaded": loaded_docs,
        "total_docs": len([v for v in loaded_docs.values() if v]),
        "timestamp": datetime.utcnow().isoformat()
    }


# --- Get doc stats endpoint ---
@router.get("/docs/stats")
async def get_docs_stats():
    """Get statistics about loaded documentation"""
    stats = {}
    
    for doc_name, content in RAG_DOCS.items():
        stats[doc_name] = {
            "loaded": len(content) > 0,
            "size": len(content),
            "lines": content.count('\n') if content else 0,
            "last_updated": "runtime"  # Could track file modified time
        }
    
    return {
        "documents": stats,
        "total_size": sum(s["size"] for s in stats.values()),
        "loaded_count": sum(1 for s in stats.values() if s["loaded"])
    }