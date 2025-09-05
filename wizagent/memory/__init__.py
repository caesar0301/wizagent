"""
This package provides a clean, well-documented interface for memory operations
with Pydantic-based data models and abstract base classes that can be
implemented by various storage backends.

The design philosophy emphasizes:
- Simplicity: Clean, intuitive APIs
- Agility: Easy to extend and customize
- Functionality: Complete feature set for memory operations
- Type Safety: Full Pydantic model validation
- Async Support: Modern async/await patterns
- Documentation: Comprehensive interface documentation
"""

# Import abstract base classes
from .base import (
    BaseMemoryManager,
    BaseMemoryStore,
)

# Import all models
from .models import (
    BaseMemoryItem,
    MemoryFilter,
    MemoryItem,
    MemoryStats,
    SearchResult,
)

# Define public API
__all__ = [
    # Data Models
    "BaseMemoryItem",
    "MemoryItem",
    "MemoryFilter",
    "SearchResult",
    "MemoryStats",
    # Abstract Interfaces
    "BaseMemoryStore",
    "BaseMemoryManager",
]
