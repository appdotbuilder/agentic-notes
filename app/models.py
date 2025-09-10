from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from datetime import datetime
from typing import Optional, List, Dict, Any


# Association table for many-to-many relationship between notes and tags
class NoteTag(SQLModel, table=True):
    __tablename__ = "note_tags"  # type: ignore[assignment]

    note_id: int = Field(foreign_key="notes.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


# Persistent models (stored in database)
class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: str = Field(default="", max_length=500)
    color: str = Field(default="#6B7280", max_length=7)  # Hex color code for theming
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    notes: List["Note"] = Relationship(back_populates="category")


class Tag(SQLModel, table=True):
    __tablename__ = "tags"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    color: str = Field(default="#374151", max_length=7)  # Hex color code for theming
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    notes: List["Note"] = Relationship(back_populates="tags", link_model=NoteTag)


class Note(SQLModel, table=True):
    __tablename__ = "notes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    content: str = Field(default="", max_length=10000)
    is_pinned: bool = Field(default=False, index=True)
    is_archived: bool = Field(default=False, index=True)
    note_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Foreign keys
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)

    # Relationships
    category: Optional[Category] = Relationship(back_populates="notes")
    tags: List[Tag] = Relationship(back_populates="notes", link_model=NoteTag)


# Non-persistent schemas (for validation, forms, API requests/responses)
class CategoryCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    color: str = Field(default="#6B7280", max_length=7)


class CategoryUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, max_length=7)


class TagCreate(SQLModel, table=False):
    name: str = Field(max_length=50)
    color: str = Field(default="#374151", max_length=7)


class TagUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)


class NoteCreate(SQLModel, table=False):
    title: str = Field(max_length=200)
    content: str = Field(default="", max_length=10000)
    category_id: Optional[int] = Field(default=None)
    tag_ids: List[int] = Field(default=[])
    is_pinned: bool = Field(default=False)
    note_metadata: Dict[str, Any] = Field(default={})


class NoteUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = Field(default=None, max_length=10000)
    category_id: Optional[int] = Field(default=None)
    tag_ids: Optional[List[int]] = Field(default=None)
    is_pinned: Optional[bool] = Field(default=None)
    is_archived: Optional[bool] = Field(default=None)
    note_metadata: Optional[Dict[str, Any]] = Field(default=None)


class NoteResponse(SQLModel, table=False):
    id: int
    title: str
    content: str
    is_pinned: bool
    is_archived: bool
    created_at: str  # ISO format string
    updated_at: str  # ISO format string
    category_id: Optional[int]
    category_name: Optional[str] = None
    tag_names: List[str] = Field(default=[])
    note_metadata: Dict[str, Any] = Field(default={})


class CategoryResponse(SQLModel, table=False):
    id: int
    name: str
    description: str
    color: str
    created_at: str  # ISO format string
    updated_at: str  # ISO format string
    note_count: int = Field(default=0)


class TagResponse(SQLModel, table=False):
    id: int
    name: str
    color: str
    created_at: str  # ISO format string
    note_count: int = Field(default=0)
