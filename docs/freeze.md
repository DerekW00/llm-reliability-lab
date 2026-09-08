# Freeze and interpretation

The first repository commit fixed the schema, normalization semantics and
policy before dataset or fixture implementation. Data documents, labels and
raw checksums are committed before fixture construction. See `data/manifest.json`
and the two separate dataset-agent commits in the actual history.

These thresholds are an illustrative engineering policy. Zero critical field
errors is appropriate for demonstrating an invoice gate; it does not establish
that a real system with zero observed errors is risk-free. Forty synthetic
evaluation cases cannot estimate deployment error rates or cover every invoice.

The freeze records commit ordering, not authoring independence: the corpus was
written for this demonstration by the same effort that planned the fixture
scenarios, and `EVAL-02`'s rationale names the planned noncritical supplier error
outright. That label is still exactly what its own document says on the cited line,
and `docs/dataset.md` already states these are not independently annotated research
labels and not a blind held-out benchmark.

Specification clarifications after the initial freeze preserve the original
normalization and thresholds. A candidate already compared with a baseline must
be compared to that same baseline content, so re-comparison cannot silently
replace the original rejection context. Rejecting JSON numeric overflow is input
validation, not a change to extraction labels or metric definitions.

An integration coverage audit found that the initial spec had omitted the user's
duplicate-looking-document requirement. A separately checksummed two-case
development supplement supplies that edge case. It was added after construction
of the primary fixture files, before any demo scoring; it does not alter the
original 60-case files, their manifest, the evaluation labels or the policy.
This is a disclosed development coverage correction, not evaluation tuning.
