"""
Phase 7 — Landing Page UI Polish: Nyquist gap-fill tests.

All tests are structural (file reads, string/regex matching, AST inspection).
No subprocess npm/next calls, no network, no Streamlit runtime.

PROJECT_ROOT is derived from this file's parent's parent so the test is
relocatable without touching any implementation file.
"""

import ast
import re
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP_PY = PROJECT_ROOT / "app.py"
UI_HELPERS_PY = PROJECT_ROOT / "ui_helpers.py"
LANDING = PROJECT_ROOT / "landing"
COMPONENTS = LANDING / "components"
GLOBALS_CSS = LANDING / "app" / "globals.css"
LAYOUT_TSX = LANDING / "app" / "layout.tsx"


# ---------------------------------------------------------------------------
# GAP 1 — UI-03: BRANDED_HEADER_HTML constant in app.py
# ---------------------------------------------------------------------------

def test_app_defines_BRANDED_HEADER_HTML_constant():
    """app.py must define a module-level constant named BRANDED_HEADER_HTML."""
    source = APP_PY.read_text()
    tree = ast.parse(source)
    constant_names = [
        tgt.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for tgt in node.targets
        if isinstance(tgt, ast.Name)
    ]
    assert "BRANDED_HEADER_HTML" in constant_names, (
        "app.py does not define a module-level constant BRANDED_HEADER_HTML"
    )


def test_BRANDED_HEADER_HTML_contains_required_strings():
    """BRANDED_HEADER_HTML must include the product name, tagline, and back-link."""
    source = APP_PY.read_text()
    required = [
        "⚡ Performance Plus",
        "AI-powered budget decisions from your CRM notes",
        "← Back to site",
        'href="/"',
    ]
    for fragment in required:
        assert fragment in source, (
            f"BRANDED_HEADER_HTML in app.py is missing required fragment: {fragment!r}"
        )


def test_app_calls_st_markdown_with_BRANDED_HEADER_HTML():
    """app.py must call st.markdown(BRANDED_HEADER_HTML, ...) to render the header."""
    source = APP_PY.read_text()
    assert "st.markdown(BRANDED_HEADER_HTML" in source, (
        "app.py does not call st.markdown(BRANDED_HEADER_HTML, ...)"
    )


def test_old_st_title_and_st_write_removed():
    """The legacy st.title + st.write pair must not appear in app.py."""
    source = APP_PY.read_text()
    assert 'st.title("Performance Plus")' not in source, (
        'app.py still contains st.title("Performance Plus") — should be replaced by BRANDED_HEADER_HTML'
    )
    assert 'st.write("Autonomous Semantic Attribution Engine")' not in source, (
        'app.py still contains st.write("Autonomous Semantic Attribution Engine") — should be replaced'
    )


# ---------------------------------------------------------------------------
# GAP 2 — UI-04: st.expander per-campaign loop in app.py
# ---------------------------------------------------------------------------

def test_app_has_for_c_in_result_campaigns():
    """app.py must iterate over result.campaigns for the expander layout."""
    source = APP_PY.read_text()
    assert "for c in result.campaigns" in source, (
        "app.py does not contain 'for c in result.campaigns'"
    )


def test_app_has_st_expander():
    """app.py must use st.expander for per-campaign rendering."""
    source = APP_PY.read_text()
    assert "with st.expander" in source, (
        "app.py does not contain 'with st.expander'"
    )


def test_app_renders_semantic_reasoning_via_st_write():
    """app.py must render semantic_reasoning with st.write inside the expander."""
    source = APP_PY.read_text()
    assert "st.write(c.semantic_reasoning)" in source, (
        "app.py does not contain st.write(c.semantic_reasoning)"
    )


def test_app_has_confidence_caption():
    """app.py must include a st.caption that contains 'Confidence:' per UI-04."""
    source = APP_PY.read_text()
    # The pattern: st.caption(f"Confidence: ...") or f'Confidence:'
    assert "Confidence:" in source, (
        "app.py does not contain 'Confidence:' in a st.caption call"
    )
    # Confirm it's inside a st.caption call
    assert "st.caption(" in source, (
        "app.py does not contain any st.caption( call"
    )


