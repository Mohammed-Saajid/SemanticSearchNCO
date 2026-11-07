import pytest
from app.services.chunking import TextChunker


def test_chunker_initialization_invalid_params():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=0)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=50, chunk_overlap=50)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=50, chunk_overlap=-1)


def test_chunk_empty_text():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    assert chunker.chunk_text("") == []
    assert chunker.chunk_text("    ") == []


def test_chunk_text_smaller_than_chunk_size():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    text = "word1 word2 word3"
    result = chunker.chunk_text(text)
    assert len(result) == 1
    assert result[0] == text


def test_chunk_text_exact_chunk_size():
    chunker = TextChunker(chunk_size=4, chunk_overlap=1)
    text = "one two three four"
    result = chunker.chunk_text(text)
    assert len(result) == 1
    assert result[0] == text


def test_chunk_text_multiple_overlapping_chunks():
    chunker = TextChunker(chunk_size=4, chunk_overlap=2)
    words = [f"w{i}" for i in range(8)]
    text = " ".join(words)
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "w0 w1 w2 w3"
    assert chunks[1] == "w2 w3 w4 w5"
    assert chunks[2] == "w4 w5 w6 w7"


def test_chunk_role():
    chunker = TextChunker(chunk_size=3, chunk_overlap=1)
    role_number = "9999.0100"
    description = "a b c d e"
    chunks = chunker.chunk_role(role_number, description)
    assert len(chunks) == 2
    assert chunks[0].chunk_id == "9999.0100_chunk0"
    assert chunks[0].role_number == role_number
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "a b c"
    assert chunks[1].chunk_id == "9999.0100_chunk1"
    assert chunks[1].chunk_index == 1
    assert chunks[1].text == "c d e"

