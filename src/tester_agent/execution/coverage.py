"""Разбор coverage.xml → {file_path: {покрытые строки}}."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_coverage_xml(path: str | Path) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    tree = ET.parse(path)
    for cls in tree.iter("class"):
        filename = cls.get("filename")
        if not filename:
            continue
        covered: set[int] = set()
        for line_el in cls.findall("./lines/line"):
            if int(line_el.get("hits", "0")) > 0:
                covered.add(int(line_el.get("number", "0")))
        result[filename] = covered
    return result
