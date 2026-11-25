from dataclasses import dataclass, field

from .checks import CheckResult
from .level import LevelVerdict


@dataclass
class ItemReport:
    path: str
    checks: list[CheckResult] = field(default_factory=list)
    level: LevelVerdict | None = None
    level_asked: bool = False  # the level check was attempted (it may have given no answer)

    @property
    def failed(self) -> bool:
        return any(not c.passed for c in self.checks)


def _status(check: CheckResult) -> str:
    return "SKIPPED" if check.skipped else "PASS" if check.passed else "FAIL"


def render_report(reports: list[ItemReport], warnings: list[str] | None = None) -> str:
    failed = sum(r.failed for r in reports)
    lines = ["# Item check report", "", f"{failed} of {len(reports)} Items failed.", ""]
    for warning in warnings or []:
        lines.append(f"> **Warning:** {warning}")
    if warnings:
        lines.append("")
    for report in reports:
        lines += [f"## `{report.path}` — {'FAIL' if report.failed else 'OK'}", ""]
        for check in report.checks:
            detail = f" — {check.detail}" if check.detail else ""
            lines.append(f"- **{check.name}**: {_status(check)}{detail}")
        if report.level is not None:
            v = report.level
            lines.append(
                f"- **level and playability (advisory)**: A2 level: {'yes' if v.a2_level else 'NO'}, "
                f"playable: {'yes' if v.playable else 'NO'}"
                + (f" — {v.comments}" if v.comments else "")
            )
        elif report.level_asked:
            lines.append("- **level and playability (advisory)**: no usable answer from the model")
        else:
            lines.append("- **level and playability (advisory)**: not run")
        lines.append("")
    return "\n".join(lines)
