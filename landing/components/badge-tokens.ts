// Mirror of ui_helpers.py _badge_html / _pct_html — LOCKED hex values. Any change here MUST be matched in ui_helpers.py and vice versa.

export const BADGE_COLORS = {
  increase: { bg: "#09ab3b", text: "#ffffff", label: "INCREASE" },
  pause: { bg: "#ff2b2b", text: "#ffffff", label: "PAUSE" },
  decrease: { bg: "#faca2b", text: "#262730", label: "DECREASE" },
  insufficient_data: { bg: "#808495", text: "#ffffff", label: "INSUFFICIENT DATA" },
} as const;

export const PCT_COLOR = {
  positive: "#09ab3b",
  negative: "#ff2b2b",
  zero: "#808495",
} as const;
