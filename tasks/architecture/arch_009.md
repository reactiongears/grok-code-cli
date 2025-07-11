# Architecture: Task 009 - Implement Conversation Management System

## Overview
This task implements a comprehensive conversation management system that provides persistence, history search, context optimization, multi-session support, and analytics for enhanced user experience.

## Technical Scope

### Files to Modify
- `grok/conversation.py` - New conversation management system
- `grok/conversation_storage.py` - New conversation storage backend
- `grok/conversation_analytics.py` - New analytics system
- `grok/agent.py` - Integrate conversation management

### Dependencies
- Task 008 (Plugin Architecture) - Required for extensible conversation features
- Task 007 (Configuration) - Required for conversation settings
- Task 006 (Error Handling) - Required for robust error management

## Implementation Details

### Phase 1: Conversation Storage Backend

#### Create `grok/conversation_storage.py`
```python
"""
Conversation storage backend for Grok CLI
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid

@dataclass
class Message:
    """Individual message in a conversation"""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float
    metadata: Dict[str, Any]
    tokens: Optional[int] = None

@dataclass
class Conversation:
    """Conversation data structure"""
    id: str
    title: str
    created_at: float
    updated_at: float
    messages: List[Message]
    metadata: Dict[str, Any]
    context_size: int = 0
    total_tokens: int = 0

class ConversationStorage:
    """Conversation storage backend using SQLite"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / '.grok' / 'conversations.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT,
                    context_size INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    tokens INTEGER,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages(conversation_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            """)
            
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content, conversation_id, role
                )
            """)
    
    def create_conversation(self, title: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, title, current_time, current_time, 
                  json.dumps(metadata or {})))
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        with sqlite3.connect(self.db_path) as conn:
            # Get conversation metadata
            cursor = conn.execute("""
                SELECT id, title, created_at, updated_at, metadata, context_size, total_tokens
                FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Get messages
            cursor = conn.execute("""
                SELECT id, role, content, timestamp, metadata, tokens
                FROM messages WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """, (conversation_id,))
            
            messages = []
            for msg_row in cursor.fetchall():
                message = Message(
                    id=msg_row[0],
                    role=msg_row[1],
                    content=msg_row[2],
                    timestamp=msg_row[3],
                    metadata=json.loads(msg_row[4] or '{}'),
                    tokens=msg_row[5]
                )
                messages.append(message)
            
            return Conversation(
                id=row[0],
                title=row[1],
                created_at=row[2],
                updated_at=row[3],
                messages=messages,
                metadata=json.loads(row[4] or '{}'),
                context_size=row[5],
                total_tokens=row[6]
            )
    
    def save_message(self, conversation_id: str, role: str, content: str, 
                    metadata: Dict[str, Any] = None, tokens: Optional[int] = None) -> str:
        """Save a message to a conversation"""
        message_id = str(uuid.uuid4())
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert message
            conn.execute("""
                INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata, tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message_id, conversation_id, role, content, current_time, 
                  json.dumps(metadata or {}), tokens))
            
            # Update conversation timestamp
            conn.execute("""
                UPDATE conversations SET updated_at = ? WHERE id = ?
            """, (current_time, conversation_id))
            
            # Update FTS index
            conn.execute("""
                INSERT INTO messages_fts (content, conversation_id, role)
                VALUES (?, ?, ?)
            """, (content, conversation_id, role))
        
        return message_id
    
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations with pagination"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, created_at, updated_at, 
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'id': row[0],
                    'title': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'message_count': row[4]
                })
            
            return conversations
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at,
                       snippet(messages_fts, 0, '<mark>', '</mark>', '...', 32) as snippet
                FROM conversations c
                JOIN messages_fts ON c.id = messages_fts.conversation_id
                WHERE messages_fts MATCH ?
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'snippet': row[4]
                })
            
            return results
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        with sqlite3.connect(self.db_path) as conn:
            # Delete messages
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM messages_fts WHERE conversation_id = ?", (conversation_id,))
            
            # Delete conversation
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            
            return cursor.rowcount > 0
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_conversations,
                    SUM(total_tokens) as total_tokens,
                    AVG(context_size) as avg_context_size,
                    (SELECT COUNT(*) FROM messages) as total_messages
                FROM conversations
            """)
            
            row = cursor.fetchone()
            return {
                'total_conversations': row[0],
                'total_tokens': row[1] or 0,
                'avg_context_size': row[2] or 0,
                'total_messages': row[3]
            }
    
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up conversations older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get conversation IDs to delete
            cursor = conn.execute("""
                SELECT id FROM conversations WHERE updated_at < ?
            """, (cutoff_time,))
            
            conversation_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete messages and conversations
            for conv_id in conversation_ids:
                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
                conn.execute("DELETE FROM messages_fts WHERE conversation_id = ?", (conv_id,))
            
            cursor = conn.execute("DELETE FROM conversations WHERE updated_at < ?", (cutoff_time,))
            
            return cursor.rowcount
```