# ---------------------------------------------------------------------------
# GAP 3 — UI-05: import line excludes build_results_table_html; function kept
# ---------------------------------------------------------------------------

def test_app_imports_badge_html_and_pct_html():
    """app.py import from ui_helpers must include _badge_html and _pct_html."""
    source = APP_PY.read_text()
    import_lines = [
        line for line in source.splitlines()
        if line.strip().startswith("from ui_helpers import")
    ]
    assert import_lines, "app.py has no 'from ui_helpers import' line"
    combined = " ".join(import_lines)
    assert "_badge_html" in combined, (
        "app.py ui_helpers import does not include _badge_html"
    )
    assert "_pct_html" in combined, (
        "app.py ui_helpers import does not include _pct_html"
    )


def test_app_does_not_import_build_results_table_html():
    """app.py must NOT import build_results_table_html (replaced by expander loop)."""
    source = APP_PY.read_text()
    import_lines = [
        line for line in source.splitlines()
        if line.strip().startswith("from ui_helpers import")
    ]
    combined = " ".join(import_lines)
    assert "build_results_table_html" not in combined, (
        "app.py still imports build_results_table_html — should be dropped (F401 risk)"
    )


def test_build_results_table_html_still_importable_from_ui_helpers():
    """build_results_table_html must remain defined in ui_helpers.py (tests depend on it)."""
    source = UI_HELPERS_PY.read_text()
    assert "def build_results_table_html(" in source, (
        "ui_helpers.py no longer defines build_results_table_html — this breaks tests/test_ui_helpers.py"
    )


def test_build_results_table_html_runtime_importable():
    """build_results_table_html must be importable as a Python symbol at runtime."""
    import importlib
    # Ensure the project root is on sys.path for the import to resolve
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("OPENAI_API_KEY", "sk-dummy")
    mod = importlib.import_module("ui_helpers")
    assert hasattr(mod, "build_results_table_html"), (
        "build_results_table_html is not importable from ui_helpers at runtime"
    )


# ---------------------------------------------------------------------------
# GAP 4 — LAND-01: Tailwind @theme tokens + IBM Plex fonts in landing/
# ---------------------------------------------------------------------------

def test_globals_css_exists_and_has_theme_block():
    """landing/app/globals.css must exist and contain a @theme block."""
    assert GLOBALS_CSS.exists(), f"landing/app/globals.css does not exist at {GLOBALS_CSS}"
    content = GLOBALS_CSS.read_text()
    assert "@theme" in content, "globals.css does not contain a @theme block"


def test_globals_css_brand_badge_hex_tokens():
    """globals.css must define all four required badge + brand hex tokens."""
    content = GLOBALS_CSS.read_text()
    required_hex = ["#09ab3b", "#ff2b2b", "#faca2b", "#808495"]
    for hex_val in required_hex:
        assert hex_val in content, (
            f"globals.css is missing required hex token: {hex_val}"
        )


def test_layout_tsx_loads_ibm_plex_sans():
    """landing/app/layout.tsx must import IBM_Plex_Sans from next/font/google."""
    assert LAYOUT_TSX.exists(), f"landing/app/layout.tsx does not exist at {LAYOUT_TSX}"
    content = LAYOUT_TSX.read_text()
    assert "IBM_Plex_Sans" in content, (
        "layout.tsx does not import IBM_Plex_Sans"
    )
    assert "next/font/google" in content, (
        "layout.tsx does not import from next/font/google"
    )


def test_globals_css_fadeslide_in_keyframe():
    """globals.css must define the fadeSlideIn keyframe animation."""
    content = GLOBALS_CSS.read_text()
    assert "fadeSlideIn" in content, (
        "globals.css does not define the fadeSlideIn @keyframes block"
    )
    # Verify the keyframe contains the opacity transition
    assert "opacity: 0" in content or "opacity:0" in content, (
        "globals.css fadeSlideIn keyframe does not contain opacity: 0 start state"
    )


