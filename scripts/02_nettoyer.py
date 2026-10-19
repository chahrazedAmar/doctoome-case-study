# =============================================================
# 02_nettoyer.py
# ÉTAPE 2 : nettoyer les données et créer des tables propres
# Règle d'or : on ne SUPPRIME presque rien, on CORRIGE et on SIGNALE (colonnes "flag").
# Chaque décision est notée en commentaire -> elle ira dans le README.
# Lancer depuis doctoome_case :  python scripts/02_nettoyer.py
# =============================================================

from pathlib import Path
import pandas as pd

# --- Chemins ---
PROJET = Path(__file__).parent.parent
DATA = PROJET / "data"              # données d'origine (on n'y touche JAMAIS)
CLEAN = PROJET / "data_clean"       # données nettoyées (créées par ce script)
CLEAN.mkdir(exist_ok=True)          # crée le dossier s'il n'existe pas

# --- Chargement ---
v = pd.read_parquet(DATA / "visitors.parquet")
s = pd.read_parquet(DATA / "sessions.parquet")
e = pd.read_parquet(DATA / "questionnaire_events.parquet")
a = pd.read_parquet(DATA / "questionnaire_answers.parquet")
o = pd.read_parquet(DATA / "questionnaire_outcomes.parquet")

# =============================================================
# A. VISITEURS
# =============================================================

# A1. Genre : 'F', 'Female', 'female' veulent dire la même chose -> on harmonise.
# .str.lower() met tout en minuscules, puis .replace() remplace les abréviations.
v["gender_clean"] = (v["gender"].str.lower()
                     .replace({"f": "female", "m": "male"})
                     .fillna("unknown"))          # vide -> "unknown" (on garde la ligne)

# A2. Région : même problème (majuscules, accents, tirets).
# On fabrique une "clé" simplifiée : minuscules + sans accents + espaces au lieu des tirets.
def cle_region(texte):
    if pd.isna(texte):
        return None
    t = texte.lower().replace("-", " ")
    for avec, sans in {"é": "e", "è": "e", "ô": "o", "î": "i"}.items():
        t = t.replace(avec, sans)
    return t

# On choisit l'écriture officielle = la plus fréquente pour chaque clé.
officielles = (v.dropna(subset=["region"])
                .assign(cle=lambda d: d["region"].map(cle_region))
                .groupby("cle")["region"]
                .agg(lambda x: x.value_counts().index[0]))   # valeur la plus fréquente
v["region_clean"] = v["region"].map(cle_region).map(officielles).fillna("unknown")

# A3. Âge : la période observée est 2026.
v["age"] = 2026 - v["birth_year"]

# Signaux d'alerte (flags) au lieu de supprimer :
v["flag_mineur"] = v["age"] < 18                              # mineurs : sujet RGPD en santé
v["flag_annee_suspecte"] = v["birth_year"].isin([1946, 2008]) # pics anormaux (valeur par défaut ? âge minimum contourné ?)

# Tranches d'âge pour l'analyse. pd.cut range chaque âge dans un intervalle.
v["age_group"] = pd.cut(v["age"],
                        bins=[0, 17, 24, 34, 44, 54, 64, 120],
                        labels=["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"])

# =============================================================
# B. SESSIONS
# =============================================================

# Hypothèse H3 : 'Google'/'google' = référencement naturel.
# Preuve : une pub payante est toujours traçable (100 % des google_ads ont une campagne,
# 0 % des 'google') et le profil est identique à google_organic (âge, mobile, complétion).
correspondance = {
    "Google": "google_organic", "google": "google_organic",
    "ChatGPT": "ai_assistant", "chatgpt": "ai_assistant", "AI Assistant": "ai_assistant",
    "facebook": "social", "instagram": "social",
}
s["source_clean"] = s["acquisition_source"].replace(correspondance)

