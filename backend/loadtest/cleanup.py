"""Deletes the disposable load-test session, its generation_tasks, and its
events rows from the real Supabase project. Run after a load test session."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import client as db

SEED_FILE = Path(__file__).parent / "seed_data.json"


def main():
    seed = json.loads(SEED_FILE.read_text())
    token = seed["session_token"]

    tasks = db._client().table("generation_tasks").delete().eq("session_token", token).execute()
    events = db._client().table("events").delete().eq("distinct_id", token).execute()
    job = db._client().table("jobs").delete().eq("job_id", seed["job_id"]).execute()
    session = db._client().table("sessions").delete().eq("token", token).execute()

    print(f"Deleted {len(tasks.data or [])} generation_tasks, {len(events.data or [])} events, "
          f"{len(job.data or [])} job, {len(session.data or [])} session for {token}")


if __name__ == "__main__":
    main()
