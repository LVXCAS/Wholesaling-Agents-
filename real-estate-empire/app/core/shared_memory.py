"""
Shared Memory and Persistence Layer for Agent System
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
from dataclasses import dataclass, asdict
import pickle
import os

from pydantic import BaseModel, Field
import redis
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .agent_state import AgentState, AgentType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory storage"""
    TRANSIENT = "transient"  # In-memory, lost on restart
    PERSISTENT = "persistent"  # Stored in database
    CACHED = "cached"  # Redis cache with TTL
    SHARED = "shared"  # Shared between agents


class MemoryScope(str, Enum):
    """Scope of memory access"""
    AGENT_PRIVATE = "agent_private"  # Only accessible by specific agent
    AGENT_SHARED = "agent_shared"  # Shared between agents of same type
    SYSTEM_WIDE = "system_wide"  # Accessible by all agents
    WORKFLOW = "workflow"  # Scoped to specific workflow


@dataclass
class MemoryItem:
    """Represents an item in memory"""
    key: str
    value: Any
    memory_type: MemoryType
    scope: MemoryScope
    owner: str  # Agent or system that owns this memory
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Database models for persistent memory
Base = declarative_base()


class PersistentMemory(Base):
    """Database model for persistent memory storage"""
    __tablename__ = "persistent_memory"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, nullable=False, index=True)
    value_json = Column(Text, nullable=False)
    memory_type = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    owner = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    metadata_json = Column(Text, default="{}")


class WorkflowMemory(Base):
    """Database model for workflow-scoped memory"""
    __tablename__ = "workflow_memory"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False)
    value_json = Column(Text, nullable=False)
    owner = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, nullable=True)


