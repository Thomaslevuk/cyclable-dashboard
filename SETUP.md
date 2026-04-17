# 🚲 Cyclable Dashboard — Guide de déploiement

## Ce que tu vas obtenir
Un dashboard en ligne, protégé par mot de passe, accessible à toute ton équipe,
qui se connecte automatiquement à Shopify et Google Sheets.

---

## ÉTAPE 1 — Déployer le script Google Apps Script (15 min)

> Objectif : exposer les données de l'onglet "essai" en JSON pour le dashboard.

1. Ouvre ton Google Sheet :
   https://docs.google.com/spreadsheets/d/1EZdvK-6u0yDtpw-xJUlqqQ1heScSFdDPLVoBJvO5TSI

2. Dans le menu : **Extensions → Apps Script**

3. Si un fichier `.gs` existe déjà, supprime son contenu.
   Sinon, clique sur **"+ Nouveau fichier"** → Code.gs

4. Copie-colle intégralement le contenu du fichier `CyclableAPI.gs`

5. Clique sur l'icône **Enregistrer** (💾)

6. Clique sur **Déployer → Nouveau déploiement**
   - Type : **Application Web**
   - Exécuter en tant que : **Moi** (ton compte Google)
   - Qui peut accéder : **Tout le monde**
   - Clique sur **Déployer**
   - Autorise l'accès si demandé

7. **Copie l'URL** générée (format : `https://script.google.com/macros/s/.../exec`)

8. Colle cette URL dans `.streamlit/secrets.toml` :
   ```
   gas_url = "https://script.google.com/macros/s/TON_URL_ICI/exec"
   ```

9. **Test** : ouvre `https://[ton-url]/exec?mode=essais` dans un navigateur.
   Tu dois voir du JSON avec tes essais.

---

## ÉTAPE 2 — Shopify ✅ déjà configuré

Les credentials Shopify (Client ID + Secret) sont déjà dans `.streamlit/secrets.toml`.
Rien à faire pour cette étape.

---

## ÉTAPE 3 — Créer un compte GitHub (5 min)

1. Va sur https://github.com/signup
2. Entre ton email (thomas@elwing.co), un mot de passe, un nom d'utilisateur
3. Vérifie ton email
4. **Envoie-moi ton nom d'utilisateur GitHub** et je fais la suite pour toi

---

## ÉTAPE 4 — Mettre le code sur GitHub (je le fais pour toi)

Une fois ton compte GitHub créé, je t'explique comment :
1. Créer un dépôt privé
2. Y mettre les fichiers (app.py, requirements.txt, CyclableAPI.gs)
3. Connecter à Streamlit Community Cloud

---

## ÉTAPE 5 — Déployer sur Streamlit Community Cloud (5 min)

1. Va sur https://share.streamlit.io
2. Connecte-toi avec ton compte GitHub
3. "New app" → sélectionne ton dépôt
4. Fichier principal : `app.py`
5. Dans **"Advanced settings" → "Secrets"**, colle le contenu de `.streamlit/secrets.toml`
6. Clique **Deploy**

L'app est en ligne en 2 minutes. Tu obtiens une URL `https://xxx.streamlit.app`
à partager à toute ton équipe.

---

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `app.py` | Dashboard principal (login + données live) |
| `CyclableAPI.gs` | Script Google Sheets → expose les essais en JSON |
| `requirements.txt` | Dépendances Python |
| `.streamlit/secrets.toml` | Credentials (NE PAS mettre sur GitHub) |
| `cyclable_dashboard.py` | Ancien dashboard (données statiques, conservé en backup) |

---

## Mot de passe du dashboard

```
Ritmic26
```

---

## Questions / problèmes ?

Donne-moi le message d'erreur et je corrige immédiatement.
