# Import Guide: Researcher Data Files

## Purpose

Researcher files are validated before they enter the real data folders. A file is never copied into `data/` first and checked later. Validation happens first, and only a file with a clean report is a candidate for the real data folders.

## The validation script

`scripts/validate_import.py` checks a file against the real Pydantic schemas. It is validation only. It never writes to `data/`, never overwrites a file, and never deletes anything.

Run it from the project root with the backend venv active:

python scripts\validate_import.py --type




Record types: `experiment`, `hardware`, `relationship`, `source`.

Examples:
python scripts\validate_import.py research\flex_experiments.json --type experiment
python scripts\validate_import.py research\flex_sources.json --type source
python scripts\validate_import.py research\hardware.csv --type hardware




Check source references against a sources file:
python scripts\validate_import.py research\flex_experiments.json --type experiment --sources research\flex_sources.json




Write the full report as JSON:
python scripts\validate_import.py research\flex_experiments.json --type experiment --report research\flex_experiments_report.json




## What it checks

- Every record matches the schema for its type (required fields, field types, enum values).
- Every record has a unique `id`. Duplicate ids are rejected.
- Numeric measurements must have a unit. A numeric value without a unit is rejected. A missing value is not the same as zero and is kept as missing.
- Measurement kind is kept as written: `measured`, `derived`, or `interpreted`. Nothing is assumed to be measured.
- When `--sources` is given, every `source_id` and `source_ids` reference must exist in that sources file. An unknown reference is rejected. Without `--sources`, source references are not checked, and the report does not claim they were.

## Exit codes and output

- Exit `0` and the word `VALID`: every record passed.
- Exit `1` and the word `INVALID`: at least one record failed. The output lists each problem as `Row <n> [<field>]: <error>`. Fix the file and run the script again.
- A missing file or an unreadable file also exits `1` with a plain message, not a traceback.

## File formats

JSON: a list of records.

```json
[
  {
    "id": "exp-flex-001",
    "name": "FLEX",
    "description": "Flame Extinguishment Experiment"
  }
]
CSV: one header row, one record per row. Column names are the field names.

Required fields per record type:

Experiment: id, name.
Hardware: id, name, hardware_type (facility, apparatus, component, instrument).
Relationship: id, experiment_id, hardware_id, relationship_type (used_in, housed_in, part_of, supports, produced_by).
Source: id, title. A doi must start with 10.. A url must start with http:// or https://.
Optional fields may be left out. Leaving a field out means "not documented". It is never filled in with a guessed value, and a missing value is never replaced with zero.

Source verification workflow
A source record is created with verification status unverified, which means "not yet reviewed".

A human reviewer checks the actual source (the report, paper, dataset, or page it points to) and then sets the status explicitly, either through the API (POST /api/v1/sources/{id}/verification) or by updating the record:

confirmed: the source was checked and supports what it is cited for.
partially_documented: the source was checked and supports only part of what it is cited for.
verification_failed: the source was checked and does not support what it is cited for.
unverified: not yet reviewed.
A source record existing never verifies a finding or a measurement on its own. A finding keeps its own verification status, independent of any source it cites. A source id appearing in a record is only a reference, not proof.

File organisation
Real research data lives only in data/<type>/: data/experiments/, data/hardware/, data/relationships/, data/sources/.
Test fixtures live only in backend/tests/fixtures/, and only when a test genuinely needs them.
Synthetic records live only inside test files, clearly labelled synthetic. They never go into data/.
Media lives only in media/<type>/.
Import reports live wherever the researcher writes them with --report. They never go into data/.
Safety rules
The script validates only. It does not import, copy, overwrite, or delete any real data file.
A file with a failed report is not placed into data/. Fix the file, re-run the script, and only use the file when the report says VALID.
Never edit a real data file to force a validation to pass. If the data and the schema disagree, the data or the schema needs a real fix, not a silent edit.
No fabricated NASA data is ever added to data/. Only records from a verified NASA source, checked by a reviewer, belong there.