### Phase 2: Conversation Manager

#### Create `grok/conversation.py`
```python
"""
Conversation management system for Grok CLI
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import tiktoken

from .conversation_storage import ConversationStorage, Conversation, Message
from .error_handling import ErrorHandler, ErrorCategory
from .config import ConfigManager

class ContextOptimizer:
    """Context optimization for managing conversation size"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def optimize_context(self, messages: List[Message]) -> List[Message]:
        """Optimize conversation context to fit within token limits"""
        if not messages:
            return messages
        
        # Calculate total tokens
        total_tokens = sum(self.count_tokens(msg.content) for msg in messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Keep system messages and recent messages
        system_messages = [msg for msg in messages if msg.role == 'system']
        other_messages = [msg for msg in messages if msg.role != 'system']
        
        # Sort by timestamp (most recent first)
        other_messages.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Add messages until we hit the limit
        optimized_messages = system_messages.copy()
        current_tokens = sum(self.count_tokens(msg.content) for msg in system_messages)
        
        for msg in other_messages:
            msg_tokens = self.count_tokens(msg.content)
            if current_tokens + msg_tokens <= self.max_tokens:
                optimized_messages.append(msg)
                current_tokens += msg_tokens
            else:
                break
        
        # Sort by timestamp (chronological order)
        optimized_messages.sort(key=lambda x: x.timestamp)
        
        return optimized_messages
    
    def summarize_old_messages(self, messages: List[Message]) -> str:
        """Create a summary of old messages"""
        if not messages:
            return ""
        
        # Simple summarization - in practice, you'd use an LLM for this
        user_messages = [msg for msg in messages if msg.role == 'user']
        assistant_messages = [msg for msg in messages if msg.role == 'assistant']
        
        summary = f"Previous conversation summary:\n"
        summary += f"- User asked {len(user_messages)} questions\n"
        summary += f"- Assistant provided {len(assistant_messages)} responses\n"
        
        # Include key topics (simple keyword extraction)
        all_content = " ".join(msg.content for msg in messages)
        # This is a simplified approach - real implementation would use NLP
        
        return summary

class ConversationManager:
    """Main conversation management system"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.storage = ConversationStorage()
        self.error_handler = ErrorHandler()
        self.context_optimizer = ContextOptimizer()
        
        # Current conversation state
        self.current_conversation_id: Optional[str] = None
        self.current_conversation: Optional[Conversation] = None
        
        # Load configuration
        self.config = config_manager.load_settings()
        self.max_context_tokens = self.config.get('conversation', {}).get('max_context_tokens', 4000)
        self.auto_save = self.config.get('conversation', {}).get('auto_save', True)
    
    def start_conversation(self, title: str = None, metadata: Dict[str, Any] = None) -> str:
        """Start a new conversation"""
        try:
            if not title:
                title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            conversation_id = self.storage.create_conversation(title, metadata)
            self.current_conversation_id = conversation_id
            self.current_conversation = self.storage.get_conversation(conversation_id)
            
            return conversation_id
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "start_conversation"}
            )
            return None
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Load an existing conversation"""
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if conversation:
                self.current_conversation_id = conversation_id
                self.current_conversation = conversation
                return True
            return False
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "load_conversation", "id": conversation_id}
            )
            return False
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a message to the current conversation"""
        try:
            if not self.current_conversation_id:
                # Auto-start conversation if none exists
                self.start_conversation()
            
            # Count tokens
            tokens = self.context_optimizer.count_tokens(content)
            
            # Save message
            message_id = self.storage.save_message(
                self.current_conversation_id, role, content, metadata, tokens
            )
            
            # Update current conversation
            if self.current_conversation:
                message = Message(
                    id=message_id,
                    role=role,
                    content=content,
                    timestamp=time.time(),
                    metadata=metadata or {},
                    tokens=tokens
                )
                self.current_conversation.messages.append(message)
                self.current_conversation.total_tokens += tokens
            
            return message_id
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "add_message"}
            )
            return None
    
    def get_context_messages(self, optimize: bool = True) -> List[Message]:
        """Get messages for context, optionally optimized"""
        if not self.current_conversation:
            return []
        
        messages = self.current_conversation.messages
        
        if optimize:
            messages = self.context_optimizer.optimize_context(messages)
        
        return messages
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations"""
        try:
            return self.storage.search_conversations(query, limit)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "search_conversations"}
            )
            return []
    
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations"""
        try:
            return self.storage.list_conversations(limit, offset)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "list_conversations"}
            )
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            success = self.storage.delete_conversation(conversation_id)
            
            # If current conversation was deleted, reset
            if conversation_id == self.current_conversation_id:
                self.current_conversation_id = None
                self.current_conversation = None
            
            return success
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "delete_conversation"}
            )
            return False
    
    def export_conversation(self, conversation_id: str, format: str = 'json') -> Optional[str]:
        """Export conversation to various formats"""
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if not conversation:
                return None
            
            if format == 'json':
                return json.dumps(asdict(conversation), indent=2)
            elif format == 'markdown':
                return self._format_as_markdown(conversation)
            elif format == 'text':
                return self._format_as_text(conversation)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "export_conversation"}
            )
            return None
    
    def _format_as_markdown(self, conversation: Conversation) -> str:
        """Format conversation as Markdown"""
        md = f"# {conversation.title}\n\n"
        md += f"**Created:** {datetime.fromtimestamp(conversation.created_at)}\n"
        md += f"**Updated:** {datetime.fromtimestamp(conversation.updated_at)}\n\n"
        
        for message in conversation.messages:
            role_title = message.role.title()
            timestamp = datetime.fromtimestamp(message.timestamp)
            md += f"## {role_title} ({timestamp})\n\n"
            md += f"{message.content}\n\n"
        
        return md
    
    def _format_as_text(self, conversation: Conversation) -> str:
        """Format conversation as plain text"""
        text = f"{conversation.title}\n"
        text += "=" * len(conversation.title) + "\n\n"
        
        for message in conversation.messages:
            timestamp = datetime.fromtimestamp(message.timestamp)
            text += f"[{timestamp}] {message.role.upper()}:\n"
            text += f"{message.content}\n\n"
        
        return text
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            stats = self.storage.get_conversation_stats()
            
            # Add current conversation stats
            if self.current_conversation:
                stats['current_conversation'] = {
                    'id': self.current_conversation.id,
                    'title': self.current_conversation.title,
                    'message_count': len(self.current_conversation.messages),
                    'total_tokens': self.current_conversation.total_tokens
                }
            
            return stats
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "get_conversation_stats"}
            )
            return {}
    
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up old conversations"""
        try:
            return self.storage.cleanup_old_conversations(days)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "cleanup_old_conversations"}
            )
            return 0
```

