"""
Multi-source ingestion module for Performance Plus.

Responsible for normalising N ad-platform CSVs (each with its own currency and
column schema) into a single merged DataFrame ready for
``data.compute_campaign_agg()``.

Key design notes
----------------
- Zero UI-framework imports — this is a pure-pandas module. ``app.py`` calls it;
  ``ingest.py`` never calls back into ``app.py``, ``data.py``, or ``llm.py``
  (one-way dependency rule per Phase 9 D-13).
- The output column ``cost_usd`` holds the *reporting-currency* value, not
  necessarily USD.  The column is intentionally kept named ``cost_usd`` for
  compatibility with ``data.compute_campaign_agg()`` which reads that column
  directly.  A comment in ``ingest()`` restates this (Phase 9 D-12).

TODO Phase 10: ``compute_campaign_agg`` needs extension to sum source-prefixed
numeric columns (e.g. ``google_ads_clicks``, ``meta_ads_clicks``).  For Phase 9
the downstream LLM still receives a valid DataFrame, but per-platform numeric
breakdown remains in source-prefixed columns and is not yet aggregated.
"""

import difflib
import io

import pandas as pd

# ---------------------------------------------------------------------------
# Phase 9 D-10 — used as the canonical list for selectbox options and
# for error messages throughout the ingestion pipeline.
# ---------------------------------------------------------------------------
SUPPORTED_CURRENCIES: list[str] = [
    "USD",
    "EUR",
    "GBP",
    "CAD",
    "AUD",
    "JPY",
    "INR",
    "SGD",
]

# Static rates as of 2026-06-02 — replace with live FX API in v4+ (Phase 9 D-10)
# Each rate represents "1 unit of that currency expressed in USD".
# Example: EUR=1.08 means 1 EUR buys 1.08 USD.
FX_RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.26,
    "CAD": 0.74,
    "AUD": 0.65,
    "JPY": 0.0067,
    "INR": 0.012,
    "SGD": 0.74,
}

