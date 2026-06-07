"""Offline tests — schema building, no network. / 오프라인 테스트(네트워크 없음)."""
from stockagent.tools import SCHEMAS, get_stock_info


def test_schema_shape():
    s = get_stock_info.schema
    assert s["function"]["name"] == "get_stock_info"
    assert "ticker" in s["function"]["parameters"]["required"]


def test_all_tools_have_schema():
    assert len(SCHEMAS) == 3
    assert all("function" in s for s in SCHEMAS)
