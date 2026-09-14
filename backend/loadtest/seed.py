"""
Seeds one real session + job + (reused) frame row in the real Supabase
project for the /generate load test, and writes their ids to seed_data.json
for locustfile.py to read.

Tagged clearly (session token prefixed "loadtest-") so the rows are easy to
find and delete afterward — see cleanup.py.
"""
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import client as db

SEED_FILE = Path(__file__).parent / "seed_data.json"


def main():
    token = "loadtest-" + secrets.token_urlsafe(16)
    db._client().table("sessions").insert({"token": token, "generations_used": 0}).execute()

    job_id = db.create_job(token, photo_r2_key="loadtest/fake.webp")

    frame = db._client().table("frames").select("frame_id").limit(1).execute().data[0]
    frame_id = frame["frame_id"]

    data = {"session_token": token, "job_id": job_id, "frame_id": frame_id}
    SEED_FILE.write_text(json.dumps(data, indent=2))
    print(f"Seeded: {data}")


if __name__ == "__main__":
    main()
