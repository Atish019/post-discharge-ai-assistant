def build_context_with_citations(chunks):
    """
    Build context with inline citations
    
    Args:
        chunks: List of retrieved chunks with metadata
    
    Returns:
        tuple: (context_with_citations, citation_list)
    """
    context_blocks = []
    citations = []
    
    for i, chunk in enumerate(chunks, 1):
        page = chunk.get("page", "Unknown")
        text = chunk.get("text", "")
        
        # Add inline citation marker
        context_block = f"[Source {i}: Page {page}]\n{text}"
        context_blocks.append(context_block)
        
        # Track citation
        citations.append({
            "source_num": i,
            "page": page,
            "chunk_id": chunk.get("chunk_id", "N/A")
        })
    
    # Join with clear separators
    context = "\n\n---\n\n".join(context_blocks)
    
    # Format citation list
    citation_text = "\n".join([
        f"Source {c['source_num']}: Page {c['page']}" 
        for c in citations
    ])
    
    return context, citation_text


def format_answer_with_citations(answer, citations):
    """
    Append citations to answer
    
    Args:
        answer: LLM generated answer
        citations: Citation list
    
    Returns:
        Complete answer with citations section
    """
    formatted = f"""{answer}

---
 **Sources:**
{citations}
"""
    return formatted


def extract_citations_from_text(text, chunks):
    """
    Extract which sources were actually used in answer
    (Advanced: checks if chunk text appears in answer)
    """
    used_sources = []
    
    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk.get("text", "")
        words = chunk_text.split()[:20] 
        sample = " ".join(words)
        
        if len(sample) > 30 and sample.lower() in text.lower():
            used_sources.append({
                "source_num": i,
                "page": chunk.get("page"),
                "relevance": "high"
            })
    
    return used_sources if used_sources else [
        {"source_num": i+1, "page": c.get("page"), "relevance": "provided"} 
        for i, c in enumerate(chunks)
    ]