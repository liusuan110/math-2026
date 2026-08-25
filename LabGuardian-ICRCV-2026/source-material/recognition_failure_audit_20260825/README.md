# Recognition Failure Audit — 2026-08-25

This directory is a self-contained evidence package for the real-image recognition audit performed against LabGuardian-Server commit `5d78845b`.

## Contents

- `images/`: the nine input JPEG files, renamed to match their case IDs.
- `raw/`: one complete `/api/v1/pipeline/run` response per image.
- `manifest.json`: request settings, input hashes, model paths and model SHA-256 hashes.
- `summary.json`: machine-readable per-case summary derived from the raw responses.
- `correction_summary.json`: bounded three-port annotation experiment on `board_1_summing`.
- `paper_failure_cases_20260825.csv`: compact table for analysis and plotting.
- `paper_recognition_failure_storyline_20260825.md`: extended Chinese interpretation and paper-story notes.
- `ICRCV_INTEGRATION_NOTE.md`: instructions for using these cases without changing the current ICRCV paper's visual-reconstruction scope.
- `figures/recognition_failure_triptych.png`: representative standard, missed-object and class-confusion cases.

## Reproduction identity

- Server commit: `5d78845b`
- Endpoint: `POST /api/v1/pipeline/run`
- Request: `conf=0.25`, `iou=0.5`, `imgsz=960`
- Component model SHA-256: `c6da8b6669d23bb23e9dcc5df3e039c8f8190d1be299d291e073c9523126a8a9`
- Pin model SHA-256: `2b06f0d8f8d84b533757d758718307e98ab283274589579ae2962e9afb629205`

The API reported `model_version=dev` and `rule_version=dev`; therefore the commit, hashes and request parameters above are the authoritative run identity.

## Evidence boundary

Expected component counts were manually checked from the nine images. Exact pin-to-hole and topology ground truth was not annotated. These cases support qualitative failure analysis and hypothesis formation, but they are not a random test set and must not be reported as overall model accuracy.

The generated figure and all numerical summaries can be traced back to the raw JSON responses. Keep the images, raw responses, manifest and summary together when moving this package.
