"""Seed AP Psychology (course_id 17) curriculum-specific error types.

Loads the four LLM-generated, admin-accepted error types from the offline
generation run (``results/error_types_psychology_20260408_083352.json``,
model ``gemini-3.1-pro-preview``) into ``generated_error_types``. These are the
same rows the live ``error_type_generation`` save flow would write, mirroring
``ErrorTypeGenerationRepository.save_reviewed_types``:

  - ``course_id``       = 17  (AP Psychology — confirmed via the ``course`` table)
  - ``curriculum_name`` = "AP Psychology"  (the ``course.name`` the save flow uses)
  - ``subject_area``    = "Psychology"  (from the generation run)
  - ``source``          = "llm",  ``status`` = "accepted"
  - ``created_by``      = the generating model, for provenance

The ``ErrorTypeResolver`` reads these for course 17 and merges them with the
hardcoded behavioural types, so AP Psychology error analysis gains four
curriculum-specific, non-behavioural (content) error types.

``rationale`` is a required NOT-NULL column, but this generation run predates the
``rationale`` field on ``GeneratedErrorTypeItem``, so the source JSON omits it.
Each rationale below is derived directly from that run's own
``context_summary`` (``common_mistake_patterns`` / ``subject_nature``) — it is
documentation-only metadata; the resolver never reads it for classification or
display (it only reads label/description/fix/detection_criteria).

Idempotent: ``upgrade`` deletes any prior llm-sourced rows for these four keys on
course 17 before inserting, so a re-apply does not duplicate. ``downgrade``
removes exactly these four rows.

Revision ID: 030
Create Date: 2026-06-18
"""

import sqlalchemy as sa

from alembic import op

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


_COURSE_ID = 17
_CURRICULUM_NAME = "AP Psychology"
_SUBJECT_AREA = "Psychology"
_CREATED_BY = "gemini-3.1-pro-preview"


# Verbatim label/description/fix/detection_criteria from the generation run's
# ``accepted_error_types``; ``rationale`` derived from its ``context_summary``.
ERROR_TYPES: list[dict[str, str]] = [
    {
        "error_type_key": "TERMINOLOGY_CONFUSION",
        "label": "Terminology Confusion",
        "description": (
            "The student confuses two closely related psychological terms, often "
            "selecting the exact opposite or a 'twin' concept (e.g., proactive vs. "
            "retroactive interference)."
        ),
        "fix": (
            "Create comparison charts or Venn diagrams for easily confused pairs of "
            "terms, focusing specifically on the single key feature that "
            "distinguishes them."
        ),
        "detection_criteria": (
            "Triggered when distractor_analysis explicitly flags the chosen wrong "
            "answer as a commonly confused related term or the inverse concept. "
            "Often occurs on questions with moderate peer_accuracy where one "
            "specific distractor draws the majority of incorrect responses."
        ),
        "rationale": (
            "AP Psychology is terminology-dense and pairs many near-identical "
            "constructs (proactive vs. retroactive interference, negative "
            "reinforcement vs. punishment); confusing such twin terms is a "
            "documented top mistake pattern for this exam."
        ),
    },
    {
        "error_type_key": "COLLOQUIAL_BIAS",
        "label": "Everyday Language Bias",
        "description": (
            "The student applies the everyday, conversational definition of a word "
            "rather than its strict scientific or psychological definition."
        ),
        "fix": (
            "When learning vocabulary, explicitly note how the psychological "
            "definition differs from how the word is used in everyday life (e.g., "
            "'punishment', 'reliability')."
        ),
        "detection_criteria": (
            "Identified when distractor_analysis shows the chosen option relies on "
            "a layman's or non-scientific interpretation of a term. The student's "
            "overall_proficiency may be high, but they miss questions requiring "
            "strict operational definitions."
        ),
        "rationale": (
            "AP Psychology requires strict operational definitions, yet students "
            "routinely fall back on everyday meanings of words like 'reliability', "
            "'validity', or 'punishment' — a recognised source of error on this "
            "curriculum."
        ),
    },
    {
        "error_type_key": "RESEARCH_DESIGN_ERROR",
        "label": "Research Design Error",
        "description": (
            "The student misidentifies components of a study (like independent vs. "
            "dependent variables) or draws inappropriate conclusions (like assuming "
            "causation from a correlational study)."
        ),
        "fix": (
            "Always identify the research method (experiment, survey, observation) "
            "first before answering questions about variables or conclusions."
        ),
        "detection_criteria": (
            "Triggered when distractor_analysis flags a failure to distinguish "
            "between research methods or variable types. This pattern will appear "
            "across various topic_names (not just the intro unit) since research "
            "methods are integrated throughout the course."
        ),
        "rationale": (
            "The redesigned AP Psychology exam emphasises scientific practices — "
            "interpreting data, research methods, and variables — so misreading "
            "study design (e.g., inferring causation from correlation) recurs "
            "across all units, not just the intro."
        ),
    },
    {
        "error_type_key": "APPLICATION_MISMATCH",
        "label": "Application Error",
        "description": (
            "The student selects an answer that contains a true psychological fact "
            "or definition, but fails to correctly apply it to the specific "
            "scenario presented in the question."
        ),
        "fix": (
            "Underline the specific behavior or situation in the prompt and ensure "
            "your chosen answer directly explains that exact scenario, not just the "
            "general topic."
        ),
        "detection_criteria": (
            "Detected when distractor_analysis shows the student picked a factually "
            "correct definition that does not fit the prompt's scenario. Typically "
            "associated with higher difficulty questions and average or "
            "above-average time_taken, showing the student read the options but "
            "failed to map them to the context."
        ),
        "rationale": (
            "The exam shifts away from memorisation toward applying concepts to "
            "specific scenarios (notably the FRQs); selecting a true-but-unapplied "
            "fact and 'dropping the application point' is a primary failure mode."
        ),
    },
]

_ERROR_TYPE_KEYS = [et["error_type_key"] for et in ERROR_TYPES]


def upgrade() -> None:
    conn = op.get_bind()

    # Idempotent re-apply: clear any prior llm-sourced rows for these keys first.
    _delete_seeded_rows(conn)

    insert_stmt = sa.text(
        "INSERT INTO generated_error_types "
        "(course_id, curriculum_name, subject_area, error_type_key, label, "
        " description, fix, detection_criteria, rationale, source, status, "
        " created_by) "
        "VALUES (:course_id, :curriculum_name, :subject_area, :error_type_key, "
        " :label, :description, :fix, :detection_criteria, :rationale, 'llm', "
        " 'accepted', :created_by)"
    )
    params = [
        {
            "course_id": _COURSE_ID,
            "curriculum_name": _CURRICULUM_NAME,
            "subject_area": _SUBJECT_AREA,
            "created_by": _CREATED_BY,
            **et,
        }
        for et in ERROR_TYPES
    ]
    conn.execute(insert_stmt, params)  # one batched executemany roundtrip


def downgrade() -> None:
    _delete_seeded_rows(op.get_bind())


def _delete_seeded_rows(conn) -> None:
    """Delete the four seeded llm-sourced rows for course 17 (named params only)."""
    stmt = sa.text(
        "DELETE FROM generated_error_types "
        "WHERE course_id = :course_id AND source = 'llm' "
        "AND error_type_key IN :keys"
    ).bindparams(sa.bindparam("keys", expanding=True))
    conn.execute(stmt, {"course_id": _COURSE_ID, "keys": _ERROR_TYPE_KEYS})
