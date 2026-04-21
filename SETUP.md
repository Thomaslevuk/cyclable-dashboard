# 🚲 Cyclable Dashboard — Guide de déploiement

## Ce que tu obtiens
Un dashboard en ligne, protégé par mot de passe, accessible à toute ton équipe.
Connecté en temps réel à Shopify + Google Sheets (essais).

---

## Architecture

| Source | Comment | Status |
|---|---|---|
| Shopify orders | OAuth2 client_credentials (auto) | ✅ Configuré |
| Google Sheets essais | Export CSV public (onglet "essai") | ✅ Configuré |
| Mot de passe | secrets.toml | ✅ Configuré |

---

## ÉTAPE 1 — Déployer sur Streamlit Community Cloud (5 min)

> Le code est déjà sur GitHub : `Thomaslevuk/cyclable-dashboard`

1. Va sur **https://share.streamlit.io**
2. Connecte-toi avec le compte GitHub **Thomaslevuk**
3. Clique **"New app"**
4. Sélectionne :
   - Repository : `Thomaslevuk/cyclable-dashboard`
   - Branch : `main`
   - Main file : `app.py`
5. Clique sur **"Advanced settings"** → **"Secrets"**
6. Colle le contenu de ton fichier `.streamlit/secrets.toml` local
   (il contient déjà le password, client_id et client_secret Shopify)

7. Clique **Deploy** — l'app est en ligne en ~2 minutes

Tu obtiens une URL du type `https://cyclable-dashboard-xxx.streamlit.app` à partager.

---

## ÉTAPE 2 — Partager l'accès

- Partage l'URL Streamlit à ton équipe
- Mot de passe : **Ritmic26**
- Données rafraîchies automatiquement toutes les 6h
- Bouton "🔄 Rafraîchir" disponible dans la sidebar pour forcer la mise à jour

---

## Mot de passe

```
Ritmic26
```

---

## Règles métier appliquées

| Règle | Détail |
|---|---|
| Filtre compte | Commandes dont le company contient "cyclable" |
| CA magasin | `total_price` complet de la commande (tous les items) |
| Vélos comptés | SKU dans la liste exacte (Solo/Duo/Jumbo/Ritmic) |
| Vélos exclus | Kits accessoires (AL005853, 854, 852, 855...) |
| Vélos 0€ | Non comptés |
| 1er vélo/commande | Exclu (demo bike) |
| Essais | Onglet "essai" du Google Sheet, filtré FY26 + UTM Cyclable |

---

## Fichiers clés

| Fichier | Rôle |
|---|---|
| `app.py` | Dashboard principal |
| `requirements.txt` | Dépendances Python |
| `.streamlit/secrets.toml` | Credentials (jamais sur GitHub) |
| `.streamlit/config.toml` | Thème couleurs Elwing |
| `CyclableAPI.gs` | Script GAS (conservé, plus nécessaire) |

---

## Problèmes ?

Donne le message d'erreur à Claude Code et c'est corrigé immédiatement.
