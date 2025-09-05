#!/usr/bin/env python3
"""
MemU Memory Store Example

This example demonstrates how to use the MemuMemoryStore class,
which provides a BaseMemoryStore interface over the MemU memory agent system.

Usage:
    poetry run python examples/memory_agent/memu_memory_store_example.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path to import wizagent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wizagent.llm_adapter import get_llm_client_memory_compatible
from wizagent.memory.memu_store import MemuMemoryStore
from wizagent.memory.models import MemoryFilter, MemoryItem

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """
    Demonstrate MemU memory store operations using the BaseMemoryStore interface
    """
    print("🧠 MemU Memory Store Example")
    print("=" * 50)

    try:
        # Initialize LLM client (required for memory operations)
        print("1. Initializing LLM client...")
        llm_client = get_llm_client_memory_compatible()
        print(f"   ✓ Using {type(llm_client.llm_client).__name__}")

        # Initialize MemU Memory Store
        print("\n2. Creating MemU Memory Store...")
        memory_store = MemuMemoryStore(
            memory_dir="./examples/memory_agent/memu_store_example_storage",
            agent_id="memu_example_agent",
            user_id="example_user",
            llm_client=llm_client,
            enable_embeddings=True,
        )
        print("   ✓ MemU Memory Store initialized")

        # Create sample memory items
        print("\n3. Adding memory items...")

        # Create memory item 1
        memory_item1 = MemoryItem(
            content="User mentioned they love hiking in the mountains and work as a software engineer.",
            memory_type="fact",
            user_id="alice",
            importance=0.8,
            tags=["personal", "hobby", "work"],
            metadata={"category": "user_profile"},
        )

        memory_id1 = await memory_store.add(memory_item1)
        print(f"   ✓ Added memory item 1: {memory_id1}")

        # Create memory item 2
        memory_item2 = MemoryItem(
            content="User prefers morning meetings and has a cat named Whiskers.",
            memory_type="note",
            user_id="alice",
            importance=0.6,
            tags=["personal", "preferences"],
            metadata={"category": "preferences"},
        )

        memory_id2 = await memory_store.add(memory_item2)
        print(f"   ✓ Added memory item 2: {memory_id2}")

        # Create memory item 3
        memory_item3 = MemoryItem(
            content="Discussion about Python programming best practices and code review process.",
            memory_type="message",
            user_id="alice",
            session_id="session_123",
            importance=0.7,
            tags=["technical", "programming"],
            metadata={"category": "work_discussion"},
        )

        memory_id3 = await memory_store.add(memory_item3)
        print(f"   ✓ Added memory item 3: {memory_id3}")

        # Retrieve a memory item
        print("\n4. Retrieving memory items...")
        retrieved_item = await memory_store.get(memory_id1)
        if retrieved_item:
            print(f"   ✓ Retrieved item: {retrieved_item.content[:50]}...")
        else:
            print("   ✗ Failed to retrieve item")

        # Update a memory item
        print("\n5. Updating memory item...")
        update_success = await memory_store.update(
            memory_id1,
            {
                "importance": 0.9,
                "tags": ["personal", "hobby", "work", "updated"],
                "metadata": {"category": "user_profile", "last_updated": "example"},
            },
        )
        print(f"   ✓ Update successful: {update_success}")

        # Get all memory items
        print("\n6. Retrieving all memory items...")
        all_items = await memory_store.get_all()
        print(f"   ✓ Total items: {len(all_items)}")
        for i, item in enumerate(all_items, 1):
            print(f"   {i}. [{item.memory_type}] {item.content[:40]}... (importance: {item.importance})")

        # Filter memory items
        print("\n7. Filtering memory items...")

        # Filter by user
        user_filter = MemoryFilter(user_id="alice")
        user_items = await memory_store.get_all(filters=user_filter)
        print(f"   ✓ Items for user 'alice': {len(user_items)}")

        # Filter by importance
        important_filter = MemoryFilter(min_importance=0.7)
        important_items = await memory_store.get_all(filters=important_filter)
        print(f"   ✓ High importance items (≥0.7): {len(important_items)}")

        # Filter by tags
        tag_filter = MemoryFilter(tags=["personal"])
        tagged_items = await memory_store.get_all(filters=tag_filter)
        print(f"   ✓ Items tagged 'personal': {len(tagged_items)}")

        # Search memory items
        print("\n8. Searching memory items...")
        search_results = await memory_store.search("hiking mountains", limit=5, threshold=0.3)
        print(f"   ✓ Search results for 'hiking mountains': {len(search_results)}")
        for result in search_results:
            print(f"   - Score: {result.relevance_score:.2f} | {result.memory_item.content[:50]}...")

        # Get memory statistics
        print("\n9. Getting memory statistics...")
        stats = await memory_store.get_stats()
        print(f"   ✓ Total items: {stats.total_items}")
        print(f"   ✓ Average importance: {stats.average_importance:.2f}")
        print(f"   ✓ Storage size: {stats.storage_size_bytes} bytes")
        print(f"   ✓ Items by type: {stats.items_by_type}")

        # Count items
        print("\n10. Counting items...")
        total_count = await memory_store.count()
        important_count = await memory_store.count(filters=important_filter)
        print(f"   ✓ Total items: {total_count}")
        print(f"   ✓ Important items: {important_count}")

        # Clean up old memories (dry run)
        print("\n11. Testing cleanup (dry run)...")
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        cleanup_count = await memory_store.cleanup_old_memories(
            older_than=one_day_ago, preserve_important=True, dry_run=True
        )
        print(f"   ✓ Items that would be cleaned up: {cleanup_count}")

        # Batch operations
        print("\n12. Testing batch operations...")

        # Create more items for batch testing
        batch_items = [
            MemoryItem(content=f"Batch item {i}", user_id="alice", importance=0.5 + i * 0.1) for i in range(3)
        ]

        batch_ids = await memory_store.add_many(batch_items)
        print(f"   ✓ Added batch items: {len(batch_ids)}")

        # Delete some items in batch
        items_to_delete = batch_ids[:2]  # Delete first 2 batch items
        deleted_count = await memory_store.delete_many(items_to_delete)
        print(f"   ✓ Deleted {deleted_count} items in batch")

        # Final stats
        print("\n13. Final statistics...")
        final_stats = await memory_store.get_stats()
        print(f"   ✓ Final total items: {final_stats.total_items}")

        print("\n✅ MemU Memory Store example completed successfully!")
        print(f"\n📁 Check the memory files in: ./examples/memory_agent/memu_store_example_storage/")

    except Exception as e:
        logger.error(f"Error in MemU memory store example: {e}")
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
