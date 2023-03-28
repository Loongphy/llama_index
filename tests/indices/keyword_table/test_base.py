"""Test keyword table index."""

from typing import Any, List
from unittest.mock import patch

import pytest

from gpt_index.indices.keyword_table.simple_base import GPTSimpleKeywordTableIndex
from gpt_index.langchain_helpers.chain_wrapper import LLMPredictor
from gpt_index.readers.schema.base import Document
from tests.mock_utils.mock_decorator import patch_common
from tests.mock_utils.mock_predict import mock_llmpredictor_predict
from tests.mock_utils.mock_utils import mock_extract_keywords


@pytest.fixture
def documents() -> List[Document]:
    """Get documents."""
    # NOTE: one document for now
    doc_text = (
        "Hello world.\n"
        "This is a test.\n"
        "This is another test.\n"
        "This is a test v2."
    )
    return [Document(doc_text)]


@patch_common
@patch(
    "gpt_index.indices.keyword_table.simple_base.simple_extract_keywords",
    mock_extract_keywords,
)
def test_build_table(
    _mock_init: Any,
    _mock_predict: Any,
    _mock_total_tokens_used: Any,
    _mock_split_text_overlap: Any,
    _mock_split_text: Any,
    documents: List[Document],
) -> None:
    """Test build table."""
    # test simple keyword table
    # NOTE: here the keyword extraction isn't mocked because we're using
    # the regex-based keyword extractor, not GPT
    table = GPTSimpleKeywordTableIndex.from_documents(documents)
    nodes = table.docstore.get_nodes(list(table.index_struct.node_ids))
    table_chunks = {n.get_text() for n in nodes}
    assert len(table_chunks) == 4
    assert "Hello world." in table_chunks
    assert "This is a test." in table_chunks
    assert "This is another test." in table_chunks
    assert "This is a test v2." in table_chunks

    # test that expected keys are present in table
    # NOTE: in mock keyword extractor, stopwords are not filtered
    assert table.index_struct.table.keys() == {
        "this",
        "hello",
        "world",
        "test",
        "another",
        "v2",
        "is",
        "a",
        "v2",
    }


@patch_common
@patch.object(LLMPredictor, "apredict", side_effect=mock_llmpredictor_predict)
@patch(
    "gpt_index.indices.keyword_table.simple_base.simple_extract_keywords",
    mock_extract_keywords,
)
def test_build_table_async(
    _mock_extract: Any,
    _mock_init: Any,
    _mock_predict: Any,
    _mock_total_tokens_used: Any,
    _mock_split_text_overlap: Any,
    _mock_split_text: Any,
    documents: List[Document],
) -> None:
    """Test build table."""
    # test simple keyword table
    # NOTE: here the keyword extraction isn't mocked because we're using
    # the regex-based keyword extractor, not GPT
    table = GPTSimpleKeywordTableIndex.from_documents(documents, use_async=True)
    nodes = table.docstore.get_nodes(list(table.index_struct.node_ids))
    table_chunks = {n.get_text() for n in nodes}
    assert len(table_chunks) == 4
    assert "Hello world." in table_chunks
    assert "This is a test." in table_chunks
    assert "This is another test." in table_chunks
    assert "This is a test v2." in table_chunks

    # test that expected keys are present in table
    # NOTE: in mock keyword extractor, stopwords are not filtered
    assert table.index_struct.table.keys() == {
        "this",
        "hello",
        "world",
        "test",
        "another",
        "v2",
        "is",
        "a",
        "v2",
    }


