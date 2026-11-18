# DefectLens

**Evidence-Verified Atomic Diagnosis of Audio-Video Generation Failures**

[![Project Page](https://img.shields.io/badge/Project_Page-DefectLens-76559c)](https://xuanhaochang.github.io/DefectLens/)
[![Evaluation App](https://img.shields.io/badge/Live_App-Evaluate_Clip-2b6cb0)](https://xuanhaochang.github.io/DefectLens/eval/)
[![Dataset](https://img.shields.io/badge/Hugging_Face-DefectLens--H3-ffcc4d)](https://huggingface.co/datasets/XuanhaoChang/DefectLens-H3)
[![Tests](https://github.com/XuanhaoChang/DefectLens/actions/workflows/tests.yml/badge.svg)](https://github.com/XuanhaoChang/DefectLens/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-slate.svg)](LICENSE)

Generated audio-video can look convincing while violating several user requirements at once—each requiring different visual, acoustic, or textual evidence to verify. **DefectLens** is a tool-augmented evaluation agent that retrieves individual requirement violations as **atomic defect records** and attaches inspectable spatiotemporal locations (`time_range`, `keyframe_sec`, and normalized `bbox`).

Its central rule is **evidence-first admission**: model proposals remain candidates until grounded by modality-appropriate media observations, and unavailable or failed signals are explicitly recorded as `not_evaluable` rather than treated as “no defect.”

- **Project Page & Video Overview:** [xuanhaochang.github.io/DefectLens](https://xuanhaochang.github.io/DefectLens/)
- **Interactive Evaluation Console:** [xuanhaochang.github.io/DefectLens/eval](https://xuanhaochang.github.io/DefectLens/eval/)
- **Public Benchmark Dataset:** [XuanhaoChang/DefectLens-H3 on Hugging Face](https://huggingface.co/datasets/XuanhaoChang/DefectLens-H3)

---

## Key Capabilities

- **Evidence Amortization Across 10 Checking Dimensions:** A shared `EvaluationContext` acquires visual frames/crops, SenseVoice ASR + constrained CTC speech scores, CAM++ speaker voiceprints, RapidOCR text readings, OpenCV motion cues, stream metadata, and AVBench/SyncNet lip-sync signals once, reusing them across related requirement checks.
- **Modality-Specific Verification:** Constrained CTC likelihoods compare expected vs. recognized dialogue on local audio segments; targeted crop/frame review gates OCR text error candidates; motion/physics gates examine local visual continuity; synchronization decisions require supporting offset and confidence evidence.
- **Source-Aware Consolidation & Grounding:** Preserves independent requirement violations (e.g., forbidden subtitle presence vs. wrong subtitle wording) along with their temporal intervals, representative keyframes, and bounding boxes.
- **Auditable Execution Contracts:** Exports structured issue predictions plus full JSONL traces (`classic_checks`, `tool_results`, evidence strength, and stage usage).

## Architecture Overview

```text
Generation prompt + reference images + generated audio-video
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
      Visual Agent        Auralis       AVBench / SyncNet
   (frames, contact    (SenseVoice CTC,   (face-track AV
    sheets, crops)    CAM++, RapidOCR)   synchronization)
            └────────────────┼────────────────┘
                             ▼
         Shared EvidenceContext + 10 Classic Checks
      (candidate → supported / deterministic / not_evaluable)
                             ▼
            Source-Aware Consolidation & Grounding
                             ▼
       Atomic Issue Records (CSV / JSON) + JSONL Audit Log
```

| Checking Dimension | Primary Evidence Signals |
| --- | --- |
| **1. Subject Identity** | Reference images, timestamped frames, contact sheets, high-res crops |
| **2. Entity Count & Spatial Layout** | Timestamped frames, contact sheets, crops |
| **3. Hard Instruction Compliance** | Visual observations, `ffprobe` duration & resolution metadata |
| **4. Motion & Physical Continuity** | Contact sheets, crops, OpenCV frame-diff / histogram / optical flow |
| **5. Subtitles, Text, Logos & Watermarks** | RapidOCR boxes, ASR-OCR temporal alignment, targeted pixel verification |
| **6. Visual & Temporal Artifacts** | Timestamped frames, crops, local OpenCV temporal diagnostics |
| **7. Dialogue & Speaker Binding** | SenseVoice transcription, local constrained CTC scoring, CAM++ clusters |
| **8. Voice Characteristics** | SenseVoice acoustic attributes, CAM++ speaker consistency, FFmpeg segments |
| **9. Audio Quality & Noise** | Audio stream inspection and segment diagnostics |
| **10. AV & Lip Synchronization** | Face-track AVBench / SyncNet offset and confidence records |

See [`docs/architecture.md`](docs/architecture.md) for component boundaries and typed evidence contracts.

---

## Benchmark Snapshot & Dataset

On the 189-clip human-annotated audio-video diagnosis benchmark (670 reference defect events across Seedance and MiniMax H3 Turbo), **DefectLens** improves both defect event retrieval and end-to-end spatiotemporal grounding over direct multimodal evaluators:

| Method | Event Precision ↑ | Event Recall ↑ | Event F1 ↑ | Mean tIoU ↑ | Joint Localization Recall ↑ |
| --- | ---: | ---: | ---: | ---: | ---: |
| **DefectLens** | 0.750 | **0.619** | **0.679** | **0.540** | **0.510** |
| GPT-5.5 | 0.793 | 0.479 | 0.597 | 0.408 | 0.376 |
| Seed-Lite | 0.656 | 0.452 | 0.535 | 0.418 | 0.133 |
| Qwen Omni | 0.583 | 0.482 | 0.528 | 0.354 | 0.228 |
| Gemini Flash | **0.831** | 0.345 | 0.487 | 0.301 | 0.257 |

The public **DefectLens-H3** subset (generated clips, ordered reference images, generation requests, and human-verified atomic defect annotations with timestamps, keyframes, and bounding boxes) is available on Hugging Face:

```python
import json
from huggingface_hub import hf_hub_download

gt_path = hf_hub_download(
    "XuanhaoChang/DefectLens-H3",
    "annotations/gt.jsonl",
    repo_type="dataset",
)
records = [json.loads(line) for line in open(gt_path, encoding="utf-8")]
print(records[0]["sample_id"], records[0]["issues"])
```

---

## Quick Start

Clone the repository with submodules and run the deterministic unit test suite (requires no model weights or remote API calls):

```bash
git clone --recurse-submodules https://github.com/XuanhaoChang/DefectLens.git
cd DefectLens
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p 'test_*.py'
```

Runtime components maintain isolated dependency boundaries:

```bash
# Parent process: orchestration, OCR, and tabular I/O
python -m pip install -r requirements-audio-agent.txt

# Isolated worker environment: AVBench / SyncNet and SenseVoice
python -m pip install -r third_party/AVBench/requirements.txt
python -m pip install -r requirements-avbench.txt
python -m pip install -r requirements-sensevoice.txt
```

> **Note:** Model-heavy stages additionally require a compatible PyTorch/CUDA runtime, LatentSync, and local SyncNet/S3FD checkpoints. DefectLens never auto-downloads weights during tests or setup.

## Configuration

Copy the environment template into `.env.local` (ignored by Git):

```bash
cp .env.example .env.local
```

Configure an OpenAI-compatible multimodal Chat Completions endpoint:

- `AVAGENT_API_KEY`
- `AVAGENT_API_URL`
- `AVAGENT_VISUAL_MODEL`

Optional specialist model overrides and local checkpoint paths are documented in [`.env.example`](.env.example).

## Running an Evaluation

The main CLI entry point is `run_avagent.py` (input CSV schema shown in [`examples/input.example.csv`](examples/input.example.csv)):

```bash
# Validate paths with a single-sample smoke run first
python run_avagent.py \
  --input-csv examples/input.example.csv \
  --limit 1 \
  --output-csv output/smoke/predictions.csv \
  --run-log output/smoke/run.jsonl

# Full evaluation with isolated AVBench/SyncNet worker
python run_avagent.py \
  --input-csv input/gt.csv \
  --output-csv output/demo/predictions.csv \
  --run-log output/demo/run.jsonl \
  --latentsync-root /path/to/LatentSync \
  --avbench-syncnet-ckpt /path/to/syncnet_v2.model \
  --avbench-python /path/to/avbench/python
```

To run the standalone direct visual/multimodal baseline without specialist tool branches, use `run_visual_baseline.py`.

## Repository Layout

```text
agents/                  Specialist orchestration and modality-specific evidence gates
agents/classic_checks/   Typed contracts and ten issue-oriented checking dimensions
av_eval/                 Dataset I/O, audit logging, routing, CLI, and web API modules
configs/                 Runtime prompts and non-secret configuration
docs/                    Architecture and web deployment documentation
examples/                Minimal, non-private input CSV examples
paper_site/              Project page static source (deployed to GitHub Pages)
scripts/                 Evaluation helpers, review export, and smoke checks
tests/                   Deterministic unit and static-contract test suite
third_party/AVBench/     Upstream AVBench Git submodule
tools/                   FFmpeg media ops, ASR, RapidOCR, and speech-subtitle alignment
web_app/                 Single-clip interactive evaluation frontend
run_avagent.py           Main DefectLens evaluation entry point
run_visual_baseline.py   Standalone direct multimodal evaluator baseline
```

## Contributing & Security

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines and pull-request checks. Please report security issues privately following [`SECURITY.md`](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
