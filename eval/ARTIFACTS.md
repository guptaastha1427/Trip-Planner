# Evaluation artifacts

Outputs are written to `eval/artifacts/` (gitignored). Each run creates a **new timestamped file**; nothing is overwritten in place.

## Refresh after hybrid retrieval

Hybrid lexical rerank is tracked as `retrieval_profile.profile_id = hybrid_rerank_v1` in new artifacts.

```bash
# Full baseline + auxiliary suites (recommended after retrieval tuning)
python3 -m eval.run_pipeline --refresh-baseline
# equivalent to:
python3 -m eval.run_pipeline --baseline --auxiliary --refresh-reason post_hybrid_retrieval
```

Older local files such as `evaluation_run_real_embeddings.json` or `evaluation_run_ci_smoke.json` are **pre-hybrid reference points** unless you generate a new `baseline_*.json` or `evaluation_run_*.json` with the current pipeline.

Each artifact includes:

- Top-level `evaluation_mode` (`heuristic_offline`, `llm_judge_live`, `ragas_library`, `mixed_live`)
- `retrieval_profile` (hybrid flags, chunking, embedding mode)
- `artifact_lineage` (refresh notes)
- Companion `baseline_<stamp>.csv` (same stem as JSON) when using `write_artifact`
