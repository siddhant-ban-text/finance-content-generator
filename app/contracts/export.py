"""Deterministic checked-in schema export; run with --out schemas/v1."""
import argparse
import json
from pathlib import Path
from app.contracts import common, execution

GROUPS = {
    "common.json": (common.ArtifactRef, common.Money, common.Percent, common.PercentagePoints, common.Usage, common.Principal),
    "execution.json": (execution.InputEnvelope, execution.OutputEnvelope, execution.ExecutionError),
}

def export_schemas(directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    for name, models in GROUPS.items():
        content = {"schema_version": "1.0", "models": {model.__name__: model.model_json_schema() for model in models}}
        (directory/name).write_text(json.dumps(content,sort_keys=True,indent=2)+"\n")
    return list(GROUPS)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    export_schemas(args.out)
