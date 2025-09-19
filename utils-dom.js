// utils-dom.js
function parsePercentText(txt) {
  const n = parseInt(String(txt).replace(/[^\d-]/g, ""), 10);
  return Number.isNaN(n) ? null : n;
}

function signedByClass(raw, className) {
  if (raw == null) return null;
  const negative = className?.includes("bg-red-300");
  return negative ? -Math.abs(raw) : Math.abs(raw);
}

// Trouve le badge (span/div) qui suit un label exact "7d"/"30d"
function findBadgeAfterLabel(root, label) {
  const all = Array.from(root.querySelectorAll("*"));
  const labelNode = all.find(n => n.childNodes.length === 1 && n.textContent.trim() === label);
  if (!labelNode) return null;

  // 1) Essaye les frères directs à droite
  for (let sib = labelNode.nextElementSibling; sib; sib = sib.nextElementSibling) {
    if (/%/.test(sib.textContent)) return sib;
  }
  // 2) Fallback: dans le même parent, l'élément avec un %
  const parent = labelNode.parentElement || root;
  const candidate = Array.from(parent.children).find(el => /%/.test(el.textContent));
  return candidate || null;
}

export function extractLiveAdsFromDOM(root = document) {
  const badge7 = findBadgeAfterLabel(root, "7d");
  const badge30 = findBadgeAfterLabel(root, "30d");

  const v7 = parsePercentText(badge7?.textContent);
  const v30 = parsePercentText(badge30?.textContent);

  const live_ads_7d = signedByClass(v7, badge7?.className || "");
  const live_ads_30d = signedByClass(v30, badge30?.className || "");

  return { live_ads_7d, live_ads_30d };
}

// Exemple d'usage (dans page.evaluate):
// const { live_ads_7d, live_ads_30d } = extractLiveAdsFromDOM();