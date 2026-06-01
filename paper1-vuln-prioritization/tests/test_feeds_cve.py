"""CPE parsing and version-range helper tests."""

from __future__ import annotations

import pytest

from paper1.feeds.cve_client import (
    CPEParseError,
    cpe_to_product_key,
    extract_affected_ranges,
    normalize_cpe,
    parse_cpe23,
    version_in_range,
)


def test_parse_valid_cpe23():
    cpe = "cpe:2.3:a:vendor:product:1.2.3:*:*:*:*:*:*:*"
    p = parse_cpe23(cpe)
    assert p.part == "a"
    assert p.vendor == "vendor"
    assert p.product == "product"
    assert p.version == "1.2.3"


def test_normalize_cpe_roundtrip():
    cpe = "cpe:2.3:a:vendor:product:1.2.3:*:*:*:*:*:*:*"
    assert normalize_cpe(cpe) == cpe


def test_parse_cpe_rejects_short():
    with pytest.raises(CPEParseError):
        parse_cpe23("cpe:2.3:a:vendor:product")


def test_parse_cpe_rejects_wrong_prefix():
    with pytest.raises(CPEParseError):
        parse_cpe23("not:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*")


def test_parse_cpe_rejects_wrong_version():
    with pytest.raises(CPEParseError):
        parse_cpe23("cpe:2.2:a:vendor:product:1.0:*:*:*:*:*:*:*")


def test_parse_cpe_rejects_bad_part():
    with pytest.raises(CPEParseError):
        parse_cpe23("cpe:2.3:z:vendor:product:1.0:*:*:*:*:*:*:*")


def test_parse_cpe_rejects_empty():
    with pytest.raises(CPEParseError):
        parse_cpe23("")


def test_cpe_to_product_key_lowercased():
    cpe = "cpe:2.3:a:Vendor:Product:1.0:*:*:*:*:*:*:*"
    assert cpe_to_product_key(cpe) == ("vendor", "product")


def test_version_in_range_inclusive_start():
    assert version_in_range("1.0", start_including="1.0", end_excluding="2.0")
    assert version_in_range("1.5", start_including="1.0", end_excluding="2.0")


def test_version_in_range_exclusive_start():
    assert not version_in_range("1.0", start_excluding="1.0", end_excluding="2.0")
    assert version_in_range("1.1", start_excluding="1.0", end_excluding="2.0")


def test_version_in_range_inclusive_end():
    assert version_in_range("2.0", start_including="1.0", end_including="2.0")
    assert not version_in_range("2.1", start_including="1.0", end_including="2.0")


def test_version_in_range_exclusive_end():
    assert not version_in_range("2.0", start_including="1.0", end_excluding="2.0")


def test_version_in_range_no_bounds_accepts_any_concrete():
    assert version_in_range("99.99")


def test_version_in_range_wildcard_false():
    assert not version_in_range("*")
    assert not version_in_range("-")


def test_version_in_range_below_start():
    assert not version_in_range("0.9", start_including="1.0")


def test_version_in_range_above_end():
    assert not version_in_range("3.0", end_excluding="2.0")


def test_extract_affected_ranges_flat():
    node = {
        "cpeMatch": [
            {
                "vulnerable": True,
                "criteria": "cpe:2.3:a:v:p:*:*:*:*:*:*:*:*",
                "versionStartIncluding": "1.0",
                "versionEndExcluding": "2.0",
            }
        ]
    }
    ranges = list(extract_affected_ranges(node))
    assert len(ranges) == 1
    assert ranges[0].cpe == "cpe:2.3:a:v:p:*:*:*:*:*:*:*:*"
    assert ranges[0].start_including == "1.0"
    assert ranges[0].end_excluding == "2.0"


def test_extract_affected_ranges_nested():
    node = {
        "children": [
            {
                "cpeMatch": [
                    {"vulnerable": True, "criteria": "cpe:2.3:a:v:p:1.0:*:*:*:*:*:*:*"}
                ]
            }
        ]
    }
    ranges = list(extract_affected_ranges(node))
    assert len(ranges) == 1
    assert ranges[0].cpe.endswith("p:1.0:*:*:*:*:*:*:*")
