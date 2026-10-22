"""Ontario posting review controls, research prototype, rules reviewed 2026-10-17.

Inputs are reviewed structured facts, not NLP guesses. Results are review findings,
not a legal compliance certificate. Unknown scope and ambiguous evidence abstain.
"""
from datetime import date, timedelta
import hashlib
import json
import math

RULE_VERSION = 'ON-2026.1-research'
EFFECTIVE = date(2026, 1, 1)


def _parse_date(value):
    """Accept explicit ISO local dates only; malformed evidence is unknown."""
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def _input_problem(record):
    if not isinstance(record, dict):
        return 'Each posting must be a JSON object.'
    posting_id = record.get('posting_id')
    if not isinstance(posting_id, str) or not posting_id.strip():
        return 'A nonempty string posting_id is required.'
    version = record.get('version')
    if type(version) is not int or version < 1:
        return 'A positive integer posting version is required; Boolean values are invalid.'
    return None


def _input_finding(reason):
    return {'rule': 'INPUT', 'status': 'review_required', 'evidence': reason}


def _finite_number(value):
    # Python integers are finite; avoid float conversion overflowing on large ints.
    return type(value) is int or (type(value) is float and math.isfinite(value))


def scope(record):
    if not isinstance(record, dict):
        return 'review_required'
    jurisdiction = record.get('jurisdiction')
    if jurisdiction == 'OTHER':
        return 'outside_scope'
    if jurisdiction != 'ON_ESA':
        return 'review_required'
    for field in ('ontario_employee_count', 'external_specific', 'crown_exempt', 'work_in_scope'):
        if record.get(field) is None:
            return 'review_required'
    count = record['ontario_employee_count']
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return 'review_required'
    if any(type(record[k]) is not bool for k in ('external_specific', 'crown_exempt', 'work_in_scope')):
        return 'review_required'
    if count < 25 or not record['external_specific'] or record['crown_exempt'] or not record['work_in_scope']:
        return 'outside_scope'
    return 'in_scope'


def review_posting(record):
    problem = _input_problem(record)
    if problem:
        return [_input_finding(problem)]
    findings = []
    def add(rule, status, evidence):
        findings.append({'rule': rule, 'status': status, 'evidence': evidence})
    status = scope(record)
    if status != 'in_scope':
        add('SCOPE', status, 'Check employer coverage, Ontario count and position scope.')
        return findings
    posted_on = _parse_date(record.get('posted_on'))
    if posted_on is None:
        add('POST_DATE', 'review_required', 'A valid posted_on date in YYYY-MM-DD format is required.')
        return findings
    if posted_on < EFFECTIVE:
        add('POST_DATE', 'outside_scope', 'Posting content predates 2026; interview notification is evaluated separately.')
        return findings
    # Annual CAD fixed salary only. Complex compensation and uncertain exemptions abstain.
    low, high = record.get('salary_low_cad'), record.get('salary_high_cad')
    complex_pay = record.get('complex_pay')
    if complex_pay is not False:
        add('PAY', 'review_required', 'Commission, hourly annualization or unknown compensation requires review.')
    elif (not _finite_number(low) or not _finite_number(high)
          or low < 0 or high < low):
        add('PAY', 'review_required', 'Finite, nonnegative numeric compensation in an ordered range is required before applying an exemption.')
    elif high > 200000:
        add('PAY', 'exempt', 'Expected annual salary range ends above CAD 200,000.')
    else:
        val = record.get('pay_disclosed')
        if type(val) is not bool:
            add('PAY_DISCLOSURE', 'review_required', 'Disclosure evidence missing.')
        elif not val:
            add('PAY_DISCLOSURE', 'flag', 'Expected fixed annual salary not disclosed.')
        if high - low > 50000:
            add('PAY_RANGE', 'flag', 'Expected range exceeds CAD 50,000.')
    ai = record.get('ai_used_for_selection')
    disclosure = record.get('ai_disclosed')
    if type(ai) is not bool or (ai and type(disclosure) is not bool):
        add('AI', 'review_required', 'Verify actual screening, assessment or selection use and disclosure.')
    elif ai and not disclosure:
        add('AI', 'flag', 'AI is used in selection but the posting disclosure is absent.')
    for field, rule, explanation, bad_value in [
        ('vacancy_disclosed', 'VACANCY', 'Statement of whether a vacancy exists is missing.', False),
        ('canadian_experience_required', 'CANADIAN_EXPERIENCE', 'Reviewed posting/application requires Canadian experience.', True),
        ('posting_version_archived', 'ARCHIVE_POSTING', 'Public posting version is absent from evidence archive.', False),
        ('application_archived', 'ARCHIVE_APPLICATION', 'Associated application form is absent from evidence archive.', False),
        ('linked_sources_archived', 'ARCHIVE_LINKS', 'Relevant linked material is absent from evidence archive.', False),
    ]:
        value = record.get(field)
        if type(value) is not bool:
            add(rule, 'review_required', 'Human-reviewed evidence is unknown.')
        elif value == bad_value:
            add(rule, 'flag', explanation)
    if not any(f['status'] in ('flag', 'review_required') for f in findings):
        add('CHECKED_RULES', 'no_flag', 'No findings in implemented checks; this is not a compliance certificate.')
    return findings


