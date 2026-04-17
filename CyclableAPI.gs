/**
 * CyclableAPI.gs — v2
 *
 * Web App Google Apps Script — expose deux endpoints JSON :
 *   ?mode=data    → magasins (onglet "Cyclable")
 *   ?mode=essais  → essais clients (onglet "essai")
 *   ?mode=debug   → debug des en-têtes
 *
 * DÉPLOIEMENT (à faire une seule fois) :
 *   1. Ouvrir le Google Sheet
 *   2. Extensions → Apps Script → coller ce fichier
 *   3. Déployer → Nouveau déploiement
 *      Type : Application Web
 *      Exécuter en tant que : Moi
 *      Accès : Tout le monde
 *   4. Copier l'URL et la mettre dans secrets.toml → gas_url
 */

// ── CONFIG ─────────────────────────────────────────────────────────────────────
var CONFIG = {
  SHEET_NAME:      "Cyclable",
  ESSAIS_SHEET_NAME: "essai",
  ESSAIS_GID:      1377845477,
  HEADER_ROW:      1,
  COLUMNS: {
    n:    ["magasin", "nom", "store", "name"],
    r:    ["responsable", "rep", "commercial"],
    t:    ["type", "statut"],
    reg:  ["région", "region"],
    ca:   ["ca", "chiffre", "revenue"],
    v:    ["vélos", "velos", "vendu", "vente"],
    o:    ["objectif", "obj", "target"],
    c:    ["coaching", "score", "note"],
    e:    ["essais", "essai", "test"],
    vt:   ["vt", "visite terrain"],
    lat:  ["lat", "latitude"],
    lng:  ["lng", "longitude", "long"],
    form: ["form", "formulaire", "date form"]
  }
};

// Colonnes de l'onglet "essai" (index 0-basé)
var ESSAIS_COL = {
  essai:      0,   // A — numéro d'essai
  produit:    1,   // B — produit
  dpt:        3,   // D — département
  cp:         4,   // E — code postal
  store:      5,   // F — UTM / magasin
  fiscal:     6,   // G — année fiscale
  year:       7,   // H — année civile
  month:      8,   // I — mois
  typeform:   9,   // J — CALENDLY/TYPE FORM
  product_q: 10,   // K — Quel produit souhaitez-vous essayer ?
  prenom:    11,   // L — Prénom
  nom:       12,   // M — Nom
  tel:       13,   // N — Téléphone
  email:     14,   // O — E-mail
  utm_src:   15,   // P — utm_source
  date:      16,   // Q — Submitted At
  token:     17    // R — Token
};

// ── ROUTER ────────────────────────────────────────────────────────────────────
function doGet(e) {
  var mode = (e && e.parameter && e.parameter.mode) || "data";

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();

    if (mode === "essais") {
      return jsonResponse(getEssaisData(ss));
    }

    if (mode === "debug") {
      var sheet = findSheet(ss, CONFIG.SHEET_NAME, null);
      if (!sheet) return jsonResponse({ error: "Onglet introuvable" });
      var data = sheet.getDataRange().getValues();
      return jsonResponse({
        sheetName: sheet.getName(),
        totalRows: data.length,
        headers: data[0],
        sample: data.slice(1, 4)
      });
    }

    // mode === "data" (défaut)
    return jsonResponse(getMagasinsData(ss));

  } catch (err) {
    return jsonResponse({ error: err.message, stack: err.stack });
  }
}

// ── ESSAIS ─────────────────────────────────────────────────────────────────────
function getEssaisData(ss) {
  var sheet = findSheet(ss, CONFIG.ESSAIS_SHEET_NAME, CONFIG.ESSAIS_GID);

  if (!sheet) {
    return {
      error: "Onglet 'essai' introuvable",
      hint: "Onglets disponibles : " + ss.getSheets().map(function(s) { return s.getName(); }).join(", ")
    };
  }

  var data  = sheet.getDataRange().getValues();
  var rows  = [];
  var byStore = {};

  for (var i = CONFIG.HEADER_ROW; i < data.length; i++) {
    var row   = data[i];
    var store = String(row[ESSAIS_COL.store] || "").trim();

    // Ignore les lignes sans magasin
    if (!store) continue;

    var dateVal = row[ESSAIS_COL.date];

    rows.push({
      store:   store,
      date:    formatDate(dateVal),
      product: String(row[ESSAIS_COL.product_q] || row[ESSAIS_COL.produit] || "").trim(),
      dept:    String(row[ESSAIS_COL.dpt] || "").trim(),
      cp:      String(row[ESSAIS_COL.cp]  || "").trim(),
      fiscal:  String(row[ESSAIS_COL.fiscal] || "").trim(),
      year:    row[ESSAIS_COL.year]  || null,
      month:   row[ESSAIS_COL.month] || null
    });

    // Agrégat par magasin
    if (!byStore[store]) {
      byStore[store] = { total: 0, byMonth: {} };
    }
    byStore[store].total++;

    var monthKey = "";
    if (dateVal instanceof Date && !isNaN(dateVal)) {
      monthKey = dateVal.getFullYear() + "-" + String(dateVal.getMonth() + 1).padStart(2, "0");
    } else if (row[ESSAIS_COL.fiscal]) {
      monthKey = String(row[ESSAIS_COL.fiscal]);
    }
    if (monthKey) {
      byStore[store].byMonth[monthKey] = (byStore[store].byMonth[monthKey] || 0) + 1;
    }
  }

  return {
    total:   rows.length,
    rows:    rows,
    byStore: byStore
  };
}

