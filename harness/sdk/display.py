"""display.py — Rich live terminal display for the CodeCompass SDK experiment runner.

Shows current trial progress, tool call log, and overall experiment statistics.
"""
from __future__ import annotations

from typing import Optional

from rich import box
from rich.console import Console, Group as RichGroup
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class ExperimentDisplay:
    """Live terminal display for the CodeCompass experiment.

    Usage:
        display = ExperimentDisplay(total_trials=270)
        with display:
            display.set_current_trial("23", "C", 2, "g3")
            display.on_tool_call(1, "read_file", {"file_path": "app/db/base.py"}, "...")
            display.update_overall(1, "C", "g3", 1.0)
    """

    def __init__(
        self,
        total_trials: int = 270,
        completed_initial: int = 0,
        use_live: bool = True,
    ):
        self.total_trials = total_trials
        self.completed = completed_initial
        self.use_live = use_live
        self._live: Optional[Live] = None

        # Current trial state
        self.task_id = "--"
        self.condition = "--"
        self.run_num = "--"
        self.group = "--"
        self.status = "IDLE"
        self.tool_rows: list[tuple[int, str, str]] = []
        self.langfuse_url = ""

        # Per-condition / per-group ACS tracking
        self._cond_group_acs: dict[str, dict[str, list[float]]] = {
            c: {"g1": [], "g2": [], "g3": []} for c in ["A", "B", "C"]
        }
        self._cond_completed: dict[str, int] = {"A": 0, "B": 0, "C": 0}

    # --- Context manager ---

    def __enter__(self) -> "ExperimentDisplay":
        if self.use_live:
            self._live = Live(
                self._render(),
                console=console,
                refresh_per_second=4,
                transient=False,
            )
            self._live.__enter__()
        return self

    def __exit__(self, *args) -> None:
        if self._live:
            self._live.__exit__(*args)

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    # --- State updates ---

    def set_current_trial(
        self, task_id: str, condition: str, run_num: int, group: str
    ) -> None:
        self.task_id = task_id
        self.condition = condition
        self.run_num = str(run_num)
        self.group = group
        self.tool_rows = []
        self.langfuse_url = ""
        self._refresh()

    def set_status(self, status: str) -> None:
        self.status = status
        self._refresh()

    def on_tool_call(
        self, step: int, tool_name: str, tool_input: dict, tool_result: str
    ) -> None:
        """Called after each tool execution to update the display."""
        file_arg = (
            tool_input.get("file_path")
            or tool_input.get("pattern")
            or tool_input.get("query", "")[:50]
            or tool_input.get("command", "")[:50]
            or ""
        )
        self.tool_rows.append((step, tool_name, str(file_arg)[:60]))
        self._refresh()

    def update_overall(
        self, completed: int, condition: str, group: str, acs: float
    ) -> None:
        """Update overall experiment progress after a trial completes."""
        self.completed = completed
        self._cond_completed[condition] += 1
        if group in self._cond_group_acs[condition]:
            self._cond_group_acs[condition][group].append(acs)
        self._refresh()

    def set_langfuse_url(self, url: str) -> None:
        self.langfuse_url = url
        self._refresh()

    # --- Rendering ---

    def _status_style(self) -> str:
        base = self.status.split("(")[0].strip()
        return {
            "RUNNING": "green",
            "DONE": "bright_green",
            "FAILED": "red",
            "ERROR": "red",
            "RATE LIMIT": "yellow",
            "IDLE": "dim",
        }.get(base, "white")

    @staticmethod
    def _bar(n: int, total: int, width: int = 20) -> str:
        if total <= 0:
            return "░" * width
        filled = int(width * n / total)
        return "█" * filled + "░" * (width - filled)

    def _render(self) -> Panel:
        style = self._status_style()

        # --- Trial header ---
        header = Text()
        header.append("Task: ", style="bold")
        header.append(f"task_{self.task_id}  ", style="cyan")
        header.append("Condition: ", style="bold")
        header.append(f"{self.condition}  ", style="yellow")
        header.append("Run: ", style="bold")
        header.append(f"{self.run_num}  ", style="white")
        header.append(f"[{self.group.upper()}]", style="dim")

        status_line = Text()
        status_line.append("● ", style=style)
        status_line.append(self.status, style=f"bold {style}")

        # --- Tool call table ---
        tool_table = Table(
            box=box.SIMPLE, show_header=True, padding=(0, 1), expand=False
        )
        tool_table.add_column("Step", style="dim", width=5, justify="right")
        tool_table.add_column("Tool", style="cyan", width=34)
        tool_table.add_column("File / Query", style="white", width=55)

        for row in self.tool_rows[-8:]:
            tool_table.add_row(str(row[0]), row[1], row[2])

        # --- Overall progress ---
        per_cond = self.total_trials // 3
        overall = Text()
        overall.append(
            f"Overall:  {self.completed}/{self.total_trials}  "
            f"{self._bar(self.completed, self.total_trials)}  "
            f"{100 * self.completed // self.total_trials if self.total_trials else 0}%\n"
        )

        cond_line = Text()
        for cond in ["A", "B", "C"]:
            count = self._cond_completed[cond]
            sym = "✓" if count >= per_cond else ("↻" if count > 0 else "·")
            cond_line.append(f"  {cond}: {count}/{per_cond} {sym}  ")

        # --- Group ACS breakdown ---
        group_line = Text()
        for g in ["g1", "g2", "g3"]:
            group_line.append(f"  {g.upper()}: ", style="dim")
            for c in ["A", "B", "C"]:
                vals = self._cond_group_acs[c][g]
                if vals:
                    mean = sum(vals) / len(vals)
                    group_line.append(f"{c}={mean:.0%} ")

        # --- Langfuse URL ---
        url_line = Text()
        if self.langfuse_url:
            url_line.append("Langfuse: ", style="dim")
            url_line.append(self.langfuse_url, style="blue underline")

        return Panel(
            RichGroup(
                header,
                status_line,
                Text(""),
                tool_table,
                Text(""),
                overall,
                cond_line,
                group_line,
                url_line,
            ),
            title="[bold blue]CodeCompass Experiment — SDK Runner[/bold blue]",
            border_style="blue",
        )
