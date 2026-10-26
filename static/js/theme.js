"use strict";
// Set the theme before the stylesheet is applied to avoid a light-theme flash.
(() => {
  const key = "restaurantos-theme";
  let theme = null;
  try {
    theme = window.localStorage.getItem(key);
  } catch {
    // Storage can be unavailable in private or restricted browsing contexts.
  }
  if (theme !== "light" && theme !== "dark") {
    theme = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = theme;
})();
