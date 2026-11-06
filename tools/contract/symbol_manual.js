const tabs = [...document.querySelectorAll("section.tab")];
function show(id) {
  if (!document.getElementById(id)) id = tabs[0].id;
  tabs.forEach(t => t.hidden = t.id !== id);
  document.querySelectorAll(".side .index").forEach(n => n.hidden = n.dataset.tab !== id);
  document.querySelectorAll(".tabs button").forEach(b => b.setAttribute("aria-selected", b.dataset.tab === id));
}
function follow() {
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (!target) return show(tabs[0].id);
  show(target.closest("section.tab").id);
  const group = target.closest("details");
  if (group) group.open = true;
  target.scrollIntoView();
}
document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.tab; }));
document.getElementById("open-all").addEventListener("click", () => document.querySelectorAll("details.group").forEach(d => d.open = true));
document.getElementById("close-all").addEventListener("click", () => document.querySelectorAll("details.group").forEach(d => d.open = false));
window.addEventListener("hashchange", follow);
follow();
