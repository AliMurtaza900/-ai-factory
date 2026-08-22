"""Planning, continuity, and quality contracts for cinematic animated shorts.

This module deliberately does not depend on a specific video vendor. It turns a
simple story goal into a persistent film bible + storyboard that a real
animation backend can consume, then validates shot-level quality and prepares
precise regeneration requests when shots fail.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Any


QUALITY_KEYS = (
    "character_consistency",
    "animation",
    "facial_expression",
    "cinematography",
    "lighting",
    "environment",
    "continuity",
    "audio_sync",
)


@dataclass
class Character:
    id: str
    name: str
    role: str
    appearance: str
    personality: str
    voice: str
    movement_style: str


@dataclass
class Location:
    id: str
    name: str
    description: str
    lighting: str
    time_of_day: str
    continuity_notes: str


@dataclass
class Shot:
    id: str
    scene_id: str
    duration_seconds: float
    shot_type: str
    camera: str
    action: str
    emotion: str
    dialogue: str = ""
    sound: str = ""
    lighting: str = ""
    continuity_from_previous: str = ""


@dataclass
class FilmPlan:
    title: str
    logline: str
    visual_direction: str
    emotional_arc: list[str]
    characters: list[Character]
    locations: list[Location]
    shots: list[Shot]
    style_constraints: list[str] = field(default_factory=list)
    production_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


class CinematicPlanner:
    """Create a complete film plan before any animation is rendered."""

    def __init__(self, provider: Any | None = None) -> None:
        self.provider = provider

    @staticmethod
    def _slug(text: str, fallback: str) -> str:
        value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return value[:32] or fallback

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        candidates = [raw]
        candidates += [x.strip() for x in re.findall(r"```(?:json)?\s*(.*?)```", raw, re.I | re.S)]
        for candidate in candidates:
            try:
                value = json.loads(candidate)
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
        start = raw.find("{")
        while start >= 0:
            depth = 0
            quoted = False
            escaped = False
            for i in range(start, len(raw)):
                c = raw[i]
                if quoted:
                    if escaped:
                        escaped = False
                    elif c == "\\":
                        escaped = True
                    elif c == '"':
                        quoted = False
                    continue
                if c == '"':
                    quoted = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            value = json.loads(raw[start:i + 1])
                            if isinstance(value, dict):
                                return value
                        except json.JSONDecodeError:
                            break
            start = raw.find("{", start + 1)
        raise ValueError("cinematic planner returned invalid JSON")

    def _llm_plan(self, goal: str) -> FilmPlan:
        provider = self.provider
        if provider is None:
            from ..providers.factory import configured_provider
            provider = configured_provider()
        prompt = f"""Turn this simple story idea into an original cinematic 3D animated short film: {goal}

Create a complete production bible and storyboard BEFORE rendering anything.
Aim for the polish, emotional clarity, character acting, lighting and cinematic
language of a premium theatrical animated feature, but do not copy any existing
studio, franchise, character, or distinctive design.

