# AI Factory

An autonomous AI system that designs, builds, tests, deploys, and improves other AI agents and automated systems.

## Current production architecture

The repository now contains the original agent-generation Factory plus a production execution layer designed for long-running content/video jobs.

### Factory core

- Agent specifications and project materialization
- Multi-agent team generation
- Provider abstraction with caching and fallback
- Evaluation and regression testing
- Autonomous improvement and guarded revision flow
- Artifact manifests and standalone generated-system validation
- GitHub publishing helpers

### Production execution layer

`factory.production` adds the missing operational layer:

- **Durable jobs** — JSON-backed state survives process/server restarts.
- **Stage checkpoints** — completed stages are skipped when a job resumes.
- **Bounded retries** — transient production failures are retried without infinite loops.
- **Parallel stages** — independent stages can run concurrently.
- **Quality gates** — video artifacts and upload results are validated before completion.
- **Video adapter contract** — integrates an existing video generator/uploader without coupling the Factory to one vendor.
- **Feedback store** — records views, CTR, retention and engagement for later optimization.
- **CLI** — runs a resumable production job from one command.

## Integrating an existing video system

The existing video generator/uploader can be connected through `CommandVideoAdapter`.

Set:

```bash
export AI_FACTORY_VIDEO_COMMAND="python /path/to/your_video_system.py"
```

The command receives `GOAL` and `WORKSPACE` environment variables and must print a JSON object such as:

```json
{
  "status": "completed",
  "video": "video.mp4",
  "title": "Example title",
  "description": "Example description",
  "video_id": "youtube-id"
}
```

Then run:

```bash
python -m factory.production "Create today's best video about AI automation"
```

The Factory persists the job, retries failed production, validates the rendered artifact, validates the upload result, and can resume from the last completed stage.

## CI

The repository has separate CI coverage for the Factory and the production execution layer. The production gate compiles the new modules and runs the complete example regression suite.

## Security and reliability

Production code never requires API keys to be written into generated artifacts. Provider failures are isolated through the provider abstraction, and production jobs use bounded retries plus durable checkpoints rather than restarting the whole workflow after every failure.