### Phase 3: Integration with Agent

#### Update `grok/agent.py` to use conversation management
```python
# Add conversation management to agent
from .conversation import ConversationManager

class EnhancedAgent:
    def __init__(self, config_manager):
        self.conversation_manager = ConversationManager(config_manager)
        # ... existing initialization
    
    def agent_loop(self, initial_prompt=None):
        # Start or continue conversation
        if not self.conversation_manager.current_conversation_id:
            self.conversation_manager.start_conversation()
        
        # Add initial prompt if provided
        if initial_prompt:
            self.conversation_manager.add_message('user', initial_prompt)
        
        # Main conversation loop
        while True:
            if not self.conversation_manager.current_conversation or \
               self.conversation_manager.current_conversation.messages[-1].role == 'assistant':
                
                user_input = session.prompt('> ')
                
                # Handle slash commands
                if user_input.startswith('/'):
                    self.handle_conversation_commands(user_input)
                    continue
                
                # Add user message
                self.conversation_manager.add_message('user', user_input)
            
            # Get optimized context
            context_messages = self.conversation_manager.get_context_messages()
            
            # Convert to API format
            api_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in context_messages
            ]
            
            # Make API call
            response = call_api(api_messages, tools=TOOLS)
            message = response.choices[0].message
            
            if message.content:
                print(message.content)
                # Add assistant message
                self.conversation_manager.add_message('assistant', message.content)
            
            # Handle tool calls
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_result = handle_tool_call(tc, mode, permissions)
                    # Add tool result as system message
                    self.conversation_manager.add_message('system', json.dumps(tool_result))
    
    def handle_conversation_commands(self, command: str):
        """Handle conversation-specific slash commands"""
        parts = command.split()
        cmd = parts[0][1:].lower()
        
        if cmd == 'conversations':
            conversations = self.conversation_manager.list_conversations()
            for conv in conversations:
                print(f"{conv['id']}: {conv['title']} ({conv['message_count']} messages)")
        
        elif cmd == 'load':
            if len(parts) > 1:
                conv_id = parts[1]
                if self.conversation_manager.load_conversation(conv_id):
                    print(f"Loaded conversation: {conv_id}")
                else:
                    print(f"Failed to load conversation: {conv_id}")
        
        elif cmd == 'search':
            if len(parts) > 1:
                query = ' '.join(parts[1:])
                results = self.conversation_manager.search_conversations(query)
                for result in results:
                    print(f"{result['id']}: {result['title']}")
                    print(f"  {result['snippet']}")
        
        elif cmd == 'export':
            if len(parts) > 1:
                conv_id = parts[1]
                format_type = parts[2] if len(parts) > 2 else 'json'
                exported = self.conversation_manager.export_conversation(conv_id, format_type)
                if exported:
                    filename = f"conversation_{conv_id}.{format_type}"
                    with open(filename, 'w') as f:
                        f.write(exported)
                    print(f"Exported conversation to {filename}")
        
        elif cmd == 'stats':
            stats = self.conversation_manager.get_conversation_stats()
            print(f"Total conversations: {stats['total_conversations']}")
            print(f"Total messages: {stats['total_messages']}")
            print(f"Total tokens: {stats['total_tokens']}")
```

