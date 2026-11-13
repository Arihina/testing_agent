"""Тесты парсера coverage.xml."""

from tester_agent.execution.coverage import parse_coverage_xml


def test_parse_coverage_xml(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text(
        """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="/x/service.py" name="service.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
            <line number="3" hits="2"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )
    coverage = parse_coverage_xml(xml)
    assert coverage == {"/x/service.py": {1, 3}}
