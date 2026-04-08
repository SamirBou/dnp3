from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_relationship import Relationship
from app.utility.base_parser import BaseParser
import re


GROUP_HEADER_RE = re.compile(r"^Group(\d+)Var\d+:")
DATA_ROW_RE = re.compile(r"^\s*(\d+)\s+\|")


class Parser(BaseParser):
    def parse(self, blob):
        relationships = []
        for facts in self._parse_group_sections(blob):
            for mp in self.mappers:
                source = facts.get(mp.source)
                target = facts.get(mp.target)

                if mp.edge and (source is None or target is None):
                    continue

                if not mp.edge:
                    relationships.append(
                        Relationship(
                            source=Fact(mp.source, source),
                            edge=None,
                            target=Fact(mp.target, None),
                        )
                    )
                else:
                    relationships.append(
                        Relationship(
                            source=Fact(mp.source, source),
                            edge=mp.edge,
                            target=Fact(mp.target, target),
                        )
                    )
        return relationships

    def _parse_group_sections(self, blob):
        sections = []
        current_group = None
        indices = []

        for line in self.line(blob):
            header_match = GROUP_HEADER_RE.match(line.strip())
            if header_match:
                if current_group is not None and indices:
                    sections.append(self._build_facts(current_group, indices))
                current_group = header_match.group(1)
                indices = []
                continue

            row_match = DATA_ROW_RE.match(line)
            if row_match and current_group is not None:
                indices.append(int(row_match.group(1)))

        if current_group is not None and indices:
            sections.append(self._build_facts(current_group, indices))

        return sections

    @staticmethod
    def _build_facts(group, indices):
        return {
            "dnp3.data.group": group,
            "dnp3.data.start": str(min(indices)),
            "dnp3.data.end": str(max(indices)),
        }
