from __future__ import annotations

from pathlib import Path

from src.analytics import load_execution_data, write_outputs
from src.generate_data import build_execution_dataset


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data" / "synthetic_execution_data.csv"

    if not data_path.exists():
        dataset = build_execution_dataset()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(data_path, index=False)

    frame = load_execution_data(data_path)
    write_outputs(frame, root)
    print(f"Analytics outputs refreshed under {root / 'results'} and {root / 'figures'}")


if __name__ == "__main__":
    main()
