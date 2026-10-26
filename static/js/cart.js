"use strict";
document.addEventListener("DOMContentLoaded", async () => {
  let cart; try {cart = JSON.parse(localStorage.getItem("restaurant-cart") || "[]"); if (!Array.isArray(cart) || cart.length > 100) cart = [];} catch {cart = [];}
  let branch = null;
  const parent = document.getElementById("cart-items"), panel = document.getElementById("checkout-panel"), totals = document.getElementById("cart-totals");
  const save = () => { localStorage.setItem("restaurant-cart", JSON.stringify(cart)); localStorage.removeItem("restaurant-checkout-key"); };
  async function render() {
    parent.replaceChildren(); panel.hidden = !cart.length;
    if (!cart.length) {parent.append(OS.node("p", "Your cart is waiting for something delicious. Browse the menu to get started.", "empty")); return;}
    branch = await OS.api(`/api/v1/branches/${cart[0].branch}/`);
    for (let index = 0; index < cart.length; index++) {
      const line = cart[index], row = OS.node("article", undefined, "card row"), info = OS.node("div");
      info.append(OS.node("strong", line.name), OS.node("p", `${line.modifierNames.join(", ")} ${line.notes}`, "muted"));
      const quantity = OS.node("input"); quantity.type = "number"; quantity.min = "1"; quantity.max = "100"; quantity.value = line.quantity; quantity.className = "quantity"; quantity.setAttribute("aria-label", `Quantity for ${line.name}`);
      quantity.onchange = () => {const value = Number(quantity.value); if (!Number.isInteger(value) || value < 1 || value > 100) {quantity.value = line.quantity; return;} line.quantity = value; save(); render().catch(error => OS.toast(error.message));};
      const remove = OS.node("button", "Remove", "small secondary"); remove.onclick = () => {cart.splice(index, 1); save(); render().catch(error => OS.toast(error.message));};
      row.append(info, quantity, OS.node("strong", `${branch.restaurant ? line.currency : ""} ${(line.unitPrice * line.quantity).toFixed(2)}`), remove); parent.append(row);
    }
    const subtotal = cart.reduce((sum, line) => sum + line.quantity * line.unitPrice, 0), tax = Math.round(subtotal * Number(branch.tax_rate) * 100) / 100;
    totals.replaceChildren(OS.node("p", `Estimated subtotal: ${cart[0].currency} ${subtotal.toFixed(2)}`), OS.node("p", `Tax: ${cart[0].currency} ${tax.toFixed(2)}`), OS.node("p", `Discount: ${cart[0].currency} 0.00`), OS.node("h3", `Estimated total: ${cart[0].currency} ${(subtotal + tax).toFixed(2)}`));
  }
  try {
    const itemId = new URLSearchParams(location.search).get("item");
    if (itemId && /^\d+$/.test(itemId)) {
      const item = await OS.api(`/api/v1/menu/items/${itemId}/`), target = document.getElementById("customize");
      const restaurant = await OS.api(`/api/v1/branches/${item.branch}/`); const profile = await OS.api(`/api/v1/restaurants/${restaurant.restaurant}/`);
      target.hidden = false; target.append(OS.node("h2", item.name), OS.node("p", `${profile.currency} ${item.price}`));
      const form = OS.node("form"), selected = [];
      for (const modifier of item.modifiers) {const label = OS.node("label", undefined, "checkbox"); const input = OS.node("input"); input.type = "checkbox"; input.value = modifier.id; input.onchange = () => {if (input.checked) selected.push(modifier); else selected.splice(selected.indexOf(modifier), 1);}; label.append(input, OS.node("span", `${modifier.name} + ${profile.currency} ${modifier.price}`)); form.append(label);}
      const notesLabel = OS.node("label", "Special instructions"), notes = OS.node("textarea"); notes.maxLength = 2000; notesLabel.append(notes);
      const quantityLabel = OS.node("label", "Quantity"), quantity = OS.node("input"); quantity.type = "number"; quantity.min = "1"; quantity.max = "100"; quantity.value = "1"; quantityLabel.append(quantity);
      const add = OS.node("button", "Add to cart"); add.type = "submit"; add.disabled = !item.availability; form.append(notesLabel, quantityLabel, add); target.append(form);
      form.onsubmit = event => {event.preventDefault(); if (cart.length && cart[0].branch !== item.branch && !confirm("Your cart is from another location. Start a new cart for this branch?")) return; if (cart.length && cart[0].branch !== item.branch) cart = []; cart.push({menu_item: item.id, branch: item.branch, name: item.name, currency: profile.currency, quantity: Number(quantity.value), modifiers: selected.map(m => m.id), modifierNames: selected.map(m => m.name), unitPrice: Number(item.price) + selected.reduce((sum, m) => sum + Number(m.price), 0), notes: notes.value}); save(); location.href = "/cart/";};
    }
    await render();
  } catch (error) {parent.textContent = error.message; parent.className = "notice error";}
  const type = document.getElementById("order-type"); type.onchange = () => {document.getElementById("table-label").hidden = type.value !== "DINE_IN"; document.getElementById("address-label").hidden = type.value !== "DELIVERY";};
  document.getElementById("checkout").onsubmit = async event => {
    event.preventDefault(); const button = document.getElementById("place-order"); if (!button || !cart.length) return; button.disabled = true; button.textContent = "Placing your order?";
    try {
      let key = localStorage.getItem("restaurant-checkout-key"); if (!key) {key = crypto.randomUUID(); localStorage.setItem("restaurant-checkout-key", key);}
      const payload = {branch: cart[0].branch, items: cart.map(({menu_item, quantity, modifiers, notes}) => ({menu_item, quantity, modifiers, notes})), order_type: type.value, notes: document.getElementById("order-notes").value, delivery_address: document.getElementById("delivery-address").value, request_key: key};
      if (type.value === "DINE_IN") {const tables = await OS.api(`/api/v1/public-tables/?branch=${cart[0].branch}`); const table = tables.find(t => t.table_number === document.getElementById("table-number").value.trim()); if (!table) throw new Error("Choose a valid table number for this branch."); payload.table = table.id;}
      const order = await OS.api("/api/v1/orders/", {method: "POST", body: JSON.stringify(payload)}); localStorage.removeItem("restaurant-cart"); localStorage.removeItem("restaurant-checkout-key"); location.href = `/orders/${order.id}/`;
    } catch (error) {document.getElementById("checkout-error").textContent = error.message; button.disabled = false; button.textContent = "Place order";}
  };
  document.getElementById("checkout").addEventListener("change", () => localStorage.removeItem("restaurant-checkout-key"));
});
