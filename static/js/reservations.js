"use strict";
document.addEventListener("DOMContentLoaded", async () => {
  const branchSelect = document.getElementById("reservation-branch"), results = document.getElementById("table-results"), booking = document.getElementById("booking-form"), errorBox = document.getElementById("reservation-error");
  let branches = [], slot = null, selected = null;
  try {branches = await OS.pages("/api/v1/branches/"); branchSelect.replaceChildren(OS.node("option", "Choose a location")); branchSelect.firstChild.value = ""; for (const branch of branches) {const option = OS.node("option", branch.name); option.value = branch.id; branchSelect.append(option);}} catch (error) {errorBox.textContent = error.message;}
  const invalidate = () => {slot = null; selected = null; booking.hidden = true; results.replaceChildren();};
  document.getElementById("availability-form").addEventListener("change", invalidate);
  branchSelect.addEventListener("change", () => {const branch = branches.find(b => String(b.id) === branchSelect.value); const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; document.getElementById("branch-hours").textContent = branch?.operating_hours.map(h => `${days[h.weekday]} ${h.opens_at.slice(0,5)} - ${h.closes_at.slice(0,5)}`).join(" ? ") || "Operating hours have not been published for this branch.";});
  document.getElementById("availability-form").onsubmit = async event => {
    event.preventDefault(); invalidate(); errorBox.textContent = ""; const button = document.getElementById("check-tables"); button.disabled = true; button.textContent = "Checking availability...";
    try {
      const params = {branch: branchSelect.value, reservation_date: document.getElementById("reservation-date").value, start_time: document.getElementById("reservation-start").value, end_time: document.getElementById("reservation-end").value, guest_count: document.getElementById("reservation-guests").value};
      const [available, tables] = await Promise.all([OS.api(`/api/v1/reservations/availability/?${new URLSearchParams(params)}`), OS.api(`/api/v1/public-tables/?branch=${params.branch}`)]);
      slot = params; const ids = new Set(available.map(t => t.id));
      if (!tables.length) results.append(OS.node("p", "No tables are published for this location.", "empty"));
      for (const table of tables) {const card = OS.node("article", undefined, "card"); const fits = table.capacity >= Number(params.guest_count), free = ids.has(table.id); card.append(OS.node("h3", `Table ${table.table_number}`), OS.node("p", `Seats ${table.capacity}`), OS.node("span", free ? "Available" : fits ? "Unavailable for this time" : "Too small for this party", "pill")); if (free) {const select = OS.node("button", "Select table", "small"); select.onclick = () => {selected = table; booking.hidden = false; document.getElementById("selected-table").textContent = `Table ${table.table_number} \u00b7 ${params.reservation_date} \u00b7 ${params.start_time}`; booking.scrollIntoView({behavior: "smooth", block: "center"});}; card.append(OS.node("p"), select);} results.append(card);}
      if (!available.length) results.prepend(OS.node("p", "No suitable tables are free. Try another time or location.", "notice"));
    } catch (error) {errorBox.textContent = error.message;} finally {button.disabled = false; button.textContent = "Find a table";}
  };
  booking.onsubmit = async event => {
    event.preventDefault(); if (!slot || !selected) return; const button = document.getElementById("confirm-booking"); button.disabled = true; button.textContent = "Requesting your table...";
    try {await OS.api("/api/v1/reservations/", {method: "POST", body: JSON.stringify({...slot, table: selected.id, guest_name: document.getElementById("guest-name").value, guest_phone: document.getElementById("guest-phone").value, special_requests: document.getElementById("special-requests").value})}); location.href = "/my/";} catch (error) {errorBox.textContent = error.message; errorBox.scrollIntoView({block:"center"}); button.disabled = false; button.textContent = "Request reservation";}
  };
});
