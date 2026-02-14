"""
Text chunking utilities for AI context management.

Provides simple overlap-based chunking with interface designed for future
migration to vector-based semantic search.
"""

from typing import List, TypedDict


class Chunk(TypedDict):
    """Represents a text chunk with metadata."""
    text: str
    start_index: int
    end_index: int
    chunk_id: int


def chunk_text(text: str, max_tokens: int = 2000, overlap: int = 200) -> List[Chunk]:
    """
    Split text into overlapping chunks for AI processing.

    Args:
        text: Source text to chunk
        max_tokens: Maximum tokens per chunk (approximate using chars/4)
        overlap: Character overlap between consecutive chunks

    Returns:
        List of Chunk dictionaries with text, indices, and IDs

    Note:
        This uses character-based approximation (1 token ≈ 4 chars).
        Future implementation can swap in semantic chunking with embeddings.
    """
    if not text or not text.strip():
        return []

    # Approximate tokens to characters (1 token ≈ 4 characters for English)
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4

    chunks: List[Chunk] = []
    start = 0
    chunk_id = 0

    while start < len(text):
        # Calculate chunk end position
        end = min(start + max_chars, len(text))

        # Try to break at sentence boundary if not at text end
        if end < len(text):
            # Look for sentence endings within last 20% of chunk
            search_start = max(start, end - max_chars // 5)
            sentence_ends = [
                i for i in range(search_start, end)
                if text[i] in '.!?' and (i + 1 >= len(text) or text[i + 1].isspace())
            ]
            if sentence_ends:
                end = sentence_ends[-1] + 1

        # Extract chunk text
        chunk_text = text[start:end].strip()

        if chunk_text:  # Only add non-empty chunks
            chunks.append({
                'text': chunk_text,
                'start_index': start,
                'end_index': end,
                'chunk_id': chunk_id
            })
            chunk_id += 1

        # Move start forward with overlap
        start = end - overlap_chars

        # Prevent infinite loop if overlap >= chunk size
        if start <= chunks[-1]['start_index'] if chunks else False:
            start = end

    return chunks


def get_relevant_chunks(
    question: str,
    chunks: List[Chunk],
    max_chunks: int = 5
) -> List[Chunk]:
    """
    Select most relevant chunks for a question.

    Current implementation: Simple keyword matching with scoring.
    Future: Vector similarity search with embeddings.

    Args:
        question: User's question
        chunks: All available chunks
        max_chunks: Maximum chunks to return

    Returns:
        Top-ranked chunks (by relevance score)
    """
    if not chunks:
        return []

    if not question or not question.strip():
        # Return first N chunks if no question provided
        return chunks[:max_chunks]

    # Extract keywords from question (simple: lowercase words > 3 chars)
    question_lower = question.lower()
    keywords = [
        word for word in question_lower.split()
        if len(word) > 3 and word.isalnum()
    ]

    if not keywords:
        # Fallback to first N chunks if no keywords
        return chunks[:max_chunks]

    # Score each chunk by keyword frequency
    scored_chunks: List[tuple[float, Chunk]] = []

    for chunk in chunks:
        chunk_lower = chunk['text'].lower()

        # Count keyword occurrences
        score = sum(chunk_lower.count(keyword) for keyword in keywords)

        # Bonus for keywords appearing close together
        positions = []
        for keyword in keywords:
            idx = chunk_lower.find(keyword)
            if idx >= 0:
                positions.append(idx)

        if len(positions) > 1:
            # Reward chunks with keywords within 100 chars of each other
            positions_sorted = sorted(positions)
            for i in range(len(positions_sorted) - 1):
                if positions_sorted[i + 1] - positions_sorted[i] < 100:
                    score += 0.5

        scored_chunks.append((score, chunk))

    # Sort by score descending and return top N
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    return [chunk for score, chunk in scored_chunks[:max_chunks]]