# ---------------------------------------------------------------------------
# GAP 5 — LAND-02: Landing component files + security assertions
# ---------------------------------------------------------------------------

def test_waitlist_form_tsx_exists():
    """landing/components/WaitlistForm.tsx must exist."""
    path = COMPONENTS / "WaitlistForm.tsx"
    assert path.exists(), f"WaitlistForm.tsx not found at {path}"


def test_hero_section_tsx_exists():
    """landing/components/HeroSection.tsx must exist."""
    path = COMPONENTS / "HeroSection.tsx"
    assert path.exists(), f"HeroSection.tsx not found at {path}"


def test_how_it_works_section_tsx_exists():
    """landing/components/HowItWorksSection.tsx must exist."""
    path = COMPONENTS / "HowItWorksSection.tsx"
    assert path.exists(), f"HowItWorksSection.tsx not found at {path}"


def test_waitlist_form_does_not_use_res_json():
    """WaitlistForm.tsx must NOT parse res.json() — never echoes raw API error detail (T-07-11)."""
    content = (COMPONENTS / "WaitlistForm.tsx").read_text()
    assert "res.json()" not in content, (
        "WaitlistForm.tsx calls res.json() — this violates T-07-11: raw API error detail "
        "must never be echoed to the visitor"
    )


def test_hero_section_has_rel_noopener_noreferrer():
    """HeroSection.tsx must include rel=\"noopener noreferrer\" on the Try Demo link (T-07-12)."""
    content = (COMPONENTS / "HeroSection.tsx").read_text()
    assert 'rel="noopener noreferrer"' in content, (
        "HeroSection.tsx is missing rel=\"noopener noreferrer\" on the target=_blank link "
        "— tab-nabbing mitigation (T-07-12) is absent"
    )


def test_landing_env_example_contains_api_base_url():
    """landing/.env.example must document NEXT_PUBLIC_API_BASE_URL."""
    env_example = LANDING / ".env.example"
    assert env_example.exists(), f"landing/.env.example does not exist at {env_example}"
    content = env_example.read_text()
    assert "NEXT_PUBLIC_API_BASE_URL" in content, (
        "landing/.env.example does not document NEXT_PUBLIC_API_BASE_URL"
    )


def test_landing_gitignore_covers_env_files():
    """landing/.gitignore must contain a pattern covering .env* files (T-07-07)."""
    gitignore = LANDING / ".gitignore"
    assert gitignore.exists(), f"landing/.gitignore does not exist at {gitignore}"
    content = gitignore.read_text()
    # Accepts .env*, .env.local, .env.*.local etc.
    has_env_pattern = re.search(r"\.env", content) is not None
    assert has_env_pattern, (
        "landing/.gitignore does not contain a .env* pattern — "
        "landing/.env.local (with API URL) could accidentally be committed (T-07-07)"
    )


# ---------------------------------------------------------------------------
# GAP 6 — LAND-03: badge-tokens.ts hex parity with ui_helpers.py (CRITICAL)
# ---------------------------------------------------------------------------

def _extract_ui_helpers_badge_colors():
    """
    Parse ui_helpers.py to extract the hex background/text colors from the
    `colors` dict inside `_badge_html`.  Returns a dict keyed by action name.
    e.g. {"increase": {"bg": "#09ab3b", "text": "#ffffff"}, ...}
    """
    source = UI_HELPERS_PY.read_text()
    # Match lines like: "increase": "background:#09ab3b; color:#ffffff;",
    pattern = re.compile(
        r'"(increase|pause|decrease|insufficient_data)"\s*:\s*"background:(#[0-9a-fA-F]{6});\s*color:(#[0-9a-fA-F]{6});"'
    )
    result = {}
    for m in pattern.finditer(source):
        action, bg, text = m.group(1), m.group(2), m.group(3)
        result[action] = {"bg": bg, "text": text}
    return result


