"""Committee ingestion is disabled until an authoritative membership source exists.

The previous implementation assigned officials to committees using a hash of
their names. Those links were fabricated and must not be regenerated.
"""


def ingest_committees():
    print(
        "Committee ingestion is NOT_IMPLEMENTED: no verified official "
        "membership source is configured. No assignments were created."
    )
    return 0


if __name__ == "__main__":
    ingest_committees()