@patch_common
@patch(
    "gpt_index.indices.keyword_table.simple_base.simple_extract_keywords",
    mock_extract_keywords,
)
def test_insert(
    _mock_init: Any,
    _mock_predict: Any,
    _mock_total_tokens_used: Any,
    _mock_split_text_overlap: Any,
    _mock_split_text: Any,
    documents: List[Document],
) -> None:
    """Test insert."""
    table = GPTSimpleKeywordTableIndex([])
    assert len(table.index_struct.table.keys()) == 0
    table.insert(documents[0])
    nodes = table.docstore.get_nodes(list(table.index_struct.node_ids))
    table_chunks = {n.get_text() for n in nodes}
    assert "Hello world." in table_chunks
    assert "This is a test." in table_chunks
    assert "This is another test." in table_chunks
    assert "This is a test v2." in table_chunks
    # test that expected keys are present in table
    # NOTE: in mock keyword extractor, stopwords are not filtered
    assert table.index_struct.table.keys() == {
        "this",
        "hello",
        "world",
        "test",
        "another",
        "v2",
        "is",
        "a",
        "v2",
    }

    # test insert with doc_id
    document1 = Document("This is", doc_id="test_id1")
    document2 = Document("test v3", doc_id="test_id2")
    table = GPTSimpleKeywordTableIndex([])
    table.insert(document1)
    table.insert(document2)
    chunk_index1_1 = list(table.index_struct.table["this"])[0]
    chunk_index1_2 = list(table.index_struct.table["is"])[0]
    chunk_index2_1 = list(table.index_struct.table["test"])[0]
    chunk_index2_2 = list(table.index_struct.table["v3"])[0]
    nodes = table.docstore.get_nodes(
        [chunk_index1_1, chunk_index1_2, chunk_index2_1, chunk_index2_2]
    )
    assert nodes[0].ref_doc_id == "test_id1"
    assert nodes[1].ref_doc_id == "test_id1"
    assert nodes[2].ref_doc_id == "test_id2"
    assert nodes[3].ref_doc_id == "test_id2"


@patch_common
@patch(
    "gpt_index.indices.keyword_table.simple_base.simple_extract_keywords",
    mock_extract_keywords,
)
def test_delete(
    _mock_init: Any,
    _mock_predict: Any,
    _mock_total_tokens_used: Any,
    _mock_split_text_overlap: Any,
    _mock_split_text: Any,
    documents: List[Document],
) -> None:
    """Test insert."""
    new_documents = [
        Document("Hello world.\nThis is a test.", doc_id="test_id_1"),
        Document("This is another test.", doc_id="test_id_2"),
        Document("This is a test v2.", doc_id="test_id_3"),
    ]

    # test delete
    table = GPTSimpleKeywordTableIndex.from_documents(new_documents)
    table.delete("test_id_1")
    assert len(table.index_struct.table.keys()) == 6
    print(table.index_struct.table.keys())
    assert len(table.index_struct.table["this"]) == 2
    nodes = table.docstore.get_nodes(list(table.index_struct.node_ids))
    node_texts = {n.get_text() for n in nodes}
    assert node_texts == {"This is another test.", "This is a test v2."}

    table = GPTSimpleKeywordTableIndex.from_documents(new_documents)
    table.delete("test_id_2")
    assert len(table.index_struct.table.keys()) == 7
    assert len(table.index_struct.table["this"]) == 2
    nodes = table.docstore.get_nodes(list(table.index_struct.node_ids))
    node_texts = {n.get_text() for n in nodes}
    assert node_texts == {"Hello world.", "This is a test.", "This is a test v2."}


@patch_common
@patch(
    "gpt_index.indices.keyword_table.simple_base.simple_extract_keywords",
    mock_extract_keywords,
)
@patch(
    "gpt_index.indices.query.keyword_table.query.simple_extract_keywords",
    mock_extract_keywords,
)
def test_query(
    _mock_init: Any,
    _mock_predict: Any,
    _mock_total_tokens_used: Any,
    _mock_split_text_overlap: Any,
    _mock_split_text: Any,
    documents: List[Document],
) -> None:
    """Test query."""
    # test simple keyword table
    # NOTE: here the keyword extraction isn't mocked because we're using
    # the regex-based keyword extractor, not GPT
    table = GPTSimpleKeywordTableIndex.from_documents(documents)

    response = table.query("Hello", mode="simple")
    assert str(response) == "Hello:Hello world."

    # try with filters
    doc_text = (
        "Hello world\n" "Hello foo\n" "This is another test\n" "This is a test v2"
    )
    documents2 = [Document(doc_text)]
    table2 = GPTSimpleKeywordTableIndex.from_documents(documents2)
    # NOTE: required keywords are somewhat redundant
    response = table2.query("This", mode="simple", required_keywords=["v2"])
    assert str(response) == "This:This is a test v2"

    # test exclude_keywords
    response = table2.query("Hello", mode="simple", exclude_keywords=["world"])
    assert str(response) == "Hello:Hello foo"
