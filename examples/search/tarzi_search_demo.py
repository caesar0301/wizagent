#!/usr/bin/env python3
"""
Tarzi Search Demo
"""

import asyncio

from wizagent.search import TarziSearch, TarziSearchConfig, TarziSearchError


def demo_basic_search():
    """Demonstrate basic Tarzi search functionality."""
    print("=== Basic Tarzi Search Demo ===")

    try:
        # Initialize with custom configuration for better timeout
        config = TarziSearchConfig()
        search = TarziSearch(config=config)

        # Perform a basic search
        query = "artificial intelligence latest developments"
        print(f"\nSearching for: '{query}'")

        result = search.search(query)

        print(f"Response time: {result.response_time:.2f}s")
        print(f"Number of sources: {len(result.sources)}")

        if result.answer:
            print(f"\nDirect answer: {result.answer}")

        print("\nTop 5 results:")
        for i, source in enumerate(result.sources[:5], 1):
            print(f"\n{i}. {source.title}")
            print(f"   URL: {source.url}")
            if source.content:
                content = source.content[:200] + "..." if len(source.content) > 200 else source.content
                print(f"   Content: {content}")

    except TarziSearchError as e:
        print(f"Tarzi search error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def demo_async_search():
    """Demonstrate async Tarzi search functionality."""
    print("\n=== Async Search Demo ===")

    try:
        config = TarziSearchConfig()
        search = TarziSearch(config=config)

        # Perform multiple async searches
        queries = ["climate change solutions", "renewable energy technologies", "electric vehicle adoption"]

        print(f"\nPerforming {len(queries)} async searches...")

        # Run searches concurrently
        tasks = [search.async_search(query) for query in queries]
        results = await asyncio.gather(*tasks)

        for query, result in zip(queries, results):
            print(f"Response time: {result.response_time:.2f}s")
            print(f"Sources found: {len(result.sources)}")
            if result.sources:
                print(f"Top result: {result.sources[0].title}")

    except TarziSearchError as e:
        print(f"Tarzi search error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    """Run all demos."""
    print("Tarzi Search Demo")
    print("==================")

    # Run sync demos
    demo_basic_search()

    # Run async demo
    print("\n" + "=" * 50)
    asyncio.run(demo_async_search())

    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()
