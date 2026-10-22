# Version-aware Ontario hiring controls

Run `python3 analysis/controls.py analysis/postings.json` from the repository root. The JSON output carries a rule version, content hash and review findings. No external systems are contacted.

Inputs are deliberately structured reviewed facts. `ontario_employee_count` is the reviewed count on the original posting date across the employer's Ontario locations. `work_in_scope` and `jurisdiction` are reviewed legal-scope decisions. `canadian_experience_required` covers the posting and associated application form. False for `linked_sources_archived` means relevant linked material is missing; true also applies where there is no relevant linked material. The actual documents are not archived by this prototype.

The annual compensation branch supports fixed CAD salary only. Commission, piecework, hourly annualization and unknown expected pay require review. A high endpoint above CAD 200,000 takes the compensation exception; exactly CAD 200,000 does not. A range exceeding CAD 50,000 is flagged when that exception does not apply. These controls implement selected rules, not all employment or human-rights obligations.

## Rule to test traceability

| Rule | Evidence field | Representative verification |
|---|---|---|
| Coverage | jurisdiction, Ontario count, work scope, Crown exemption | 24/25 threshold, unknown/type-invalid input, other jurisdiction |
| Compensation | expected annual salary and disclosure | exactly/above 200000, exactly 50000 width, unknown compensation |
| AI disclosure | actual use in selection and disclosure | missing disclosure regression; unknown AI use abstains |
| Canadian experience | reviewed requirement in posting/application | true produces a flag |
| Records | posting version, application, linked material | missing public-version evidence creates a regression |
| Interview notice | interview type/date and dated notice content | preliminary screen excluded, last interview reset, day 45/46, truthful no-decision update, late notice |
| Provenance | canonical record SHA-256 and rule version | key-order invariant hash |

The notification helper accepts one candidate/posting pair at a time. The caller is responsible for grouping correctly; do not mix candidates or requisitions. It uses ISO local dates, not raw UTC timestamps. Malformed dates, event structure or notice evidence return `review_required` with a reason. Scope is reviewed separately from posting date so pre-2026 postings with 2026 interviews can still be evaluated.

## Publication input guards

Posting IDs must be nonempty strings and versions positive integers, excluding Boolean values. Missing or invalid IDs, dates and duplicate posting/version identities receive explicit review findings. Salary values must be finite numbers: nulls, numeric strings, Booleans, NaN and infinity cannot establish a compensation exemption or clear a check. A malformed record does not prevent valid records in the same batch from being reviewed. Inputs that cannot be represented as strict JSON receive a null evidence hash and an input finding.

The command prints reviewable JSON and exits with status 2 when input/identity/date problems are detected; unreadable or malformed JSON also exits 2 with a concise error. An exit status of zero only means the input run completed: business flags, unknown scope and compensation requiring review still need human attention. The retention helper returns null for invalid or unsupported dates, meaning no review date could be calculated; it never deletes evidence. These guards do not replace a complete production schema or legal review.

## Demonstration in VS Code

Open this independent project folder. Run `python3 verify.py` in the terminal, or use the supplied verification task. With Python and the VS Code Python debugger installed, set a breakpoint at the salary exception or scope threshold. Use the supplied Inspect posting controls launch configuration, then compare version 1 and 2 in `analysis/findings.json`. Native debugging has not been performed in this delivery. Explain how unknown information differs from a flag and from an explicit out-of-scope result.

This is a research implementation, not a live ATS integration or automatic legal determination. Read the Ontario primary sources in SOURCES.md before a real deployment and obtain qualified review of scope, deadlines, retention and any changed rules.