def _extract_badge_tokens_colors():
    """
    Parse badge-tokens.ts to extract BADGE_COLORS hex values.
    Expects lines like: increase: { bg: "#09ab3b", text: "#ffffff", label: "INCREASE" },
    Returns a dict keyed by action name.
    """
    source = (COMPONENTS / "badge-tokens.ts").read_text()
    pattern = re.compile(
        r'(increase|pause|decrease|insufficient_data)\s*:\s*\{\s*bg:\s*"(#[0-9a-fA-F]{6})",\s*text:\s*"(#[0-9a-fA-F]{6})"'
    )
    result = {}
    for m in pattern.finditer(source):
        action, bg, text = m.group(1), m.group(2), m.group(3)
        result[action] = {"bg": bg, "text": text}
    return result


def test_badge_tokens_ts_increase_bg_is_09ab3b():
    """badge-tokens.ts: increase.bg must be #09ab3b."""
    colors = _extract_badge_tokens_colors()
    assert "increase" in colors, "badge-tokens.ts missing 'increase' entry in BADGE_COLORS"
    assert colors["increase"]["bg"].lower() == "#09ab3b", (
        f"badge-tokens.ts increase.bg is {colors['increase']['bg']!r}, expected #09ab3b"
    )


def test_badge_tokens_ts_pause_bg_is_ff2b2b():
    """badge-tokens.ts: pause.bg must be #ff2b2b."""
    colors = _extract_badge_tokens_colors()
    assert "pause" in colors, "badge-tokens.ts missing 'pause' entry in BADGE_COLORS"
    assert colors["pause"]["bg"].lower() == "#ff2b2b", (
        f"badge-tokens.ts pause.bg is {colors['pause']['bg']!r}, expected #ff2b2b"
    )


def test_badge_tokens_ts_decrease_bg_is_faca2b():
    """badge-tokens.ts: decrease.bg must be #faca2b."""
    colors = _extract_badge_tokens_colors()
    assert "decrease" in colors, "badge-tokens.ts missing 'decrease' entry in BADGE_COLORS"
    assert colors["decrease"]["bg"].lower() == "#faca2b", (
        f"badge-tokens.ts decrease.bg is {colors['decrease']['bg']!r}, expected #faca2b"
    )


def test_badge_tokens_ts_insufficient_data_bg_is_808495():
    """badge-tokens.ts: insufficient_data.bg must be #808495."""
    colors = _extract_badge_tokens_colors()
    assert "insufficient_data" in colors, (
        "badge-tokens.ts missing 'insufficient_data' entry in BADGE_COLORS"
    )
    assert colors["insufficient_data"]["bg"].lower() == "#808495", (
        f"badge-tokens.ts insufficient_data.bg is {colors['insufficient_data']['bg']!r}, expected #808495"
    )


def test_badge_tokens_ts_parity_with_ui_helpers():
    """
    CRITICAL cross-stack parity: badge-tokens.ts BADGE_COLORS bg/text must
    exactly match ui_helpers.py _badge_html colors dict for all four actions.
    """
    py_colors = _extract_ui_helpers_badge_colors()
    ts_colors = _extract_badge_tokens_colors()

    assert py_colors, "Could not parse badge colors from ui_helpers.py"
    assert ts_colors, "Could not parse badge colors from badge-tokens.ts"

    for action in ("increase", "pause", "decrease", "insufficient_data"):
        assert action in py_colors, f"ui_helpers.py missing color entry for {action!r}"
        assert action in ts_colors, f"badge-tokens.ts missing color entry for {action!r}"
        assert py_colors[action]["bg"].lower() == ts_colors[action]["bg"].lower(), (
            f"bg color mismatch for {action!r}: "
            f"ui_helpers.py has {py_colors[action]['bg']!r}, "
            f"badge-tokens.ts has {ts_colors[action]['bg']!r}"
        )
        assert py_colors[action]["text"].lower() == ts_colors[action]["text"].lower(), (
            f"text color mismatch for {action!r}: "
            f"ui_helpers.py has {py_colors[action]['text']!r}, "
            f"badge-tokens.ts has {ts_colors[action]['text']!r}"
        )