# Phase 9 D-06 — the four required fields every CRM CSV must supply,
# after the user applies their field mapping.
REQUIRED_CRM_FIELDS: list[str] = [
    "session_id",
    "lead_status",
    "projected_value",
    "sales_notes",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def convert_cost(amount: float, from_ccy: str, to_ccy: str) -> float:
    """Convert *amount* from *from_ccy* to *to_ccy* using the static FX_RATES.

    Parameters
    ----------
    amount:
        The monetary amount in the source currency.
    from_ccy:
        3-letter ISO 4217 code of the source currency (e.g. ``"EUR"``).
    to_ccy:
        3-letter ISO 4217 code of the target / reporting currency
        (e.g. ``"USD"``).

    Returns
    -------
    float
        ``amount * FX_RATES[from_ccy] / FX_RATES[to_ccy]``.
        When ``from_ccy == to_ccy`` the result equals ``amount`` exactly.

    Raises
    ------
    ValueError
        If either *from_ccy* or *to_ccy* is not in :data:`FX_RATES`.
    """
    for ccy in (from_ccy, to_ccy):
        if ccy not in FX_RATES:
            supported = ", ".join(SUPPORTED_CURRENCIES)
            raise ValueError(
                f"Unsupported currency: {ccy}. Supported: {supported}"
            )
    return amount * FX_RATES[from_ccy] / FX_RATES[to_ccy]


def auto_suggest_crm_columns(crm_columns: list[str]) -> dict[str, str | None]:
    """Suggest the best matching CRM CSV column for each required field.

    Uses :func:`difflib.get_close_matches` (cutoff=0.4) for fuzzy matching.
    This powers the auto-suggest UI in Plan 09-03 (Phase 9 D-05).

    Parameters
    ----------
    crm_columns:
        The list of column headers present in the uploaded CRM CSV.

    Returns
    -------
    dict[str, str | None]
        Mapping ``{required_field: best_match_or_None}`` for every field in
        :data:`REQUIRED_CRM_FIELDS`.
    """
    result: dict[str, str | None] = {}
    for field in REQUIRED_CRM_FIELDS:
        matches = difflib.get_close_matches(field, crm_columns, n=1, cutoff=0.4)
        result[field] = matches[0] if matches else None
    return result


# ---------------------------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------------------------

# Columns that are treated as "key" columns — they are added by ingest() itself
# and must NOT be source-prefixed.  Any other column in an ad-platform CSV is
# renamed "{source_slug}_{column}" before pd.concat to prevent collision when
# multiple platforms share the same column name (Phase 9 D-14).
_KEY_COLUMNS: frozenset[str] = frozenset(
    {"session_id", "campaign_id", "platform", "currency_code", "cost_usd"}
)


def ingest(
    platform_csvs: list[tuple[str, bytes, str, str]],
    crm_bytes: bytes,
    crm_field_map: dict[str, str],
    reporting_currency: str,
) -> pd.DataFrame:
    """Normalise N ad-platform CSVs and merge with CRM data.

    Parameters
    ----------
    platform_csvs:
        List of ``(platform_display_name, csv_bytes, currency_code,
        source_slug)`` tuples.  Each tuple represents one ad platform upload.

        - *platform_display_name* — human-readable label shown in the UI
          (e.g. ``"Google Ads"``).  Written to the ``platform`` column.
        - *csv_bytes* — raw CSV file bytes.  Entries where this is ``None``
          or empty bytes are silently skipped (partial-upload support).
        - *currency_code* — 3-letter ISO code of the cost column in this CSV
          (e.g. ``"EUR"``).  Must be in :data:`SUPPORTED_CURRENCIES`.
        - *source_slug* — stable lowercase prefix for non-key column names
          (e.g. ``"google_ads"`` → ``google_ads_clicks``).  The caller in
          ``app.py`` (Plan 09-03) supplies this so column naming stays stable
          across UI changes.

    crm_bytes:
        Raw CRM CSV file bytes.

    crm_field_map:
        Mapping from *standard field name* → *user CSV column name* for each
        of the four required fields in :data:`REQUIRED_CRM_FIELDS`.
        Example: ``{"session_id": "sid", "lead_status": "status", ...}``.

    reporting_currency:
        3-letter ISO code the user chose as their reporting currency
        (e.g. ``"USD"``).  All ``cost_local`` values from every platform are
        converted to this currency and written to the ``cost_usd`` column.

        NOTE (Phase 9 D-12): despite the column being named ``cost_usd``, the
        values represent the *reporting currency*, which may not be USD.  The
        column name is kept for compatibility with ``data.compute_campaign_agg()``.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame with at least these columns::

            session_id, campaign_id, platform, currency_code, cost_usd,
            {source_slug}_clicks, {source_slug}_impressions,
            {source_slug}_conversion_rate,
            lead_status, projected_value, sales_notes

        One row per (ad-platform session × matching CRM session).  A single
        ``session_id`` can appear in multiple rows if the session appeared in
        more than one ad platform.

    Raises
    ------
    ValueError
        - If *reporting_currency* is not in :data:`SUPPORTED_CURRENCIES`.
        - If any platform's *currency_code* is not in :data:`SUPPORTED_CURRENCIES`.
        - If all supplied *csv_bytes* entries are empty / ``None``.
        - If a column conflict (``_x`` / ``_y`` suffix) survives the merge
          — indicates a source-prefix misconfiguration.
        - If the CRM field mapping is incomplete or references a missing column.
    pd.errors.MergeError
        If the CRM CSV contains duplicate ``session_id`` values (``validate="m:1"``
        enforcement).
    """
    # ------------------------------------------------------------------
    # Step 1 — Validate reporting currency up front.
    # ------------------------------------------------------------------
    if reporting_currency not in SUPPORTED_CURRENCIES:
        supported = ", ".join(SUPPORTED_CURRENCIES)
        raise ValueError(
            f"Unsupported reporting currency: {reporting_currency}. "
            f"Supported: {supported}"
        )

    # ------------------------------------------------------------------
    # Step 2 — Normalise each ad-platform CSV.
    # ------------------------------------------------------------------
    normalised_dfs: list[pd.DataFrame] = []

    for platform_display_name, csv_bytes, currency_code, source_slug in platform_csvs:
        # Skip empty / None uploads (partial-upload support).
        if not csv_bytes:
            continue

        # 2a — Validate platform currency.
        if currency_code not in SUPPORTED_CURRENCIES:
            supported = ", ".join(SUPPORTED_CURRENCIES)
            raise ValueError(
                f"Unsupported currency: {currency_code}. Supported: {supported}"
            )

        # 2b — Parse CSV.
        df = pd.read_csv(io.BytesIO(csv_bytes))

        # 2c — Add system-injected columns (Phase 9 D-15).
        df["platform"] = platform_display_name
        df["currency_code"] = currency_code

        # 2d — Convert cost_local to reporting currency.
        # Output column is named cost_usd for compute_campaign_agg compat (D-12).
        df["cost_usd"] = df["cost_local"].apply(
            lambda v: convert_cost(v, currency_code, reporting_currency)
        )
        df = df.drop(columns=["cost_local"])

        # 2e — Source-prefix rename (Phase 9 D-14).
        # All non-key columns get prefixed with source_slug + "_" BEFORE concat
        # to prevent collision when multiple platforms share the same column name.
        rename_map = {
            col: f"{source_slug}_{col}"
            for col in df.columns
            if col not in _KEY_COLUMNS
        }
        df = df.rename(columns=rename_map)

        normalised_dfs.append(df)

    # ------------------------------------------------------------------
    # Step 3 — Guard: at least one non-empty platform is required.
    # ------------------------------------------------------------------
    if not normalised_dfs:
        raise ValueError(
            "ingest() requires at least one non-empty ad platform CSV. "
            "The app.py gate (Phase 9 D-04) should prevent this in normal usage."
        )

    # ------------------------------------------------------------------
    # Step 4 — Concatenate all normalised platform DataFrames.
    # ------------------------------------------------------------------
    combined_ads = pd.concat(normalised_dfs, ignore_index=True)

    # ------------------------------------------------------------------
    # Step 5 — Load, rename, and validate the CRM CSV.
    # ------------------------------------------------------------------
    crm_df = pd.read_csv(io.BytesIO(crm_bytes))

    # Build the rename mapping from user column names → standard field names.
    # The crm_field_map dict is keyed by standard field, valued by user column.
    rename_map_crm = {
        user_col: standard_field
        for standard_field, user_col in crm_field_map.items()
        if user_col  # skip any falsy (unmapped) entry
    }

    # Validate completeness: every required field must map to a real column.
    for standard_field in REQUIRED_CRM_FIELDS:
        user_col = crm_field_map.get(standard_field)
        if not user_col or user_col not in crm_df.columns:
            raise ValueError(
                f"CRM field mapping incomplete or refers to missing column: "
                f"{standard_field} → {user_col!r}"
            )

    crm_df = crm_df.rename(columns=rename_map_crm)

    # Keep only the 4 standard fields — extra CRM columns are Phase 10 scope
    # (see CONTEXT.md "Deferred Ideas" and Phase 9 D-07).
    crm_df = crm_df[REQUIRED_CRM_FIELDS]

    # ------------------------------------------------------------------
    # Step 6 — Inner merge with validate="m:1" (Phase 9 D-14 + ARCH §1).
    # validate="m:1" catches duplicate session_ids in the CRM CSV without
    # blocking the intentional ad-side fan-out (one session in multiple
    # platforms).
    # ------------------------------------------------------------------
    merged = pd.merge(
        combined_ads,
        crm_df,
        on="session_id",
        how="inner",
        validate="m:1",
    )

    # ------------------------------------------------------------------
    # Step 7 — Post-merge collision assertion (Phase 9 D-14).
    # Source-prefix renaming should have prevented any _x/_y suffixes.
    # If any survive, it means a non-key column was not prefixed — surface
    # this as a clear error rather than silently propagating malformed data.
    # ------------------------------------------------------------------
    bad_cols = [
        c for c in merged.columns if c.endswith("_x") or c.endswith("_y")
    ]
    if bad_cols:
        raise ValueError(
            f"Column name conflict after merge: {bad_cols}. "
            "Source-prefix renaming missed a column; check platform CSV schemas."
        )

    return merged