# B2. Incohérence : une visite "direct" ne devrait pas avoir de campagne.
s["flag_direct_avec_campagne"] = (s["acquisition_source"] == "direct") & s["campaign_name"].notna()

# B3. Heure de Paris (les données sont en UTC = heure universelle).
s["started_paris"] = s["session_started_at"].dt.tz_convert("Europe/Paris")
s["date"] = s["started_paris"].dt.date
s["semaine"] = s["started_paris"].dt.tz_localize(None).dt.to_period("W").dt.start_time   # lundi de la semaine

# B4. Dernier jour incomplet : les données s'arrêtent le 2 août à 16h44 UTC.
s["flag_periode_incomplete"] = s["started_paris"] >= pd.Timestamp("2026-08-01", tz="Europe/Paris")

# =============================================================
# C. RÉPONSES : garder la DERNIÈRE réponse quand quelqu'un change d'avis
# =============================================================
# Preuve : avec la dernière réponse, on retrouve 100 % des résultats officiels (vérifié).
nb_avant = len(a)
a = a.sort_values("answered_at")                                     # ordre chronologique
a_clean = a.drop_duplicates(subset=["session_id", "question_number"], keep="last")
print(f"Réponses : {nb_avant} -> {len(a_clean)} ({nb_avant - len(a_clean)} changements d'avis retirés)")

# =============================================================
# D. TABLE FUNNEL : une ligne par session, une colonne par étape (True/False)
# =============================================================
f = s[["session_id", "visitor_id", "source_clean", "campaign_name", "device_type",
       "is_returning_visitor", "started_paris", "date", "semaine",
       "flag_direct_avec_campagne", "flag_periode_incomplete"]].copy()

# isin() renvoie True si la session apparaît dans la liste
debut = e.loc[e["event_type"] == "questionnaire_start", "session_id"]
vue_q1 = e.loc[(e["event_type"] == "question_view") & (e["question_number"] == 1), "session_id"]
f["start"] = f["session_id"].isin(debut)
f["vue_q1"] = f["session_id"].isin(vue_q1)
for n in range(1, 6):   # boucle de 1 à 5 : une colonne par question
    f[f"rep_q{n}"] = f["session_id"].isin(a_clean.loc[a_clean["question_number"] == n, "session_id"])
f["complete"] = f["session_id"].isin(o["session_id"])

# Anomalie de suivi : les 5 réponses mais pas de résultat enregistré
f["flag_5rep_sans_resultat"] = f["rep_q5"] & f[["rep_q1", "rep_q2", "rep_q3", "rep_q4"]].all(axis=1) & ~f["complete"]

# On ajoute les infos du visiteur (merge = jointure, comme JOIN en SQL)
f = f.merge(v[["visitor_id", "gender_clean", "region_clean", "age", "age_group",
               "flag_mineur", "flag_annee_suspecte"]],
            on="visitor_id", how="left")

# =============================================================
# E. ENREGISTRER les tables propres
# =============================================================
v.to_parquet(CLEAN / "visitors_clean.parquet")
s.to_parquet(CLEAN / "sessions_clean.parquet")
a_clean.to_parquet(CLEAN / "answers_clean.parquet")
o.to_parquet(CLEAN / "outcomes_clean.parquet")
f.to_parquet(CLEAN / "funnel_sessions.parquet")

# --- Petit résumé pour vérifier ---
print("\nGenre nettoyé :\n", v["gender_clean"].value_counts())
print("\nRégions nettoyées :", v["region_clean"].nunique(), "valeurs")
print("\nSources nettoyées :\n", s["source_clean"].value_counts())
print("\nFlags : mineurs =", v["flag_mineur"].sum(),
      "| années suspectes =", v["flag_annee_suspecte"].sum(),
      "| direct+campagne =", s["flag_direct_avec_campagne"].sum(),
      "| 5 réponses sans résultat =", f["flag_5rep_sans_resultat"].sum())
print("\nTable funnel :", f.shape, "-> enregistrée dans data_clean/")