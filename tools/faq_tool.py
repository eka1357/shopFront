"""Local RAG search tool over Bloom Hair Studio FAQ knowledge base.

Uses lightweight TF-IDF and cosine similarity to retrieve relevant business
information, pricing, and policies without external vector database dependencies.
"""

import math
import os
import re
from collections import Counter
from pathlib import Path
from strands import tool

FAQ_PATH = Path(__file__).parent.parent / "faq.md"


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "did",
    "do", "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "must", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "won't", "would", "you", "your", "yours"
}


def _tokenize(text: str, filter_stops: bool = True) -> list[str]:
    """Tokenize and normalize text into lowercase alphanumeric terms, optionally filtering stop words."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
    if filter_stops:
        return [t for t in tokens if t not in STOP_WORDS]
    return tokens



class LocalFAQRetriever:
    """Lightweight in-memory TF-IDF knowledge base indexer and search retriever."""

    def __init__(self, faq_file_path: Path | str = FAQ_PATH):
        self.file_path = Path(faq_file_path)
        self.chunks: list[dict[str, str]] = []
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.chunk_vectors: list[dict[str, float]] = []
        self._load_and_index()

    def _load_and_index(self) -> None:
        """Parse markdown file into semantic chunks and compute TF-IDF representations."""
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split content by markdown section headers (H2 / H3)
        raw_sections = re.split(r"\n(?=##?#?\s)", content)
        chunks = []

        for sec in raw_sections:
            sec_text = sec.strip()
            if not sec_text:
                continue

            # Extract header if present
            lines = sec_text.splitlines()
            title = lines[0].replace("#", "").strip() if lines else "General FAQ"
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec_text

            title_tokens = _tokenize(title)
            body_tokens = _tokenize(sec_text)
            # Boost title tokens to prioritize explicit section header matches
            combined_tokens = body_tokens + (title_tokens * 3)

            chunks.append({
                "title": title,
                "content": sec_text,
                "tokens": combined_tokens,
            })

        self.chunks = chunks
        num_docs = len(self.chunks)
        if num_docs == 0:
            return

        # Build document frequency (DF)
        doc_freq: Counter[str] = Counter()
        for chunk in self.chunks:
            unique_terms = set(chunk["tokens"])
            for term in unique_terms:
                doc_freq[term] += 1

        # Calculate inverse document frequency (IDF) with smoothing
        self.idf = {
            term: math.log((1 + num_docs) / (1 + count)) + 1.0
            for term, count in doc_freq.items()
        }

        # Calculate TF-IDF vectors for all chunks
        self.chunk_vectors = []
        for chunk in self.chunks:
            tf = Counter(chunk["tokens"])
            total_tokens = len(chunk["tokens"]) or 1
            vector: dict[str, float] = {}
            for term, count in tf.items():
                term_tf = count / total_tokens
                term_idf = self.idf.get(term, 1.0)
                vector[term] = term_tf * term_idf

            # Normalize vector (L2 norm)
            norm = math.sqrt(sum(val * val for val in vector.values())) or 1.0
            self.chunk_vectors.append({k: v / norm for k, v in vector.items()})

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str | float]]:
        """Retrieve the top-k most relevant FAQ chunks for a natural language query."""
        if not self.chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        # Calculate query TF-IDF vector
        query_tf = Counter(query_tokens)
        total_q_tokens = len(query_tokens)
        query_vec: dict[str, float] = {}
        for term, count in query_tf.items():
            if term in self.idf:
                query_vec[term] = (count / total_q_tokens) * self.idf[term]

        q_norm = math.sqrt(sum(val * val for val in query_vec.values()))
        if q_norm == 0:
            # Fallback substring scan if no vocabulary overlap
            matches = []
            for chunk in self.chunks:
                text_lower = chunk["content"].lower()
                score = sum(1.0 for t in query_tokens if t in text_lower)
                if score > 0:
                    matches.append({"title": chunk["title"], "content": chunk["content"], "score": score})
            matches.sort(key=lambda x: x["score"], reverse=True)
            return matches[:top_k]

        normalized_q = {k: v / q_norm for k, v in query_vec.items()}

        # Cosine similarity against each chunk
        results = []
        for i, chunk_vec in enumerate(self.chunk_vectors):
            score = sum(val * chunk_vec.get(term, 0.0) for term, val in normalized_q.items())
            if score > 0.01:
                results.append({
                    "title": self.chunks[i]["title"],
                    "content": self.chunks[i]["content"],
                    "score": round(score, 4),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# Global singleton instance for the session
_retriever = LocalFAQRetriever()


@tool
def search_faq(query: str) -> str:
    """Search Bloom Hair Studio's knowledge base.

    Use this tool to find information about salon services, pricing, treatment duration,
    operating hours, 24-hour cancellation policy, late arrival rules, refund/adjustment terms,
    parking, or studio address.

    Args:
        query: The customer's inquiry or keyword (e.g., "haircut price", "cancellation policy", "balayage duration", "open Sunday").

    Returns:
        Formatted snippets from the official Bloom Hair Studio knowledge base answering the query.
    """
    matches = _retriever.search(query, top_k=2)
    if not matches:
        return "No specific FAQ entry found for this query. Inform the customer or check studio policies."

    output_lines = ["Relevant Information from Bloom Hair Studio Knowledge Base:"]
    for match in matches:
        output_lines.append(f"\n--- {match['title']} ---")
        output_lines.append(str(match["content"]))

    return "\n".join(output_lines)