class AgentMemoryStats(Base):
    """Database model for agent memory usage statistics"""
    __tablename__ = "agent_memory_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String, nullable=False, index=True)
    agent_type = Column(String, nullable=False)
    memory_items_count = Column(Integer, default=0)
    total_memory_size = Column(Float, default=0.0)  # in MB
    last_cleanup = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SharedMemoryManager:
    """
    Manages shared memory and persistence for the agent system
    Provides multiple storage backends: in-memory, Redis, and database
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 database_url: str = "sqlite:///agent_memory.db"):
        self.redis_url = redis_url
        self.database_url = database_url
        
        # In-memory storage
        self.transient_memory: Dict[str, MemoryItem] = {}
        
        # Redis client for cached memory
        self.redis_client: Optional[redis.Redis] = None
        
        # Database for persistent memory
        self.engine = None
        self.SessionLocal = None
        
        # Memory access locks
        self.memory_locks: Dict[str, asyncio.Lock] = {}
        
        # Statistics
        self.access_stats: Dict[str, int] = {}
        self.cleanup_stats: Dict[str, datetime] = {}
    
    async def initialize(self):
        """Initialize all memory backends"""
        try:
            # Initialize Redis
            await self._initialize_redis()
            
            # Initialize Database
            self._initialize_database()
            
            # Start cleanup tasks
            asyncio.create_task(self._periodic_cleanup())
            
            logger.info("Shared memory manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize shared memory manager: {e}")
            raise e
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self.redis_client = None
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(self.database_url)
            Base.metadata.create_all(bind=self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise e
    
    def _get_memory_key(self, key: str, scope: MemoryScope, owner: str) -> str:
        """Generate a unique memory key based on scope and owner"""
        if scope == MemoryScope.AGENT_PRIVATE:
            return f"agent:{owner}:{key}"
        elif scope == MemoryScope.AGENT_SHARED:
            # Extract agent type from owner
            agent_type = owner.split("_")[0] if "_" in owner else owner
            return f"agent_type:{agent_type}:{key}"
        elif scope == MemoryScope.SYSTEM_WIDE:
            return f"system:{key}"
        elif scope == MemoryScope.WORKFLOW:
            return f"workflow:{owner}:{key}"
        else:
            return f"unknown:{owner}:{key}"
    
    async def store(self, 
                   key: str, 
                   value: Any, 
                   memory_type: MemoryType,
                   scope: MemoryScope,
                   owner: str,
                   ttl: Optional[int] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a value in memory
        
        Args:
            key: Memory key
            value: Value to store
            memory_type: Type of memory storage
            scope: Access scope
            owner: Owner of the memory item
            ttl: Time to live in seconds
            metadata: Additional metadata
            
        Returns:
            True if stored successfully
        """
        try:
            memory_key = self._get_memory_key(key, scope, owner)
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
            
            memory_item = MemoryItem(
                key=memory_key,
                value=value,
                memory_type=memory_type,
                scope=scope,
                owner=owner,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Store based on memory type
            if memory_type == MemoryType.TRANSIENT:
                await self._store_transient(memory_item)
            elif memory_type == MemoryType.CACHED:
                await self._store_cached(memory_item, ttl)
            elif memory_type == MemoryType.PERSISTENT:
                await self._store_persistent(memory_item)
            elif memory_type == MemoryType.SHARED:
                # Store in both cache and persistent for shared memory
                await self._store_cached(memory_item, ttl)
                await self._store_persistent(memory_item)
            
            # Update statistics
            self.access_stats[owner] = self.access_stats.get(owner, 0) + 1
            
            logger.debug(f"Stored memory item: {memory_key} for {owner}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory item {key}: {e}")
            return False
    
    async def retrieve(self, 
                      key: str, 
                      scope: MemoryScope, 
                      owner: str,
                      memory_type: Optional[MemoryType] = None) -> Optional[Any]:
        """
        Retrieve a value from memory
        
        Args:
            key: Memory key
            scope: Access scope
            owner: Owner of the memory item
            memory_type: Specific memory type to search (optional)
            
        Returns:
            Retrieved value or None if not found
        """
        try:
            memory_key = self._get_memory_key(key, scope, owner)
            
            # Try different memory types in order of speed
            if not memory_type or memory_type == MemoryType.TRANSIENT:
                value = await self._retrieve_transient(memory_key)
                if value is not None:
                    return value
            
            if not memory_type or memory_type == MemoryType.CACHED:
                value = await self._retrieve_cached(memory_key)
                if value is not None:
                    return value
            
            if not memory_type or memory_type in [MemoryType.PERSISTENT, MemoryType.SHARED]:
                value = await self._retrieve_persistent(memory_key, owner)
                if value is not None:
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory item {key}: {e}")
            return None
    
    async def delete(self, key: str, scope: MemoryScope, owner: str) -> bool:
        """Delete a memory item"""
        try:
            memory_key = self._get_memory_key(key, scope, owner)
            
            # Delete from all storage types
            await self._delete_transient(memory_key)
            await self._delete_cached(memory_key)
            await self._delete_persistent(memory_key, owner)
            
            logger.debug(f"Deleted memory item: {memory_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory item {key}: {e}")
            return False
    
    async def list_keys(self, scope: MemoryScope, owner: str, pattern: str = "*") -> List[str]:
        """List all keys for a given scope and owner"""
        try:
            keys = []
            
            # Get keys from transient memory
            prefix = self._get_memory_key("", scope, owner)
            for key in self.transient_memory.keys():
                if key.startswith(prefix):
                    keys.append(key.replace(prefix, ""))
            
            # Get keys from Redis
            if self.redis_client:
                redis_pattern = f"{prefix}*"
                redis_keys = await asyncio.to_thread(self.redis_client.keys, redis_pattern)
                for key in redis_keys:
                    clean_key = key.replace(prefix, "")
                    if clean_key not in keys:
                        keys.append(clean_key)
            
            # Get keys from database
            with self.SessionLocal() as db:
                db_items = db.query(PersistentMemory).filter(
                    PersistentMemory.owner == owner,
                    PersistentMemory.scope == scope.value
                ).all()
                
                for item in db_items:
                    clean_key = item.key.replace(prefix, "")
                    if clean_key not in keys:
                        keys.append(clean_key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list keys for {owner}: {e}")
            return []
    
    # Storage backend implementations
    
    async def _store_transient(self, memory_item: MemoryItem):
        """Store in transient (in-memory) storage"""
        self.transient_memory[memory_item.key] = memory_item
    
    async def _store_cached(self, memory_item: MemoryItem, ttl: Optional[int]):
        """Store in Redis cache"""
        if not self.redis_client:
            # Fallback to transient storage
            await self._store_transient(memory_item)
            return
        
        try:
            serialized_value = json.dumps({
                "value": memory_item.value,
                "metadata": memory_item.metadata,
                "created_at": memory_item.created_at.isoformat(),
                "owner": memory_item.owner
            })
            
            if ttl:
                await asyncio.to_thread(
                    self.redis_client.setex, 
                    memory_item.key, 
                    ttl, 
                    serialized_value
                )
            else:
                await asyncio.to_thread(
                    self.redis_client.set, 
                    memory_item.key, 
                    serialized_value
                )
                
        except Exception as e:
            logger.error(f"Failed to store in Redis cache: {e}")
            # Fallback to transient storage
            await self._store_transient(memory_item)
    
    async def _store_persistent(self, memory_item: MemoryItem):
        """Store in database"""
        try:
            with self.SessionLocal() as db:
                # Check if item already exists
                existing = db.query(PersistentMemory).filter(
                    PersistentMemory.key == memory_item.key,
                    PersistentMemory.owner == memory_item.owner
                ).first()
                
                if existing:
                    # Update existing item
                    existing.value_json = json.dumps(memory_item.value)
                    existing.updated_at = memory_item.updated_at
                    existing.expires_at = memory_item.expires_at
                    existing.metadata_json = json.dumps(memory_item.metadata)
                    existing.access_count += 1
                else:
                    # Create new item
                    db_item = PersistentMemory(
                        key=memory_item.key,
                        value_json=json.dumps(memory_item.value),
                        memory_type=memory_item.memory_type.value,
                        scope=memory_item.scope.value,
                        owner=memory_item.owner,
                        created_at=memory_item.created_at,
                        updated_at=memory_item.updated_at,
                        expires_at=memory_item.expires_at,
                        metadata_json=json.dumps(memory_item.metadata)
                    )
                    db.add(db_item)
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store in database: {e}")
    
    async def _retrieve_transient(self, memory_key: str) -> Optional[Any]:
        """Retrieve from transient storage"""
        memory_item = self.transient_memory.get(memory_key)
        if memory_item:
            # Check expiration
            if memory_item.expires_at and datetime.now() > memory_item.expires_at:
                del self.transient_memory[memory_key]
                return None
            
            memory_item.access_count += 1
            return memory_item.value
        return None
    
    async def _retrieve_cached(self, memory_key: str) -> Optional[Any]:
        """Retrieve from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await asyncio.to_thread(self.redis_client.get, memory_key)
            if cached_data:
                data = json.loads(cached_data)
                return data["value"]
        except Exception as e:
            logger.error(f"Failed to retrieve from Redis cache: {e}")
        
        return None
    
    async def _retrieve_persistent(self, memory_key: str, owner: str) -> Optional[Any]:
        """Retrieve from database"""
        try:
            with self.SessionLocal() as db:
                db_item = db.query(PersistentMemory).filter(
                    PersistentMemory.key == memory_key,
                    PersistentMemory.owner == owner
                ).first()
                
                if db_item:
                    # Check expiration
                    if db_item.expires_at and datetime.now() > db_item.expires_at:
                        db.delete(db_item)
                        db.commit()
                        return None
                    
                    # Update access count
                    db_item.access_count += 1
                    db.commit()
                    
                    return json.loads(db_item.value_json)
                    
        except Exception as e:
            logger.error(f"Failed to retrieve from database: {e}")
        
        return None
    
    async def _delete_transient(self, memory_key: str):
        """Delete from transient storage"""
        if memory_key in self.transient_memory:
            del self.transient_memory[memory_key]
    
    async def _delete_cached(self, memory_key: str):
        """Delete from Redis cache"""
        if self.redis_client:
            try:
                await asyncio.to_thread(self.redis_client.delete, memory_key)
            except Exception as e:
                logger.error(f"Failed to delete from Redis cache: {e}")
    
    async def _delete_persistent(self, memory_key: str, owner: str):
        """Delete from database"""
        try:
            with self.SessionLocal() as db:
                db_item = db.query(PersistentMemory).filter(
                    PersistentMemory.key == memory_key,
                    PersistentMemory.owner == owner
                ).first()
                
                if db_item:
                    db.delete(db_item)
                    db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to delete from database: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired memory items"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_expired_items()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _cleanup_expired_items(self):
        """Clean up expired memory items"""
        now = datetime.now()
        
        # Clean up transient memory
        expired_keys = []
        for key, item in self.transient_memory.items():
            if item.expires_at and now > item.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.transient_memory[key]
        
        # Clean up database
        try:
            with self.SessionLocal() as db:
                expired_items = db.query(PersistentMemory).filter(
                    PersistentMemory.expires_at.isnot(None),
                    PersistentMemory.expires_at < now
                ).all()
                
                for item in expired_items:
                    db.delete(item)
                
                db.commit()
                
                if expired_keys or expired_items:
                    logger.info(f"Cleaned up {len(expired_keys)} transient and {len(expired_items)} persistent expired items")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup database: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            "transient_items": len(self.transient_memory),
            "redis_available": self.redis_client is not None,
            "database_available": self.engine is not None,
            "access_stats": self.access_stats.copy(),
            "cleanup_stats": self.cleanup_stats.copy()
        }
        
        # Get database stats
        if self.SessionLocal:
            try:
                with self.SessionLocal() as db:
                    persistent_count = db.query(PersistentMemory).count()
                    workflow_count = db.query(WorkflowMemory).count()
                    
                    stats["persistent_items"] = persistent_count
                    stats["workflow_items"] = workflow_count
                    
            except Exception as e:
                logger.error(f"Failed to get database stats: {e}")
        
        return stats


# Global shared memory manager
shared_memory_manager = SharedMemoryManager()