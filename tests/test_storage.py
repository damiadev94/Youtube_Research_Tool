import csv

from src.models import SearchQuery, VideoResult
from src.storage import CsvStorage


def test_incremental_results_and_checkpoints(tmp_path):
    storage = CsvStorage(tmp_path)
    search = SearchQuery(query="one", category="cat", url="https://example.test")
    result = VideoResult("one", "cat", 1, "id", "Title", "Channel", 1, "1 view", "today", "1:00", "https://youtube.com/watch?v=id", "", "now")
    assert storage.save_results([result]) == 1
    storage.mark_completed(search)
    assert storage.is_completed(search)
    with (tmp_path / "results.csv").open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle))[0]["title"] == "Title"
