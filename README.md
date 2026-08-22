# AI Factory

An autonomous AI system that designs, builds, tests, deploys, and improves AI agents and automated systems — now with a production pipeline for original cinematic 3D animated short films.

## Cinematic animated-film pipeline

The production layer no longer has to treat a video as a slideshow of independent AI images. A story idea is compiled into a persistent film plan before rendering:

`story idea -> film bible -> character/world continuity -> full storyboard -> shot rendering -> voice/dialogue -> music/SFX -> shot QC -> targeted regeneration -> final edit -> YouTube`

The cinematic planner creates:

- Original characters with stable appearance, personality, voice and movement style.
- Persistent locations, lighting, time-of-day and continuity notes.
- A complete shot-by-shot storyboard with camera, action, emotion, dialogue, sound and lighting.
- Cinematic direction focused on expressive 3D animation, motivated camera movement and professional lighting.
- Explicit constraints preventing character drift and still-image slideshow behavior.

### Automatic bad-shot regeneration

A cinematic renderer may return per-shot quality scores for:

`character_consistency, animation, facial_expression, cinematography, lighting, environment, continuity, audio_sync`

Every score must be at least `75`. Failed shots create `regeneration_request.json` and the render stage retries. The next renderer attempt receives the exact failed shot IDs and reasons so it can regenerate only what is broken while preserving adjacent-shot continuity.

## Renderer contract

The existing video generator/uploader remains the backend. Set:

```bash
export AI_FACTORY_VIDEO_COMMAND="python /path/to/your_video_system.py"
```

In cinematic mode the command receives:

- `GOAL` — original story idea.
- `WORKSPACE` — durable job workspace.
- `CINEMATIC_MODE=1` — tells the backend to use the animated-film pipeline.
- `FILM_PLAN_PATH` — complete `film_plan.json` produced before rendering.
- `REGENERATION_REQUEST_PATH` — present when a previous render failed shot-level QC.

The backend must print one JSON object. A cinematic result should look like:

```json
{
  "status": "completed",
  "video": "video.mp4",
  "title": "Original animated short",
  "description": "...",
  "video_id": "youtube-id",
  "shots": [
    {
      "id": "S01_SH01",
      "continuity_ok": true,
      "quality": {
        "character_consistency": 92,
        "animation": 88,
        "facial_expression": 90,
        "cinematography": 91,
        "lighting": 94,
        "environment": 89,
        "continuity": 93,
        "audio_sync": 90
      }
    }
  ]
}
```

If `shots` is omitted, the adapter stays backward-compatible with the existing renderer but can only perform artifact-level QC; it cannot automatically judge individual shots.

## Run

```bash
python -m factory.production "A lonely young inventor builds a tiny flying machine to reunite with a lost friend"
```

The job state and film plan are persisted, so interrupted production can resume without rebuilding completed stages.

## Important creative constraint

Use premium theatrical animation as a quality reference, but all generated stories, characters, worlds, costumes and designs must be original. Do not copy existing studio characters, franchises or proprietary assets.

## Existing Factory capabilities

The repository also retains the original agent-generation Factory, provider abstraction, evaluation/regression testing, autonomous improvement, artifact manifests, GitHub publishing helpers, durable production jobs, retries, checkpoints and feedback storage.
