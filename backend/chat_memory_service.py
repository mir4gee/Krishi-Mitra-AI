import json
import datetime as dt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
import os
from contextlib import contextmanager

@dataclass
class ChatMessage:
    """Represents a single chat message"""
    session_id: str
    message_id: str
    timestamp: str
    user_prompt: str
    ai_response: str
    user_context: Dict
    query_type: str
    confidence_score: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ChatMemoryManager:
    """
    Manages chat history with both in-memory and persistent storage options
    """
    
    def __init__(self, use_database: bool = True, db_path: str = "chat_history.db"):
        self.use_database = use_database
        self.db_path = db_path
        
        # In-memory storage (always available as backup)
        self.memory_store: Dict[str, List[ChatMessage]] = {}
        
        if self.use_database:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        message_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_prompt TEXT NOT NULL,
                        ai_response TEXT NOT NULL,
                        user_context TEXT NOT NULL,
                        query_type TEXT,
                        confidence_score REAL DEFAULT 0.0,
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_session_id 
                    ON chat_history(session_id)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON chat_history(timestamp)
                ''')
                
                conn.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")
            self.use_database = False
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            print(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def save_chat(self, session_id: str, user_prompt: str, ai_response: str, 
                  user_context: Dict, query_type: str = "general", 
                  confidence_score: float = 0.0, metadata: Dict = None) -> str:
        """
        Save a chat interaction to memory/database
        Returns message_id
        """
        message_id = f"{session_id}_{int(dt.datetime.now().timestamp() * 1000)}"
        timestamp = dt.datetime.now().isoformat()
        
        chat_message = ChatMessage(
            session_id=session_id,
            message_id=message_id,
            timestamp=timestamp,
            user_prompt=user_prompt,
            ai_response=ai_response,
            user_context=user_context,
            query_type=query_type,
            confidence_score=confidence_score,
            metadata=metadata or {}
        )
        
        # Save to in-memory store
        if session_id not in self.memory_store:
            self.memory_store[session_id] = []
        self.memory_store[session_id].append(chat_message)
        
        # Save to database if enabled
        if self.use_database:
            try:
                with self.get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO chat_history 
                        (session_id, message_id, timestamp, user_prompt, ai_response, 
                         user_context, query_type, confidence_score, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_id, message_id, timestamp, user_prompt, ai_response,
                        json.dumps(user_context), query_type, confidence_score,
                        json.dumps(metadata or {})
                    ))
                    conn.commit()
            except Exception as e:
                print(f"Database save error: {e}")
        
        return message_id
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a specific session"""
        messages = []
        
        if self.use_database:
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.execute('''
                        SELECT * FROM chat_history 
                        WHERE session_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (session_id, limit))
                    
                    for row in cursor.fetchall():
                        messages.append(ChatMessage(
                            session_id=row['session_id'],
                            message_id=row['message_id'],
                            timestamp=row['timestamp'],
                            user_prompt=row['user_prompt'],
                            ai_response=row['ai_response'],
                            user_context=json.loads(row['user_context']),
                            query_type=row['query_type'],
                            confidence_score=row['confidence_score'],
                            metadata=json.loads(row['metadata'])
                        ))
                
                return messages[::-1]  # Return in chronological order
            except Exception as e:
                print(f"Database retrieval error: {e}")
        
        # Fallback to memory store
        if session_id in self.memory_store:
            return self.memory_store[session_id][-limit:]
        
        return []
    
    def get_recent_context(self, session_id: str, max_messages: int = 5) -> Dict:
        """
        Get recent conversation context for better AI responses
        """
        recent_messages = self.get_session_history(session_id, max_messages)
        
        if not recent_messages:
            return {"has_history": False, "context_summary": "No previous conversation"}
        
        # Analyze recent conversation patterns
        query_types = [msg.query_type for msg in recent_messages]
        crops_mentioned = []
        locations_mentioned = []
        
        for msg in recent_messages:
            ctx = msg.user_context
            if ctx.get('cropType'):
                crops_mentioned.append(ctx['cropType'])
            if ctx.get('farmerLocation'):
                locations_mentioned.append(ctx['farmerLocation'])
        
        # Get most recent user context
        latest_context = recent_messages[-1].user_context if recent_messages else {}
        
        return {
            "has_history": True,
            "message_count": len(recent_messages),
            "recent_queries": [msg.user_prompt for msg in recent_messages[-3:]],
            "recent_query_types": list(set(query_types)),
            "primary_crop": max(set(crops_mentioned), key=crops_mentioned.count) if crops_mentioned else None,
            "farmer_location": latest_context.get('farmerLocation'),
            "farmer_name": latest_context.get('name'),
            "conversation_themes": self._extract_themes(recent_messages),
            "last_interaction": recent_messages[-1].timestamp if recent_messages else None
        }
    
    def _extract_themes(self, messages: List[ChatMessage]) -> List[str]:
        """Extract conversation themes from recent messages"""
        themes = []
        all_text = " ".join([msg.user_prompt.lower() for msg in messages])
        
        theme_keywords = {
            "market_selling": ["sell", "market", "price", "mandi", "buyer"],
            "crop_care": ["irrigation", "fertilizer", "pest", "disease", "care"],
            "weather_concerns": ["weather", "rain", "drought", "temperature", "climate"],
            "financial_help": ["loan", "credit", "scheme", "subsidy", "money"],
            "storage_spoilage": ["storage", "spoil", "preserve", "warehouse"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def search_history(self, session_id: str, query: str, limit: int = 10) -> List[ChatMessage]:
        """Search through chat history"""
        messages = self.get_session_history(session_id, limit=100)  # Search more messages
        query_lower = query.lower()
        
        matching_messages = []
        for msg in messages:
            if (query_lower in msg.user_prompt.lower() or 
                query_lower in msg.ai_response.lower() or
                query_lower in msg.query_type.lower()):
                matching_messages.append(msg)
        
        return matching_messages[:limit]
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics about a chat session"""
        messages = self.get_session_history(session_id)
        
        if not messages:
            return {"total_messages": 0, "session_active": False}
        
        query_types = [msg.query_type for msg in messages]
        confidence_scores = [msg.confidence_score for msg in messages if msg.confidence_score > 0]
        
        return {
            "total_messages": len(messages),
            "session_active": True,
            "first_interaction": messages[0].timestamp,
            "last_interaction": messages[-1].timestamp,
            "query_type_distribution": {qt: query_types.count(qt) for qt in set(query_types)},
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "session_duration_hours": self._calculate_session_duration(messages)
        }
    
    def _calculate_session_duration(self, messages: List[ChatMessage]) -> float:
        """Calculate session duration in hours"""
        if len(messages) < 2:
            return 0
        
        try:
            start = dt.datetime.fromisoformat(messages[0].timestamp)
            end = dt.datetime.fromisoformat(messages[-1].timestamp)
            duration = (end - start).total_seconds() / 3600  # Convert to hours
            return round(duration, 2)
        except:
            return 0
    
    def delete_session(self, session_id: str) -> bool:
        """Delete all messages for a session"""
        try:
            if self.use_database:
                with self.get_db_connection() as conn:
                    conn.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
                    conn.commit()
            
            if session_id in self.memory_store:
                del self.memory_store[session_id]
            
            return True
        except Exception as e:
            print(f"Session deletion error: {e}")
            return False
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up sessions older than specified days"""
        cutoff_date = dt.datetime.now() - dt.timedelta(days=days_old)
        cutoff_str = cutoff_date.isoformat()
        
        deleted_count = 0
        try:
            if self.use_database:
                with self.get_db_connection() as conn:
                    cursor = conn.execute(
                        'DELETE FROM chat_history WHERE timestamp < ?', 
                        (cutoff_str,)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
            
            # Clean memory store
            sessions_to_delete = []
            for session_id, messages in self.memory_store.items():
                if messages and messages[-1].timestamp < cutoff_str:
                    sessions_to_delete.append(session_id)
            
            for session_id in sessions_to_delete:
                del self.memory_store[session_id]
                deleted_count += len(self.memory_store.get(session_id, []))
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        return deleted_count

# Global instance
chat_memory = ChatMemoryManager(use_database=True)