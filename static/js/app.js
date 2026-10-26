"use strict";
window.OS = {
  csrf() { return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1] || ""; },
  async api(url, options = {}) {
    const response = await fetch(url, {credentials: "same-origin", ...options, headers: {"Content-Type": "application/json", "X-CSRFToken": OS.csrf(), ...options.headers}});
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : JSON.stringify(data));
    return data;
  },
  toast(message) { const el = document.getElementById("toast"); el.textContent = message; el.hidden = false; setTimeout(() => {el.hidden = true;}, 4500); },
  node(tag, text, className) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; },
  async pages(url) { let result = []; while (url) {const data = await OS.api(url); if (Array.isArray(data)) return data; result.push(...data.results); url = data.next;} return result; }
};

(() => {
  const key = "restaurantos-theme";
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const colorMeta = document.querySelector('meta[name="theme-color"]');
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");

  function update(theme, persist = false) {
    const isDark = theme === "dark";
    root.dataset.theme = isDark ? "dark" : "light";
    if (toggle) {
      toggle.setAttribute("aria-pressed", String(isDark));
      toggle.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} mode`);
      toggle.querySelector("[aria-hidden]").textContent = isDark ? "☀" : "☾";
      toggle.querySelector(".theme-toggle-label").textContent = isDark ? "Light mode" : "Dark mode";
    }
    if (colorMeta) colorMeta.content = isDark ? "#121916" : "#f9f8f3";
    if (persist) {
      try { window.localStorage.setItem(key, isDark ? "dark" : "light"); } catch { /* Theme still works for this page. */ }
    }
  }

  update(root.dataset.theme || (media?.matches ? "dark" : "light"));
  toggle?.addEventListener("click", () => update(root.dataset.theme === "dark" ? "light" : "dark", true));
  media?.addEventListener("change", (event) => {
    let saved = null;
    try { saved = window.localStorage.getItem(key); } catch { /* Use the current selection. */ }
    if (saved !== "light" && saved !== "dark") update(event.matches ? "dark" : "light");
  });
})();
