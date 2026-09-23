from src.utils import normalize_views, video_id_from_url, youtube_search_url


def test_normalize_common_view_counts():
    assert normalize_views("1.2M views") == 1_200_000
    assert normalize_views("500K views") == 500_000
    assert normalize_views("12 mil vistas") == 12_000
    assert normalize_views("1,234 views") == 1234
    assert normalize_views("views unavailable") is None


def test_normalize_compact_youtube_view_counts_without_label():
    assert normalize_views("10 k") == 10_000
    assert normalize_views("103 k") == 103_000
    assert normalize_views("2.7 K") == 2_700
    assert normalize_views("180 k") == 180_000
    assert normalize_views("1.3 M") == 1_300_000
    assert normalize_views("635 k") == 635_000
    assert normalize_views("hace 2 años") is None


def test_url_helpers():
    assert "search_query=no+se" in youtube_search_url("no se")
    assert video_id_from_url("https://www.youtube.com/watch?v=abc_123&t=2") == "abc_123"