def notification(record, interviews, notices, as_of):
    if scope(record) != 'in_scope':
        return {'status': scope(record), 'due_on': None}
    def unknown(reason):
        return {'status': 'review_required', 'due_on': None, 'evidence': reason}
    problem = _input_problem(record)
    if problem:
        return unknown(problem)
    today = _parse_date(as_of)
    if today is None:
        return unknown('A valid as_of date in YYYY-MM-DD format is required.')
    if not isinstance(interviews, list) or not isinstance(notices, list):
        return unknown('Interview and notice evidence must each be a list.')
    qualifying = []
    for interview in interviews:
        if not isinstance(interview, dict):
            return unknown('Each interview event must be an object.')
        event_date = _parse_date(interview.get('date'))
        if event_date is None or interview.get('kind') not in ('interview', 'screening'):
            return unknown('Each event needs a valid date and a reviewed interview or screening kind.')
        if interview['kind'] == 'interview' and event_date <= today:
            qualifying.append(event_date)
    if not qualifying or max(qualifying) < EFFECTIVE:
        return {'status': 'outside_scope', 'due_on': None}
    last = max(qualifying)
    try:
        due = last + timedelta(days=45)
    except OverflowError:
        return unknown('The interview date is outside the supported deadline range.')
    valid = []
    for notice in notices:
        if not isinstance(notice, dict):
            return unknown('Each notice event must be an object.')
        notice_date = _parse_date(notice.get('date'))
        if notice_date is None or type(notice.get('decision_made')) is not bool:
            return unknown('Each notice needs a valid date and reviewed Boolean decision_made evidence.')
        if last <= notice_date <= today:
            valid.append(notice_date)
    earliest = min(valid) if valid else None
    if earliest is not None:
        result = 'in_time' if earliest <= due else 'late_notice'
    else:
        result = 'overdue' if today > due else ('due_today' if today == due else 'pending')
    return {'status': result, 'due_on': due.isoformat()}


def regressions(previous, current):
    for record in (previous, current):
        problem = _input_problem(record)
        if problem:
            return [_input_finding(problem)]
    if previous['posting_id'] != current['posting_id']:
        return [_input_finding('Version comparisons must refer to the same posting_id.')]
    old = {(f['rule'], f['status']) for f in review_posting(previous)}
    return [f for f in review_posting(current)
            if f['status'] in ('flag', 'review_required') and (f['rule'], f['status']) not in old]


def evidence_digest(record):
    try:
        payload = json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                             allow_nan=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
    except (TypeError, ValueError, UnicodeError):
        return None


def retention_review_after(removed_on):
    d = _parse_date(removed_on)
    if d is None or d.year > 9996:
        return None
    try:
        anniversary = d.replace(year=d.year + 3)
    except ValueError:
        anniversary = date(d.year + 3, 3, 1)
    # Conservative review day after the anniversary, not automatic deletion.
    try:
        return (anniversary + timedelta(days=1)).isoformat()
    except OverflowError:
        return None


def review_batch(records):
    if not isinstance(records, list):
        return [{'posting_id': None, 'version': None, 'rule_version': RULE_VERSION,
                 'sha256': None, 'findings': [_input_finding('Input must be a JSON list of postings.')]}]
    identities = {}
    for record in records:
        if _input_problem(record) is None:
            key = (record['posting_id'], record['version'])
            identities[key] = identities.get(key, 0) + 1
    results = []
    for record in records:
        problem = _input_problem(record)
        posting_id = record['posting_id'] if problem is None else None
        version = record['version'] if problem is None else None
        digest = evidence_digest(record) if isinstance(record, dict) else None
        findings = review_posting(record)
        extra = []
        if problem is None and identities[(posting_id, version)] > 1:
            extra.append(_input_finding('Duplicate posting_id/version identity; resolve before interpreting this batch.'))
        if digest is None and isinstance(record, dict):
            extra.append(_input_finding('Evidence cannot be hashed as strict JSON; check nonfinite numbers and unsupported values.'))
        if extra:
            findings = [f for f in findings if f['status'] != 'no_flag'] + extra
        results.append({'posting_id': posting_id, 'version': version,
                        'rule_version': RULE_VERSION, 'sha256': digest, 'findings': findings})
    return results


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text())
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f'Input could not be read as JSON: {exc}\n')
    results = review_batch(records)
    print(json.dumps(results, indent=2, allow_nan=False))
    # Output remains useful for review, but malformed input is not a successful run.
    invalid = any(f['rule'] in ('INPUT', 'POST_DATE') and f['status'] == 'review_required'
                  for result in results for f in result['findings'])
    if invalid:
        parser.exit(2)