def test_badge_tokens_pct_color_values():
    """badge-tokens.ts PCT_COLOR must define positive=#09ab3b, negative=#ff2b2b, zero=#808495."""
    source = (COMPONENTS / "badge-tokens.ts").read_text()
    # Parse PCT_COLOR block
    pct_pattern = re.compile(
        r'PCT_COLOR\s*=\s*\{([^}]+)\}',
        re.DOTALL,
    )
    m = pct_pattern.search(source)
    assert m, "Could not find PCT_COLOR object in badge-tokens.ts"
    block = m.group(1)

    pos_m = re.search(r'positive\s*:\s*"(#[0-9a-fA-F]{6})"', block)
    neg_m = re.search(r'negative\s*:\s*"(#[0-9a-fA-F]{6})"', block)
    zero_m = re.search(r'zero\s*:\s*"(#[0-9a-fA-F]{6})"', block)

    assert pos_m, "PCT_COLOR.positive not found in badge-tokens.ts"
    assert neg_m, "PCT_COLOR.negative not found in badge-tokens.ts"
    assert zero_m, "PCT_COLOR.zero not found in badge-tokens.ts"

    assert pos_m.group(1).lower() == "#09ab3b", (
        f"PCT_COLOR.positive is {pos_m.group(1)!r}, expected #09ab3b"
    )
    assert neg_m.group(1).lower() == "#ff2b2b", (
        f"PCT_COLOR.negative is {neg_m.group(1)!r}, expected #ff2b2b"
    )
    assert zero_m.group(1).lower() == "#808495", (
        f"PCT_COLOR.zero is {zero_m.group(1)!r}, expected #808495"
    )


# ---------------------------------------------------------------------------
# GAP 7 — LAND-04: DemoAnimation observer cleanup + no dangerouslySetInnerHTML
# ---------------------------------------------------------------------------

def test_demo_animation_tsx_exists():
    """landing/components/DemoAnimation.tsx must exist."""
    path = COMPONENTS / "DemoAnimation.tsx"
    assert path.exists(), f"DemoAnimation.tsx not found at {path}"


def test_demo_animation_has_observer_disconnect():
    """DemoAnimation.tsx must call observer.disconnect() (T-07-17 — prevents re-trigger)."""
    content = (COMPONENTS / "DemoAnimation.tsx").read_text()
    assert "observer.disconnect()" in content, (
        "DemoAnimation.tsx does not call observer.disconnect() — "
        "IntersectionObserver may leak or re-trigger (T-07-17)"
    )


def test_demo_animation_has_useeffect_cleanup():
    """DemoAnimation.tsx useEffect must return () => observer.disconnect() cleanup (T-07-18)."""
    content = (COMPONENTS / "DemoAnimation.tsx").read_text()
    # Accepts both arrow and traditional return forms
    has_cleanup = (
        "return () => observer.disconnect()" in content
        or "return ()=>observer.disconnect()" in content
    )
    assert has_cleanup, (
        "DemoAnimation.tsx useEffect does not return a cleanup function calling "
        "observer.disconnect() — memory leak if component unmounts (T-07-18)"
    )


def test_features_section_tsx_exists():
    """landing/components/FeaturesSection.tsx must exist."""
    path = COMPONENTS / "FeaturesSection.tsx"
    assert path.exists(), f"FeaturesSection.tsx not found at {path}"


def test_footer_tsx_exists():
    """landing/components/Footer.tsx must exist."""
    path = COMPONENTS / "Footer.tsx"
    assert path.exists(), f"Footer.tsx not found at {path}"


def test_no_dangerously_set_inner_html_in_landing_components():
    """No landing component file may use dangerouslySetInnerHTML (T-07-09/T-07-15)."""
    violations = []
    for tsx_file in COMPONENTS.glob("*.tsx"):
        content = tsx_file.read_text()
        if "dangerouslySetInnerHTML" in content:
            violations.append(tsx_file.name)
    assert not violations, (
        f"dangerouslySetInnerHTML found in landing component(s): {violations} — "
        "this bypasses React's XSS protection (T-07-09/T-07-15)"
    )
