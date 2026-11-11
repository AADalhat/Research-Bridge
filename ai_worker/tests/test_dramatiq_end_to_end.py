import time
import pytest
from pathlib import Path
from dramatiq import Worker

import broker
from tasks import extract_pdf_metadata

TEST_PDF = Path(r"C:\Users\DELL 3520\Desktop\ai worker\Research_Bridge1.2.pdf")

def test_dramatiq_redis_end_to_end():
    """
    Spins up a Dramatiq Worker connected to Redis (Memurai),
    dispatches an extraction task to the queue, and retrieves the verified result from Redis.
    """
    b = broker.get_broker()
    worker = Worker(b, worker_threads=2)
    worker.start()

    try:
        # Enqueue task
        msg = extract_pdf_metadata.send(
            file_path=str(TEST_PDF),
            mode="digital",
            max_pages=15
        )

        assert msg.message_id is not None

        # Wait for worker to consume from Redis and store result
        result = msg.get_result(block=True, timeout=15000)

        assert result is not None
        assert result["classification"] == "digital"
        assert result["pages_processed"] == 2
        assert result["status"] in ["completed", "EXTRACTION_STALLED"]
        assert result["output_file"] is not None
        assert Path(result["output_file"]).exists()

        print("\nVerified End-to-End Dramatiq + Redis Execution:")
        print(f"  Message ID: {msg.message_id}")
        print(f"  Job ID:     {result['job_id']}")
        print(f"  Status:     {result['status']}")
        print(f"  Output:     {result['output_file']}")
    finally:
        worker.stop()

