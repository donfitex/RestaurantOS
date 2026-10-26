"use strict";
document.addEventListener("DOMContentLoaded", async () => {
  const summary = document.getElementById("account-data");
  try {
    const history = await OS.api("/api/v1/auth/history/");
    summary.textContent = `${history.order_count} orders ? ${history.reservation_count} reservations`;
    for (const [kind, url] of [["orders", "/api/v1/orders/"], ["reservations", "/api/v1/reservations/"]]) {
      const parent = document.getElementById(`my-${kind}`);
      const data = await OS.api(url);
      if (!data.results.length) { parent.append(OS.node("p", `No ${kind} yet.`, "empty")); continue; }
      for (const item of data.results) {
        const card = OS.node("article", undefined, "card row");
        card.append(OS.node("span", kind === "orders" ? `Order #${item.id} \u00b7 ${item.currency} ${item.total}` : `${item.reservation_date} \u00b7 ${item.start_time} \u00b7 ${item.guest_count} guests`), OS.node("span", item.status, "pill"));
        if ((kind === "orders" && item.status === "PENDING") || (kind === "reservations" && ["PENDING", "CONFIRMED"].includes(item.status))) {
          const cancel = OS.node("button", "Cancel", "small secondary");
          cancel.onclick = async () => { if (!confirm(`Cancel this ${kind === "orders" ? "order" : "reservation"}?`)) return; cancel.disabled = true; try {await OS.api(`${url}${item.id}/cancel/`, {method: "POST", body: "{}"}); location.reload();} catch (error) {OS.toast(error.message); cancel.disabled = false;} };
          card.append(cancel);
        }
        parent.append(card);
      }
      if (data.next) {const more = OS.node("a", "View next page"); more.href = data.next; parent.append(more);}
    }
  } catch (error) {summary.textContent = error.message; summary.className = "notice error";}
});
