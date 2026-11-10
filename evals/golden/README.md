# Golden dataset starter

Use JSONL, one example per line. The file `starter_examples.jsonl` contains illustrative examples only; replace or expand them with adjudicated, source-grounded examples before using them as a release gate.

Required metadata:
- `example_id`
- `agent_name`
- `dataset_version`
- `split` (`dev`, `holdout`, `prod_regression`)
- `input`
- `reference`
- `labels`
- `severity`
- `source_refs`
- `adjudication`

Never tune prompts on `holdout`. Keep event-level leakage out of the split. Do not store full copyrighted article text.
