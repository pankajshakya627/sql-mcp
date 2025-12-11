"""
Session storage for paginated query results.
Stores query results temporarily so users can paginate through large datasets.
"""
import time
import threading
import uuid
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("db-agent-mcp.session")


class QuerySession:
    """Stores a single query result for pagination."""
    
    def __init__(self, query: str, results: List[Dict], page_size: int = 20):
        self.session_id = str(uuid.uuid4())[:8]
        self.query = query
        self.results = results
        self.total_rows = len(results)
        self.page_size = page_size
        self.current_page = 1
        self.created_at = time.time()
        self.last_accessed = time.time()
        
    @property
    def total_pages(self) -> int:
        return (self.total_rows + self.page_size - 1) // self.page_size
    
    def get_page(self, page: int = None) -> Dict[str, Any]:
        """Get a specific page of results."""
        if page is not None:
            self.current_page = max(1, min(page, self.total_pages))
        
        self.last_accessed = time.time()
        
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.results[start_idx:end_idx]
        
        return {
            "session_id": self.session_id,
            "page": self.current_page,
            "total_pages": self.total_pages,
            "total_rows": self.total_rows,
            "page_size": self.page_size,
            "showing": f"{start_idx + 1}-{min(end_idx, self.total_rows)}",
            "data": page_data,
            "has_next": self.current_page < self.total_pages,
            "has_prev": self.current_page > 1
        }
    
    def next_page(self) -> Dict[str, Any]:
        """Get next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
        return self.get_page()
    
    def prev_page(self) -> Dict[str, Any]:
        """Get previous page."""
        if self.current_page > 1:
            self.current_page -= 1
        return self.get_page()


class SessionStore:
    """Global session store for all active query sessions."""
    
    # Session timeout in seconds (5 minutes)
    SESSION_TIMEOUT = 300
    
    def __init__(self):
        self._sessions: Dict[str, QuerySession] = {}
        self._lock = threading.Lock()
        self._cleanup_running = False
        
    def create_session(self, query: str, results: List[Dict], page_size: int = 20) -> QuerySession:
        """Create a new query session."""
        session = QuerySession(query, results, page_size)
        
        with self._lock:
            self._sessions[session.session_id] = session
            logger.info(f"📦 Session created: {session.session_id} ({session.total_rows} rows)")
        
        # Start cleanup if not running
        self._start_cleanup()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[QuerySession]:
        """Get a session by ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_accessed = time.time()
                logger.debug(f"📦 Session accessed: {session_id}")
            return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a specific session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"🗑️ Session deleted: {session_id}")
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        current_time = time.time()
        expired = []
        
        with self._lock:
            for sid, session in self._sessions.items():
                if current_time - session.last_accessed > self.SESSION_TIMEOUT:
                    expired.append(sid)
            
            for sid in expired:
                del self._sessions[sid]
                logger.info(f"🗑️ Session expired: {sid}")
        
        return len(expired)
    
    def _start_cleanup(self):
        """Start background cleanup thread."""
        if self._cleanup_running:
            return
        
        def cleanup_loop():
            self._cleanup_running = True
            while True:
                time.sleep(60)  # Check every minute
                count = self.cleanup_expired()
                if count > 0:
                    logger.info(f"🧹 Cleaned up {count} expired sessions")
                
                # Stop if no sessions left
                with self._lock:
                    if not self._sessions:
                        self._cleanup_running = False
                        break
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    @property
    def active_sessions(self) -> int:
        """Get count of active sessions."""
        return len(self._sessions)
    
    def list_sessions(self) -> List[Dict]:
        """List all active sessions."""
        with self._lock:
            return [
                {
                    "session_id": s.session_id,
                    "query": s.query[:50] + "..." if len(s.query) > 50 else s.query,
                    "total_rows": s.total_rows,
                    "current_page": s.current_page,
                    "age_seconds": int(time.time() - s.created_at)
                }
                for s in self._sessions.values()
            ]


# Global session store instance
session_store = SessionStore()
