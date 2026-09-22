from src.models import VideoResult
from src.validator import is_valid_result


def test_validator_requires_minimum_traceable_fields():
    valid = VideoResult("query", "", 1, "id", "title", "channel", None, "", "", "", "https://youtube.com/watch?v=id", "", "now")
    assert is_valid_result(valid)
    assert not is_valid_result(valid.__class__("query", "", 0, "id", "title", "channel", None, "", "", "", "https://youtube.com/watch?v=id", "", "now"))