## Implementation Steps for Claude Code

### Step 1: Create Conversation Storage Backend
```
Task: Create robust conversation storage system

Instructions:
1. Create grok/conversation_storage.py with SQLite backend
2. Implement conversation and message data structures
3. Add full-text search capabilities
4. Create database schema and indexing
5. Test storage operations and search functionality
```

### Step 2: Implement Conversation Manager
```
Task: Create comprehensive conversation management system

Instructions:
1. Create grok/conversation.py with ConversationManager class
2. Implement context optimization for token management
3. Add conversation lifecycle management
4. Create export/import functionality
5. Test conversation management operations
```

### Step 3: Integrate with Agent System
```
Task: Integrate conversation management with existing agent

Instructions:
1. Update grok/agent.py to use conversation management
2. Add conversation-specific slash commands
3. Implement context-aware API calls
4. Add conversation persistence throughout sessions
5. Test integrated conversation experience
```

### Step 4: Add Conversation Analytics
```
Task: Implement conversation analytics and insights

Instructions:
1. Create grok/conversation_analytics.py
2. Add usage tracking and metrics
3. Implement conversation insights and patterns
4. Add analytics reporting functionality
5. Test analytics data collection and reporting
```

## Testing Strategy

### Unit Tests
- Storage operations (CRUD)
- Context optimization algorithms
- Search functionality
- Export/import operations

### Integration Tests
- Conversation lifecycle management
- Multi-session handling
- Agent integration
- Performance with large conversations

### Performance Tests
- Database query optimization
- Memory usage with large conversations
- Search performance
- Context optimization efficiency

## Success Metrics
- Reliable conversation persistence
- Efficient context optimization
- Fast search capabilities
- Seamless multi-session support
- Comprehensive analytics

## Next Steps
After completion of this task:
1. Enhanced user experience with conversation history
2. Better context management for long conversations
3. Foundation for advanced conversation features