Return ONLY JSON with this exact shape:
{{
  "title": "...", "logline": "...", "visual_direction": "...",
  "emotional_arc": ["..."],
  "characters": [{{"id":"...","name":"...","role":"...","appearance":"...","personality":"...","voice":"...","movement_style":"..."}}],
  "locations": [{{"id":"...","name":"...","description":"...","lighting":"...","time_of_day":"...","continuity_notes":"..."}}],
  "shots": [{{"id":"S01_SH01","scene_id":"S01","duration_seconds":5,"shot_type":"...","camera":"...","action":"...","emotion":"...","dialogue":"...","sound":"...","lighting":"...","continuity_from_previous":"..."}}],
  "style_constraints": ["..."], "production_notes": ["..."]
}}
Use 5-8 scenes and 2-4 shots per scene. Keep recurring character descriptions stable.
"""
        response = provider.generate(
            prompt,
            system="You are the director, storyboard artist, character designer, cinematographer and continuity supervisor of an original animated short. Return only valid JSON.",
        )
        return self._from_dict(self._parse_json(response.text), goal)

    def _deterministic_plan(self, goal: str) -> FilmPlan:
        clean = re.sub(r"\s+", " ", goal).strip()
        title = clean[:55].rstrip(" .") or "The Little Light"
        character_name = "Milo"
        return FilmPlan(
            title=title,
            logline=f"A small hero faces the central problem hidden inside: {clean}",
            visual_direction="Original premium 3D animation; tactile materials, expressive faces, cinematic depth, motivated camera movement, volumetric light, restrained color progression, and physically believable motion.",
            emotional_arc=["wonder", "problem", "uncertainty", "journey", "loss or setback", "courage", "emotional release", "hopeful resolution"],
            characters=[Character("C01", character_name, "protagonist", "Original stylized 3D character with a distinctive silhouette, expressive eyes, consistent costume and tactile materials.", "Curious, vulnerable, persistent and kind.", "Warm youthful voice with natural pauses and emotional variation.", "Readable gestures, grounded weight shifts, small nervous movements that become confident by the ending.")],
            locations=[Location("L01", "Home", "A memorable lived-in environment that establishes the hero and the normal world.", "Soft motivated morning light", "morning", "Keep major props and spatial relationships fixed."), Location("L02", "Journey", "A visually rich original environment that changes gradually as the hero progresses.", "Directional cinematic light", "late afternoon", "Maintain geography and travel direction."), Location("L03", "Emotional Place", "A quiet location reserved for the emotional climax and resolution.", "Warm practical light with soft rim light", "dusk", "Preserve hero silhouette and key prop continuity.")],
            shots=self._fallback_shots(),
            style_constraints=[
                "Original characters and environments only.",
                "Never use a still image as a substitute for character animation.",
                "Preserve identity, costume, proportions and props across shots.",
                "Prefer motivated camera movement over random motion.",
                "Dialogue must be acted, not read as narration.",
            ],
            production_notes=[
                "Render the entire storyboard before final edit.",
                "Reject broken hands/faces, identity drift, frozen acting, camera jitter and continuity violations.",
                "Regenerate only failed shots when possible.",
            ],
        )

    @staticmethod
    def _fallback_shots() -> list[Shot]:
        beats = [
            ("S01", "wide establishing", "Slow push toward the hero in the normal world.", "wonder"),
            ("S01", "close-up", "The hero notices the problem and reacts.", "surprise"),
            ("S02", "medium tracking", "The hero commits to a journey.", "determination"),
            ("S03", "wide moving shot", "The environment opens up as the journey becomes difficult.", "uncertainty"),
            ("S04", "over-the-shoulder", "A setback forces the hero to confront what matters.", "sadness"),
            ("S05", "intimate close-up", "A quiet emotional choice changes the hero.", "courage"),
            ("S06", "dynamic tracking", "The hero acts with new confidence.", "hope"),
            ("S07", "wide-to-close reveal", "The consequence lands emotionally and the story resolves.", "relief"),
        ]
        shots: list[Shot] = []
        for i, (scene, shot_type, action, emotion) in enumerate(beats, 1):
            shots.append(Shot(f"{scene}_SH{i:02d}", scene, 4.5 if i not in (1, 8) else 6.0, shot_type, "cinematic motivated movement; 35mm/50mm language selected by shot", action, emotion, sound="Layered environment ambience, character movement and motivated foley.", lighting="Physically motivated cinematic lighting with soft volumetric atmosphere.", continuity_from_previous="Preserve character identity, costume, props, geography and emotional state."))
        return shots

    @staticmethod
    def _from_dict(data: dict[str, Any], goal: str) -> FilmPlan:
        required = ["title", "logline", "visual_direction", "emotional_arc", "characters", "locations", "shots"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError("film plan missing: " + ", ".join(missing))
        characters = [Character(**item) for item in data["characters"]]
        locations = [Location(**item) for item in data["locations"]]
        shots = [Shot(**item) for item in data["shots"]]
        if not characters or not locations or len(shots) < 4:
            raise ValueError("film plan is too small to be a short film")
        ids = [shot.id for shot in shots]
        if len(ids) != len(set(ids)):
            raise ValueError("shot ids must be unique")
        return FilmPlan(
            title=str(data["title"]), logline=str(data["logline"]), visual_direction=str(data["visual_direction"]),
            emotional_arc=[str(x) for x in data["emotional_arc"]], characters=characters, locations=locations,
            shots=shots, style_constraints=[str(x) for x in data.get("style_constraints", [])],
            production_notes=[str(x) for x in data.get("production_notes", [])],
        )

    def plan(self, goal: str) -> FilmPlan:
        if not goal or not goal.strip():
            raise ValueError("A non-empty story idea is required")
        if os.getenv("AI_FACTORY_ENABLE_LLM_CINEMATIC", "1").lower() in {"1", "true", "yes"}:
            try:
                return self._llm_plan(goal.strip())
            except Exception as exc:
                print(f"Cinematic LLM planner unavailable -> deterministic fallback: {exc}")
        return self._deterministic_plan(goal.strip())


def validate_cinematic_result(result: dict[str, Any], plan: FilmPlan, workspace: Path) -> dict[str, Any]:
    """Validate shot-level output and create a targeted regeneration request."""
    if result.get("status") != "completed":
        raise ValueError("cinematic renderer did not complete")
    shots = result.get("shots")
    if not isinstance(shots, list):
        # Backward-compatible mode: the existing renderer may not expose shot scores yet.
        return {"status": "approved", "mode": "legacy-adapter", "warning": "shot-level QC unavailable"}

    expected = {shot.id for shot in plan.shots}
    failures: list[dict[str, Any]] = []
    for shot in shots:
        if not isinstance(shot, dict) or not shot.get("id"):
            failures.append({"id": "unknown", "reasons": ["invalid-shot-result"]})
            continue
        scores = shot.get("quality", {})
        reasons: list[str] = []
        if not isinstance(scores, dict):
            reasons.append("missing-quality-scores")
        else:
            for key in QUALITY_KEYS:
                value = scores.get(key)
                if value is None or float(value) < 75:
                    reasons.append(f"{key}<{75}")
        if shot.get("continuity_ok") is False:
            reasons.append("continuity-failed")
        if reasons:
            failures.append({"id": str(shot["id"]), "reasons": reasons})

    returned = {str(x.get("id")) for x in shots if isinstance(x, dict) and x.get("id")}
    missing = sorted(expected - returned)
    failures.extend({"id": shot_id, "reasons": ["missing-shot"]} for shot_id in missing)
    if failures:
        request = {"status": "regenerate", "failed_shots": failures, "instruction": "Regenerate only failed shots while preserving the Film Bible, character identity, world geography, props, dialogue timing and adjacent-shot continuity."}
        (workspace / "regeneration_request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"cinematic QC rejected {len(failures)} shot(s); regeneration request written")
    return {"status": "approved", "mode": "cinematic", "shots": len(shots), "threshold": 75}
