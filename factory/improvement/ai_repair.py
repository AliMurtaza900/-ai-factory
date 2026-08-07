"""AI-assisted repair proposals with strict, bounded application semantics."""

from dataclasses import dataclass
import json

from ..providers.factory import configured_provider
from ..builder.project import GeneratedFile
from ..specs.agent_spec import AgentSpec


@dataclass(frozen=True)
class RepairProposal:
    path: str
    old_text: str
    new_text: str
    reason: str


class AIRepairPlanner:
    """Ask an available provider for a tiny text replacement, never arbitrary commands."""

    def __init__(self, provider=None):
        self.provider = provider

    def propose(self, spec: AgentSpec, files: list[GeneratedFile], failures: list[str]) -> list[RepairProposal]:
        provider = self.provider or configured_provider()
        file_context = "\n\n".join(f"FILE: {f.path}\n{f.content}" for f in files)
        prompt = f"""You are repairing a generated AI agent.
Goal: {spec.purpose}
Failures: {failures}
Files:\n{file_context}
Return ONLY JSON array. Each item must contain path, old_text, new_text, reason.
Only propose small literal text replacements. Do not add commands, shell code, secrets, URLs, or dependencies.
Return [] if you cannot identify a safe repair."""
        response = provider.generate(prompt, system="Return only safe JSON repair proposals.")
        data = json.loads(response.text)
        return [RepairProposal(str(x["path"]), str(x["old_text"]), str(x["new_text"]), str(x["reason"])) for x in data]

    @staticmethod
    def apply(files: list[GeneratedFile], proposals: list[RepairProposal]) -> list[GeneratedFile]:
        by_path = {f.path: f.content for f in files}
        for proposal in proposals:
            if proposal.path not in by_path or not proposal.old_text or proposal.old_text not in by_path[proposal.path]:
                continue
            by_path[proposal.path] = by_path[proposal.path].replace(proposal.old_text, proposal.new_text, 1)
        return [GeneratedFile(f.path, by_path[f.path]) for f in files]
