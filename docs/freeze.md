# Freeze and interpretation

The first repository commit fixed the schema, normalization semantics and
policy before dataset or fixture implementation. Data documents, labels and
raw checksums are committed before fixture construction. See `data/manifest.json`
and the two separate dataset-agent commits in the actual history.

These thresholds are an illustrative engineering policy. Zero critical field
errors is appropriate for demonstrating an invoice gate; it does not establish
that a real system with zero observed errors is risk-free. Forty synthetic
evaluation cases cannot estimate deployment error rates or cover every invoice.

Specification clarifications after the initial freeze preserve the original
normalization and thresholds. A candidate already compared with a baseline must
be compared to that same baseline content, so re-comparison cannot silently
replace the original rejection context. Rejecting JSON numeric overflow is input
validation, not a change to extraction labels or metric definitions.
