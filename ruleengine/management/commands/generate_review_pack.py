"""Generates the tax editor's review pack: one numbered item per
parameter, strategy, and authority, each with its values, primary-source
link, and the machine pre-check evidence — so professional sign-off is a
read-and-approve exercise, item by item."""

import datetime

from django.core.management.base import BaseCommand

from ruleengine.editorial import precheck

PACK_PATH = "docs/RULE_BASE_REVIEW_PACK.md"


def _fmt_payload(payload, indent=0):
    pad = "  " * indent
    lines = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}- {key}:")
                lines.extend(_fmt_payload(value, indent + 1))
            else:
                lines.append(f"{pad}- {key}: **{value:,}**" if isinstance(value, (int, float)) and not isinstance(value, bool)
                             else f"{pad}- {key}: **{value}**")
    elif isinstance(payload, list):
        for item in payload:
            lines.extend(_fmt_payload(item, indent))
    return lines


class Command(BaseCommand):
    help = "Write the editorial review pack to docs/RULE_BASE_REVIEW_PACK.md."

    def handle(self, *args, **options):
        report = precheck()
        n = 0
        lines = [
            "# Rule-base review pack — editorial sign-off",
            "",
            f"Generated {datetime.date.today():%d %B %Y}. "
            f"Machine pre-check: **{report['failures']} failed checks** across "
            f"{len(report['parameters'])} parameters, {len(report['strategies'])} strategies, "
            f"{len(report['authorities'])} authorities.",
            "",
            "**How to approve:** read each numbered item; the primary source is one",
            "click away. Reply YES to approve all items, or list the item numbers you",
            "question. Your approval is recorded as the §5.6 editorial review on every",
            "rule-base release, with your name and the date.",
            "",
            "---",
            "## A. Tax parameters (the rates and thresholds the engine uses)",
            "",
        ]
        for parameter in report["parameters"]:
            n += 1
            lines.append(f"### {n}. {parameter['label']}  \n`{parameter['key']}` — {parameter['domain']} — release {parameter['release']} — effective {parameter['effective']}")
            lines.extend(_fmt_payload(parameter["payload"]))
            for name, ok, detail in parameter["checks"]:
                lines.append(f"- {'PASS' if ok else '**FAIL**'} — {name}{f' ({detail})' if detail else ''}")
            for evidence in parameter["source_evidence"]:
                lines.append(f"- Source cross-reference: {evidence}")
            lines.append("")

        lines += ["---", "## B. Strategies (the planning advice, with legal basis)", ""]
        for strategy in report["strategies"]:
            n += 1
            lines.append(f"### {n}. {strategy['name']}  \n`{strategy['code']}` — {strategy['domain']} — risk **{strategy['risk']}**, timeframe {strategy['timeframe']}")
            lines.append(f"> {strategy['explanation']}")
            for citation, uri, status in strategy["authorities"]:
                lines.append(f"- Authority: [{citation}]({uri}) ({status})")
            for name, ok, detail in strategy["checks"]:
                lines.append(f"- {'PASS' if ok else '**FAIL**'} — {name}{f' ({detail})' if detail else ''}")
            lines.append("")

        lines += ["---", "## C. Authority registry (every citation, verified fetchable)", ""]
        for authority in report["authorities"]:
            n += 1
            lines.append(f"### {n}. [{authority['citation']}]({authority['uri']}) — {authority['type']}")
            lines.append(f"> {authority['extract']}")
            for name, ok, detail in authority["checks"]:
                lines.append(f"- {'PASS' if ok else '**FAIL**'} — {name}{f' ({detail})' if detail else ''}")
            lines.append("")

        lines += [
            "---",
            "## Sign-off",
            "",
            "By approving, the reviewing professional confirms they have read each",
            "item, spot-checked values against the linked primary sources where",
            "judgement required it, and accept editorial responsibility for this",
            "rule-base content under §5.6 of the architecture document.",
            "",
            "| Item range | Reviewer | Decision | Date |",
            "|---|---|---|---|",
            f"| 1–{n} | _(name)_ | _(YES / exceptions)_ | _(date)_ |",
            "",
        ]
        with open(PACK_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.stdout.write(self.style.SUCCESS(
            f"{PACK_PATH}: {n} numbered items, {report['failures']} machine-check failures."
        ))
