# SWE-bench Verified-40 Results

## Overview
This folder contains the results of running the SWE-bench `verified-40` benchmark using our agent.

- `generation/`: contains the generation traces for each task
- `generation/preds.json`: final combined predictions for all 40 tasks
- `gemini__gemini-2.5-flash.eval.json`: final evaluation results

---

## Execution Strategy

Due to API rate limits (HTTP 429: RESOURCE_EXHAUSTED) from the Vertex AI model, it was not possible to run all 40 tasks in a single execution.

To address this, the benchmark was executed in **8 batches**, each containing 5 tasks:

- Batch 1: tasks 0–5
- Batch 2: tasks 5–10
- Batch 3: tasks 10–15
- Batch 4: tasks 15–20
- Batch 5: tasks 20–25
- Batch 6: tasks 25–30
- Batch 7: tasks 30–35
- Batch 8: tasks 35–40

Each batch was run independently to avoid interruptions caused by rate limiting.

---

## Result Aggregation

After running all batches:

- The individual `preds.json` files from each batch were merged into a single file:
  `generation/preds.json`
- This merged file contains predictions for all 40 tasks.
- A final evaluation was performed on the merged predictions to produce:
  `gemini__gemini-2.5-flash.eval.json`

---

## Final result

The agent resolved 22 out of 40 tasks

This exceeds the required threshold of 21 resolved tasks.

---

## Notes

- All generation traces are included so results can be inspected or reproduced.
- Since the benchmark was executed in batches due to API rate limits, the included log and exit status files correspond to a representative batch run.
- Renamed batch log files to minisweagent_batch*.log to distinguish logs from different verified-40 batch runs.
