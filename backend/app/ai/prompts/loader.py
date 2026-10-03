"""Prompt loader and manager tracking versioned agent prompts."""

from __future__ import annotations

from pathlib import Path

PROMPT_VERSION = "2026.10.1"


class PromptManager:
    """Loads and compiles modular system prompts, guidelines, and few-shots."""

    def __init__(self, prompts_dir: Path | str | None = None) -> None:
        if prompts_dir is None:
            self.prompts_dir = Path(__file__).resolve().parent
        else:
            self.prompts_dir = Path(prompts_dir)

    @property
    def version(self) -> str:
        """Current semantic prompt version string."""
        return PROMPT_VERSION

    def get_complete_system_prompt(self, include_few_shots: bool = True) -> str:
        """Alias for get_system_prompt."""
        return self.get_system_prompt(include_few_shots=include_few_shots)

    def get_system_prompt(self, include_few_shots: bool = True) -> str:
        """Assemble the complete system prompt for the agent."""
        system_file = self.prompts_dir / "system.md"
        tools_policy_file = self.prompts_dir / "tools_policy.md"
        response_style_file = self.prompts_dir / "response_style.md"

        sections: list[str] = []

        if system_file.exists():
            sections.append(system_file.read_text(encoding="utf-8").strip())
        if tools_policy_file.exists():
            sections.append(tools_policy_file.read_text(encoding="utf-8").strip())
        if response_style_file.exists():
            sections.append(response_style_file.read_text(encoding="utf-8").strip())

        if include_few_shots:
            few_shots_dir = self.prompts_dir / "few_shots"
            if few_shots_dir.exists():
                shot_texts: list[str] = []
                for shot_file in sorted(few_shots_dir.glob("*.md")):
                    shot_texts.append(shot_file.read_text(encoding="utf-8").strip())
                if shot_texts:
                    sections.append(
                        "## Reference Few-Shot Examples\n\n" + "\n\n---\n\n".join(shot_texts)
                    )

        return "\n\n---\n\n".join(sections)
