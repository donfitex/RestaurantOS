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
