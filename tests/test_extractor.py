from src.models import VideoResult
from src.extractor import YouTubeExtractor
from src.validator import is_valid_result


def test_validator_requires_minimum_traceable_fields():
    valid = VideoResult("query", "", 1, "id", "title", "channel", None, "", "", "", "https://youtube.com/watch?v=id", "", "now")
    assert is_valid_result(valid)
    assert not is_valid_result(valid.__class__("query", "", 0, "id", "title", "channel", None, "", "", "", "https://youtube.com/watch?v=id", "", "now"))


def test_metadata_classifier_does_not_confuse_views_with_relative_date():
    views, published = YouTubeExtractor.classify_metadata(["hace 2 años", "103 k"])
    assert views == "103 k"
    assert published == "hace 2 años"


def test_metadata_classifier_leaves_unknown_values_empty():
    views, published = YouTubeExtractor.classify_metadata(["metadata not understood"])
    assert views == ""
    assert published == ""
