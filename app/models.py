from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class AIOperationType(str, Enum):
    """Types of AI operations that can be performed."""

    SUMMARIZE = "summarize"
    GENERATE_IDEAS = "generate_ideas"
    SUGGEST_CONNECTIONS = "suggest_connections"
    ANSWER_QUESTION = "answer_question"


class NoteStatus(str, Enum):
    """Status of a note."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# Association table for many-to-many relationship between notes and tags
class NoteTag(SQLModel, table=True):
    """Association table for notes and tags."""

    __tablename__ = "note_tags"  # type: ignore[assignment]

    note_id: int = Field(foreign_key="notes.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


# Persistent models (stored in database)
class Folder(SQLModel, table=True):
    """Hierarchical folder structure for organizing notes."""

    __tablename__ = "folders"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    parent_id: Optional[int] = Field(default=None, foreign_key="folders.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    parent: Optional["Folder"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Folder.id"}
    )
    children: List["Folder"] = Relationship(back_populates="parent")
    notes: List["Note"] = Relationship(back_populates="folder")


class Tag(SQLModel, table=True):
    """Tags for categorizing and organizing notes."""

    __tablename__ = "tags"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    color: Optional[str] = Field(default="#6366f1", max_length=7)  # Hex color code
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Many-to-many relationship with notes
    notes: List["Note"] = Relationship(back_populates="tags", link_model=NoteTag)


class Note(SQLModel, table=True):
    """Core note entity with rich text content and metadata."""

    __tablename__ = "notes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    content: str = Field(default="")  # Rich text content stored as HTML/Markdown
    content_plain: str = Field(default="")  # Plain text version for search
    folder_id: Optional[int] = Field(default=None, foreign_key="folders.id")
    status: NoteStatus = Field(default=NoteStatus.ACTIVE)
    is_favorite: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Search and indexing
    search_vector: Optional[str] = Field(default=None)  # For full-text search
    word_count: int = Field(default=0)

    # Metadata for AI features
    note_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    folder: Optional[Folder] = Relationship(back_populates="notes")
    tags: List[Tag] = Relationship(back_populates="notes", link_model=NoteTag)
    ai_operations: List["AIOperation"] = Relationship(back_populates="note")
    connections_from: List["NoteConnection"] = Relationship(
        back_populates="source_note", sa_relationship_kwargs={"foreign_keys": "NoteConnection.source_note_id"}
    )
    connections_to: List["NoteConnection"] = Relationship(
        back_populates="target_note", sa_relationship_kwargs={"foreign_keys": "NoteConnection.target_note_id"}
    )


class NoteConnection(SQLModel, table=True):
    """Represents connections/relationships between notes."""

    __tablename__ = "note_connections"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    source_note_id: int = Field(foreign_key="notes.id")
    target_note_id: int = Field(foreign_key="notes.id")
    connection_type: str = Field(max_length=100, default="related")  # e.g., "related", "references", "expands_on"
    strength: float = Field(default=1.0, ge=0.0, le=1.0)  # Connection strength (0-1)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_ai: bool = Field(default=False)  # Whether connection was suggested by AI

    # Relationships
    source_note: Note = Relationship(
        back_populates="connections_from", sa_relationship_kwargs={"foreign_keys": "NoteConnection.source_note_id"}
    )
    target_note: Note = Relationship(
        back_populates="connections_to", sa_relationship_kwargs={"foreign_keys": "NoteConnection.target_note_id"}
    )


class AIOperation(SQLModel, table=True):
    """Tracks AI operations performed on notes."""

    __tablename__ = "ai_operations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="notes.id")
    operation_type: AIOperationType
    input_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Operation parameters
    result: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # AI response
    prompt_used: Optional[str] = Field(default=None)
    model_used: Optional[str] = Field(default=None, max_length=100)
    tokens_used: Optional[int] = Field(default=None)
    execution_time_ms: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    # Relationships
    note: Note = Relationship(back_populates="ai_operations")


class SearchQuery(SQLModel, table=True):
    """Tracks user search queries for analytics and improvements."""

    __tablename__ = "search_queries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    query: str = Field(max_length=1000)
    results_count: int = Field(default=0)
    execution_time_ms: Optional[int] = Field(default=None)
    filters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Applied filters
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class FolderCreate(SQLModel, table=False):
    """Schema for creating a new folder."""

    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    parent_id: Optional[int] = Field(default=None)


class FolderUpdate(SQLModel, table=False):
    """Schema for updating a folder."""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    parent_id: Optional[int] = Field(default=None)


class TagCreate(SQLModel, table=False):
    """Schema for creating a new tag."""

    name: str = Field(max_length=100)
    color: Optional[str] = Field(default="#6366f1", max_length=7)
    description: Optional[str] = Field(default=None, max_length=500)


class TagUpdate(SQLModel, table=False):
    """Schema for updating a tag."""

    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=7)
    description: Optional[str] = Field(default=None, max_length=500)


class NoteCreate(SQLModel, table=False):
    """Schema for creating a new note."""

    title: str = Field(max_length=500)
    content: str = Field(default="")
    folder_id: Optional[int] = Field(default=None)
    tag_ids: List[int] = Field(default=[])


class NoteUpdate(SQLModel, table=False):
    """Schema for updating a note."""

    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = Field(default=None)
    folder_id: Optional[int] = Field(default=None)
    status: Optional[NoteStatus] = Field(default=None)
    is_favorite: Optional[bool] = Field(default=None)
    tag_ids: Optional[List[int]] = Field(default=None)


class NoteConnectionCreate(SQLModel, table=False):
    """Schema for creating a note connection."""

    source_note_id: int
    target_note_id: int
    connection_type: str = Field(default="related", max_length=100)
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = Field(default=None, max_length=500)


class AIOperationRequest(SQLModel, table=False):
    """Schema for requesting an AI operation."""

    note_id: int
    operation_type: AIOperationType
    parameters: Dict[str, Any] = Field(default={})
    question: Optional[str] = Field(default=None)  # For answer_question operations


class SearchRequest(SQLModel, table=False):
    """Schema for search requests."""

    query: str = Field(max_length=1000)
    folder_ids: Optional[List[int]] = Field(default=None)
    tag_ids: Optional[List[int]] = Field(default=None)
    status: Optional[NoteStatus] = Field(default=None)
    favorites_only: bool = Field(default=False)
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class NoteSearchResult(SQLModel, table=False):
    """Schema for search results."""

    id: int
    title: str
    content_snippet: str
    folder_name: Optional[str] = Field(default=None)
    tags: List[str] = Field(default=[])
    created_at: str  # ISO format string
    updated_at: str  # ISO format string
    relevance_score: float = Field(default=0.0)


class AIOperationResponse(SQLModel, table=False):
    """Schema for AI operation responses."""

    operation_id: int
    operation_type: AIOperationType
    result: Dict[str, Any]
    success: bool
    execution_time_ms: Optional[int] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
