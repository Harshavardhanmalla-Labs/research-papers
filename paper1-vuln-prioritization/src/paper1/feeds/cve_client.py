"""CPE 2.3 parsing and version-range helpers.

Conservative implementation: this module performs *no* fuzzy product
mapping. CPEs that fail to parse exactly are reported as warnings, not
silently coerced. Version comparisons use a permissive numeric/string
ordering suitable for `versionStartIncluding` / `versionEndExcluding`
ranges as NVD publishes them.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CPEParseError",
    "ParsedCPE",
    "VersionRange",
    "cpe_to_product_key",
    "extract_affected_ranges",
    "normalize_cpe",
    "parse_cpe23",
    "version_in_range",
]


class CPEParseError(ValueError):
    """Raised when a string cannot be parsed as a CPE 2.3 URI."""


_CPE_FIELD_NAMES = (
    "prefix",  # "cpe"
    "version",  # "2.3"
    "part",  # a|o|h
    "vendor",
    "product",
    "version_field",
    "update",
    "edition",
    "language",
    "sw_edition",
    "target_sw",
    "target_hw",
    "other",
)


@dataclass(frozen=True)
class ParsedCPE:
    part: str
    vendor: str
    product: str
    version: str
    update: str
    edition: str
    language: str
    sw_edition: str
    target_sw: str
    target_hw: str
    other: str

    def as_canonical(self) -> str:
        """Reconstruct the canonical CPE 2.3 URI from parsed fields."""
        fields = [
            "cpe",
            "2.3",
            self.part,
            self.vendor,
            self.product,
            self.version,
            self.update,
            self.edition,
            self.language,
            self.sw_edition,
            self.target_sw,
            self.target_hw,
            self.other,
        ]
        return ":".join(fields)


def parse_cpe23(raw: str) -> ParsedCPE:
    """Parse a CPE 2.3 URI into structured fields.

    Raises CPEParseError on malformed input. Accepts the canonical
    13-field colon-separated form ``cpe:2.3:a:vendor:product:...``.
    """
    if not isinstance(raw, str) or not raw:
        raise CPEParseError(f"CPE must be a non-empty string, got {raw!r}")
    parts = raw.split(":")
    if len(parts) != len(_CPE_FIELD_NAMES):
        raise CPEParseError(
            f"CPE has {len(parts)} fields, expected {len(_CPE_FIELD_NAMES)}: {raw!r}"
        )
    if parts[0] != "cpe":
        raise CPEParseError(f"CPE prefix must be 'cpe', got {parts[0]!r}")
    if parts[1] != "2.3":
        raise CPEParseError(f"CPE version must be '2.3', got {parts[1]!r}")
    if parts[2] not in {"a", "o", "h", "*", "-"}:
        raise CPEParseError(f"CPE part must be a|o|h (or wildcard), got {parts[2]!r}")
    return ParsedCPE(
        part=parts[2],
        vendor=parts[3],
        product=parts[4],
        version=parts[5],
        update=parts[6],
        edition=parts[7],
        language=parts[8],
        sw_edition=parts[9],
        target_sw=parts[10],
        target_hw=parts[11],
        other=parts[12],
    )


def normalize_cpe(raw: str) -> str:
    """Parse and re-emit a CPE in canonical form. Raises on malformed input."""
    return parse_cpe23(raw).as_canonical()


def cpe_to_product_key(cpe: str) -> tuple[str, str]:
    """Return (vendor, product) lower-cased from a CPE 2.3 URI."""
    p = parse_cpe23(cpe)
    return p.vendor.lower(), p.product.lower()


# ---------------------------------------------------------------------------
# Version ranges
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VersionRange:
    cpe: str | None
    start_including: str | None = None
    start_excluding: str | None = None
    end_including: str | None = None
    end_excluding: str | None = None
    vulnerable: bool = True


def _split_version(v: str) -> list[Any]:
    """Split a version into a list of integers and strings for comparison."""
    parts: list[Any] = []
    cur = ""
    cur_is_digit: bool | None = None
    for ch in v:
        ch_is_digit = ch.isdigit()
        if cur and cur_is_digit != ch_is_digit:
            parts.append(int(cur) if cur_is_digit else cur)
            cur = ""
        cur += ch
        cur_is_digit = ch_is_digit
    if cur:
        parts.append(int(cur) if cur_is_digit else cur)
    return parts


def _compare_versions(a: str, b: str) -> int:
    """Permissive version comparison.

    Returns -1, 0, or 1. Splits each version into runs of digits and
    non-digits; compares pairwise. Integer-vs-string compares treat
    integers as smaller (pre-release ordering convention).
    """
    pa = _split_version(a)
    pb = _split_version(b)
    for x, y in zip(pa, pb, strict=False):
        if isinstance(x, int) and isinstance(y, int):
            if x != y:
                return -1 if x < y else 1
        elif isinstance(x, str) and isinstance(y, str):
            if x != y:
                return -1 if x < y else 1
        else:
            # Mixed: integers sort before strings.
            return -1 if isinstance(x, int) else 1
    if len(pa) != len(pb):
        return -1 if len(pa) < len(pb) else 1
    return 0


def version_in_range(
    version: str,
    *,
    start_including: str | None = None,
    start_excluding: str | None = None,
    end_including: str | None = None,
    end_excluding: str | None = None,
) -> bool:
    """Test whether `version` lies in the (semi-open) range bounds.

    Wildcards ('*' or '-') in `version` produce a False with no error;
    callers should treat wildcard versions as unknown and flag separately.
    """
    if not version or version in {"*", "-"}:
        return False
    if start_including is not None and _compare_versions(version, start_including) < 0:
        return False
    if start_excluding is not None and _compare_versions(version, start_excluding) <= 0:
        return False
    if end_including is not None and _compare_versions(version, end_including) > 0:
        return False
    if end_excluding is not None and _compare_versions(version, end_excluding) >= 0:
        return False
    return True


def extract_affected_ranges(node: dict[str, Any]) -> Iterator[VersionRange]:
    """Yield VersionRange for each cpeMatch entry under an NVD configurations node.

    Accepts an NVD JSON 2.0 ``configurations`` node element. Nested
    children (``nodes`` recursion) are traversed.
    """
    matches = node.get("cpeMatch", []) or []
    for m in matches:
        yield VersionRange(
            cpe=m.get("criteria"),
            start_including=m.get("versionStartIncluding"),
            start_excluding=m.get("versionStartExcluding"),
            end_including=m.get("versionEndIncluding"),
            end_excluding=m.get("versionEndExcluding"),
            vulnerable=bool(m.get("vulnerable", True)),
        )
    for child in node.get("children", []) or []:
        yield from extract_affected_ranges(child)
