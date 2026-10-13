"""Admin control: --disable stops live clients; --enable grants seven days."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--enable", action="store_true")
    mode.add_argument("--disable", action="store_true")
    args = parser.parse_args()
    config = json.loads((Path(__file__).resolve().parents[1] / "config/google.json").read_text())
    state = {"protocol": 1, "enabled": args.enable,
             "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()}
    target = f'gs://{config["control_bucket"]}/{config["control_object"]}'
    with tempfile.TemporaryDirectory() as directory:
        payload = Path(directory) / "ai-control.json"
        payload.write_text(json.dumps(state))
        result = subprocess.run(["gcloud", "storage", "cp", str(payload), target,
                                 "--project", config["project"]],
                                capture_output=True, text=True, timeout=45)
        if result.returncode:
            parser.exit(2, "Control update failed; remote state not confirmed\n")
    print("AI enabled for seven days" if args.enable else "AI disabled remotely")


if __name__ == "__main__":
    main()
