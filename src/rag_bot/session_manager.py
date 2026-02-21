"""
In-memory session manager for conversation history and analytics.
"""

import time
import uuid
from typing import Dict, List, Optional
from collections import defaultdict


class SessionManager:
    """Manages conversation sessions and query analytics."""

    def __init__(self):
        # session_id -> list of messages [{role, content}]
        self._sessions: Dict[str, List[Dict]] = {}
        # session_id -> creation timestamp
        self._session_created: Dict[str, float] = {}
        # Analytics tracking
        self._query_count: int = 0
        self._recent_queries: List[Dict] = []
        self._topic_counts: Dict[str, int] = defaultdict(int)
        self._response_times: List[float] = []

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        self._session_created[session_id] = time.time()
        return session_id

    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._session_created[session_id] = time.time()
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._session_created[session_id] = time.time()
        self._sessions[session_id].append({"role": role, "content": content})
        # Keep history manageable (last 20 messages)
        if len(self._sessions[session_id]) > 20:
            self._sessions[session_id] = self._sessions[session_id][-20:]

    def delete_session(self, session_id: str):
        """Delete a session."""
        self._sessions.pop(session_id, None)
        self._session_created.pop(session_id, None)

    def track_query(self, question: str, response_time: float):
        """Track a query for analytics."""
        self._query_count += 1
        self._response_times.append(response_time)
        self._recent_queries.append({
            "question": question,
            "timestamp": time.time(),
            "response_time": response_time,
        })
        # Keep only last 100 queries
        if len(self._recent_queries) > 100:
            self._recent_queries = self._recent_queries[-100:]
        # Track topics (simple keyword extraction)
        for word in question.lower().split():
            if len(word) > 3 and word.isalpha():
                self._topic_counts[word] += 1

    def get_analytics(self) -> Dict:
        """Return analytics data."""
        avg_time = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times
            else 0
        )
        # Get top topics
        sorted_topics = sorted(
            self._topic_counts.items(), key=lambda x: x[1], reverse=True
        )[:20]
        return {
            "total_queries": self._query_count,
            "active_sessions": len(self._sessions),
            "avg_response_time": round(avg_time, 3),
            "popular_topics": [
                {"topic": t, "count": c} for t, c in sorted_topics
            ],
            "recent_queries": self._recent_queries[-10:],
        }


# Global singleton
session_manager = SessionManager()
