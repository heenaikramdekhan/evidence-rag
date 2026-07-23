# Sample Evidence Handling Policy (demo document)

This is a placeholder document so the pipeline works end-to-end before you add
your own corpus. Replace everything in `data/raw_docs/` with your real files.

## 1. Chain of Custody

Every item of evidence must be logged with a unique identifier at the moment of
collection. The log records the collector's name, the date and time of
collection, and the location. Any transfer of custody must be signed by both the
releasing and receiving parties.

## 2. Storage

Physical evidence is stored in a tamper-evident sealed container in a
temperature-controlled room. Digital evidence is stored as a write-once copy,
and a cryptographic hash (SHA-256) of the original is recorded before analysis.

## 3. Retention

Evidence related to an open case is retained until the case is formally closed
and all appeal windows have expired. The default retention period after closure
is seven years, unless a court order specifies otherwise.

## 4. Access Control

Only authorized investigators listed on the case may access the evidence.
Each access event is recorded in the custody log, including the reason for
access. Remote access to digital evidence is prohibited.

## 5. Disposal

After the retention period, evidence is disposed of by a two-person team. The
disposal is witnessed, documented, and the custody log is closed with a final
signature.
