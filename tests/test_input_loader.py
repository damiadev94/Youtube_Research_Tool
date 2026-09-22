import pytest

from src.input_loader import load_queries


def test_loads_utf8_optional_columns(tmp_path):
    path = tmp_path / "queries.csv"
    path.write_text("category,query,url\nPropósito,qué hacer con mi vida,\n", encoding="utf-8")
    rows = load_queries(path)
    assert rows[0].category == "Propósito"
    assert "search_query=qu%C3%A9+hacer+con+mi+vida" in rows[0].url


def test_requires_query_header(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("term\na\n", encoding="utf-8")
    with pytest.raises(ValueError, match="query"):
        load_queries(path)