// ── MAGASINS ──────────────────────────────────────────────────────────────────
function getMagasinsData(ss) {
  var sheet = findSheet(ss, CONFIG.SHEET_NAME, null);
  if (!sheet) {
    return {
      error: "Onglet introuvable",
      hint: "Onglets disponibles : " + ss.getSheets().map(function(s) { return s.getName(); }).join(", ")
    };
  }

  var data   = sheet.getDataRange().getValues();
  var colMap = detectColumns(data[0]);
  var stores = parseStores(data, colMap);
  var today  = new Date();
  var dateStr = today.getDate() + " "
    + ["janv","févr","mars","avr","mai","juin","juil","août","sept","oct","nov","déc"][today.getMonth()]
    + " " + today.getFullYear();

  var meta = {
    objectif_fy26:        toNum(sheet.getRange("P4").getValue()),
    demo_bikes:           toNum(sheet.getRange("E4").getValue()),
    sellout_fy26:         toNum(sheet.getRange("J4").getValue()),
    objectif_sellin_mars: toNum(sheet.getRange("T4").getValue()),
    sellin_mars:          toNum(sheet.getRange("U4").getValue())
  };
  meta.sell_in = meta.sellout_fy26 + meta.demo_bikes;

  return { updated: dateStr, colMap: colMap, meta: meta, stores: stores };
}

// ── UTILITAIRES ───────────────────────────────────────────────────────────────
function findSheet(ss, name, gid) {
  var sheet = ss.getSheetByName(name);
  if (sheet) return sheet;

  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getName().toLowerCase() === name.toLowerCase()) return sheets[i];
  }
  if (gid !== null) {
    for (var j = 0; j < sheets.length; j++) {
      if (sheets[j].getSheetId() === gid) return sheets[j];
    }
  }
  return null;
}

function detectColumns(headers) {
  var colMap = {};
  var norm = headers.map(function(h) { return String(h).toLowerCase().trim(); });
  for (var key in CONFIG.COLUMNS) {
    var kws = CONFIG.COLUMNS[key];
    if (typeof kws === "number") { colMap[key] = kws - 1; continue; }
    var found = -1;
    for (var i = 0; i < norm.length && found < 0; i++) {
      for (var j = 0; j < kws.length; j++) {
        if (norm[i].indexOf(kws[j]) >= 0) { found = i; break; }
      }
    }
    colMap[key] = found;
  }
  return colMap;
}

function parseStores(data, colMap) {
  var stores = [];
  for (var i = CONFIG.HEADER_ROW; i < data.length; i++) {
    var row  = data[i];
    var name = colMap.n >= 0 ? String(row[colMap.n] || "").trim() : "";
    if (!name || name.toLowerCase() === "total" || name.toLowerCase() === "magasin") continue;
    var store = {
      n:    name,
      r:    colMap.r   >= 0 ? String(row[colMap.r]   || "").trim() : "",
      t:    colMap.t   >= 0 ? String(row[colMap.t]   || "").trim() : "",
      reg:  colMap.reg >= 0 ? String(row[colMap.reg] || "").trim() : "",
      ca:   colMap.ca  >= 0 ? toNum(row[colMap.ca])                : 0,
      v:    colMap.v   >= 0 ? toNum(row[colMap.v])                 : 0,
      o:    colMap.o   >= 0 ? toNum(row[colMap.o])                 : 0,
      c:    colMap.c   >= 0 ? toNumOrNull(row[colMap.c])           : null,
      e:    colMap.e   >= 0 ? toNum(row[colMap.e])                 : 0,
      vt:   colMap.vt  >= 0 ? toNum(row[colMap.vt])               : 0,
      lat:  colMap.lat >= 0 ? toFloat(row[colMap.lat])             : null,
      lng:  colMap.lng >= 0 ? toFloat(row[colMap.lng])             : null,
      form: colMap.form >= 0 ? formatDate(row[colMap.form])        : null
    };
    store.g = store.v - store.o;
    stores.push(store);
  }
  return stores;
}

function toNum(val) {
  var n = parseFloat(String(val).replace(/[^\d.-]/g, ""));
  return isNaN(n) ? 0 : Math.round(n);
}
function toFloat(val) {
  var n = parseFloat(val);
  return isNaN(n) ? null : n;
}
function toNumOrNull(val) {
  if (val === "" || val === null || val === undefined) return null;
  var n = parseFloat(String(val).replace(/[^\d.-]/g, ""));
  return isNaN(n) ? null : Math.round(n);
}
function formatDate(val) {
  if (!val) return null;
  if (val instanceof Date && !isNaN(val)) {
    var y = val.getFullYear();
    var m = String(val.getMonth() + 1).padStart(2, "0");
    var d = String(val.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
  }
  var s = String(val).trim();
  return s || null;
}
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj, null, 2))
    .setMimeType(ContentService.MimeType.JSON);
}
