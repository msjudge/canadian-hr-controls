# From Approval to Publication: Job Posting Governance in Ontario

**Manvir Singh Judge | HR Operations · HRIS · People Analytics**  
Independent research, developed with AI assistance. All operational records and financial assumptions are synthetic.

[Explore the dashboard](https://msjudge.github.io/canadian-hr-controls/) · [Research report](https://msjudge.github.io/canadian-hr-controls/report.pdf) · [Visual walkthrough](https://msjudge.github.io/canadian-hr-controls/screenshots.html) · [LinkedIn](https://www.linkedin.com/in/msjudge/)

## The HR question

I examined a talent-acquisition control gap: the approved requisition template may differ from the version a candidate sees. I built a Python prototype that reviews structured posting facts, preserves uncertainty for human review and compares findings across posting versions. Selected Ontario requirements effective in 2026 provide the scenario context.

## What I found

My synthetic fixture set contains nine versions across eight posting IDs: three flagged, two requiring review, two with no implemented flags and two outside the modeled scope. JOB-001 moves from an unflagged v1 to AI-disclosure and posting-archive findings in v2. All nine expected findings reproduce from the source.

## My interpretation

I would use this workflow to define version ownership, exception routing and an evidence-retention standard. A digest supports traceability but does not archive a posting. Deliberately constructed fixtures cannot estimate employer non-compliance, and this prototype does not certify legal compliance. HR/legal validation is required before deployment.

## What I implemented

Python was executed and verified. The Tableau-style dashboard and editor workspace are independently built browser replicas. Native Tableau or VS Code execution is not claimed.

The dashboard connects management findings to the detailed ledger or evidence register, source logic and research limitations. Captions explain each screenshot's analytical purpose. The report documents population, metric definitions, verification, limitations and the proposed next decision.

## Reproduce the study

Run `python3 verify.py` from this directory. The `analysis/` folder contains the executed implementation and frozen evidence. Serve `docs/` with a local static server or visit the live dashboard above. No paid hosting, database or API is required.

## Scope and authorship

This is my independent portfolio research, not work attributed to a current or former employer. Browser interfaces are clearly labelled replicas. Consult the report before interpreting any modeled financial or governance outcome.
