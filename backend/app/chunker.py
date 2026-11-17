from typing import List, Dict, Any
import re
from app.config import settings

class RecursiveCharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        final_chunks = []
        separator = separators[-1]
        new_separators = []

        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator != "" else list(text)

        good_splits = []
        for s in splits:
            if separator and separator != "":
                s_with_sep = s + separator
            else:
                s_with_sep = s
            if len(s_with_sep) < self.chunk_size:
                good_splits.append(s_with_sep)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(s_with_sep)
                else:
                    other_info = self._split_text(s_with_sep, new_separators)
                    final_chunks.extend(other_info)
        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)
        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        docs = []
        current_doc = []
        total = 0

        for d in splits:
            _len = len(d)
            if total + _len > self.chunk_size:
                if total > self.chunk_size:
                    # Current chunk is already big enough
                    pass
                if current_doc:
                    doc = "".join(current_doc).strip()
                    if doc:
                        docs.append(doc)
                    # Overlap handling: rewind current_doc to maintain overlap
                    while total > self.chunk_overlap or (total + _len > self.chunk_size and total > 0):
                        if not current_doc:
                            break
                        total -= len(current_doc[0])
                        current_doc.pop(0)
            current_doc.append(d)
            total += _len

        doc = "".join(current_doc).strip()
        if doc:
            docs.append(doc)
        return docs

def chunk_pages_data(
    pages_data: List[Dict[str, Any]],
    doc_id: str,
    filename: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Splits page-extracted text into structured chunks of 1000 characters with 200 overlap.
    Preserves page numbers and chunk sequence index.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []
    chunk_seq = 0

    for page_item in pages_data:
        page_num = page_item["page"]
        text = page_item["text"]
        
        page_chunks = splitter._split_text(text, splitter.separators)
        for chunk_text in page_chunks:
            chunk_text_clean = chunk_text.strip()
            if len(chunk_text_clean) >= 20:  # Skip trivial noisy fragments
                all_chunks.append({
                    "chunk_id": f"{doc_id}_p{page_num}_c{chunk_seq}",
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_number": page_num,
                    "chunk_seq": chunk_seq,
                    "text": chunk_text_clean
                })
                chunk_seq += 1

    return all_chunks
