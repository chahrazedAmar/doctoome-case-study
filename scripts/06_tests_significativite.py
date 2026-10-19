# =============================================================
# 06_tests_significativite.py
# ÉTAPE 6 : vérifier que les écarts observés ne sont pas dus au hasard.
#
# Outil : le test du chi-deux (khi-2), fourni par la bibliothèque scipy.
#   1. On construit un "tableau croisé" : une ligne par groupe, deux colonnes (oui / non).
#   2. Le test renvoie une p-value = la probabilité de voir un écart au moins aussi grand
#      SI les groupes étaient en réalité identiques (donc par pur hasard).
#   3. p < 0,05  -> l'écart est probablement réel.
#      p >= 0,05 -> on ne peut PAS affirmer qu'il existe (ce n'est pas la preuve qu'il n'existe pas).
# Attention : plus on fait de tests, plus un résultat "significatif" peut arriver par chance,
# et une p-value proche de 0,05 peut changer selon la définition choisie (voir le contrôle de sensibilité).
# Lancer depuis doctoome_case :  python scripts/06_tests_significativite.py
# =============================================================

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 70)

# --- Chemins (relatifs : le script marche sur n'importe quel ordinateur) ---
PROJET = Path(__file__).parent.parent
CLEAN = PROJET / "data_clean"
OUT = PROJET / "outputs"

# --- Chargement des tables nettoyées par 02_nettoyer.py ---
f = pd.read_parquet(CLEAN / "funnel_sessions.parquet")      # une ligne par session
a = pd.read_parquet(CLEAN / "answers_clean.parquet")         # dernière réponse par question
o = pd.read_parquet(CLEAN / "outcomes_clean.parquet")        # résultats

# On retire la période incomplète (1er-2 août), comme dans les requêtes SQL.
f = f[~f["flag_periode_incomplete"]].copy()

resultats = []   # on y range une ligne par test


def tester(nom, tableau):
    """Lance le test du chi-deux sur un tableau croisé et range le résultat."""
    chi2, p, _, _ = chi2_contingency(tableau)       # on garde le chi2 et la p-value
    resultats.append({
        "test": nom,
        "chi2": round(chi2, 1),
        "p_value": float(f"{p:.3g}"),
        # p < 0,01 : écart solide ; entre 0,01 et 0,05 : à la limite, à confirmer ; au-dessus : non significatif
        "conclusion": ("écart réel (p < 0,01)" if p < 0.01
                       else "limite : à confirmer (0,01 <= p < 0,05)" if p < 0.05
                       else "non significatif (p >= 0,05)"),
    })


def intervalle_confiance(serie):
    """Taux et intervalle de confiance à 95 % d'une série de True/False."""
    n = len(serie)
    p = serie.mean()
    marge = 1.96 * np.sqrt(p * (1 - p) / n)           # formule classique pour une proportion
    return p, p - marge, p + marge


# =============================================================
# A. Q4 : abandon selon l'appareil et la région
# =============================================================
# "A vu la Q4" = a répondu à la Q3 (vérifié : ce sont exactement les mêmes sessions).
q4 = f[f["rep_q3"]].copy()
q4["abandon_q4"] = ~q4["rep_q4"]                      # a vu la Q4 mais n'y a pas répondu

tester("Abandon Q4 : mobile / ordinateur / tablette", pd.crosstab(q4["device_type"], q4["abandon_q4"]))
tester("Abandon Q4 : selon la région (tous appareils)", pd.crosstab(q4["region_clean"], q4["abandon_q4"]))
mobile = q4[q4["device_type"] == "mobile"]
tester("Abandon Q4 : selon la région (mobile seulement)", pd.crosstab(mobile["region_clean"], mobile["abandon_q4"]))

print("=" * 70)
print("Taux d'abandon à la Q4 avec intervalle de confiance à 95 %")
print("=" * 70)
for appareil in ["mobile", "desktop", "tablet"]:
    p, bas, haut = intervalle_confiance(q4.loc[q4["device_type"] == appareil, "abandon_q4"])
    print(f"{appareil:8s} {100 * p:5.1f} %   [{100 * bas:.1f} ; {100 * haut:.1f}]")

# =============================================================
# B. Q4 : "rarely_or_never" selon l'âge (adultes, hors années de naissance suspectes)
# =============================================================
r = a[a["question_number"] == 4].merge(
    f[["session_id", "age", "flag_mineur", "flag_annee_suspecte"]], on="session_id")
r = r[~r["flag_mineur"] & ~r["flag_annee_suspecte"]]
r["rarement"] = r["answer_value"] == "rarely_or_never"
r["tranche"] = pd.cut(r["age"], bins=[0, 34, 54, 120], labels=["18-34", "35-54", "55+"])
tester("Q4 « rarement ou jamais » selon l'âge (3 tranches)", pd.crosstab(r["tranche"], r["rarement"]))

print("\n« Rarement ou jamais » à la Q4, par tranche d'âge fine :")
r["tranche_fine"] = pd.cut(r["age"], bins=[0, 24, 34, 44, 54, 64, 120],
                           labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
print((100 * r.groupby("tranche_fine", observed=True)["rarement"].mean()).round(1).to_string())

# =============================================================
# C. Sources : démarrer, puis finir
# =============================================================
# "Démarrer" = événement questionnaire_start (même définition que sql/08).
tester("Démarrage selon la source (toutes sources)", pd.crosstab(f["source_clean"], f["start"]))
demarres = f[f["start"]]
tester("Finir (parmi les démarrés) selon la source", pd.crosstab(demarres["source_clean"], demarres["complete"]))

ia_google = f[f["source_clean"].isin(["ai_assistant", "google_organic"])]
tester("Démarrage : assistant IA / Google organique", pd.crosstab(ia_google["source_clean"], ia_google["start"]))
d = ia_google[ia_google["start"]]
tester("Finir parmi les démarrés : assistant IA / Google organique", pd.crosstab(d["source_clean"], d["complete"]))

# Contrôle de sensibilité : "démarrer" = avoir VU la Q1 (893 démarrages n'affichent jamais la Q1).
d2 = ia_google[ia_google["vue_q1"]]
tester("Finir parmi ceux qui ont vu la Q1 : assistant IA / Google organique", pd.crosstab(d2["source_clean"], d2["complete"]))

print("\nTaux par source (assistant IA contre Google organique) :")
resume = ia_google.groupby("source_clean").agg(
    sessions=("start", "size"),
    pct_demarrent=("start", lambda x: round(100 * x.mean(), 1)))
resume["pct_finissent_parmi_demarres"] = (100 * d.groupby("source_clean")["complete"].mean()).round(1)
print(resume.to_string())

# =============================================================
# D. Pistes testées et écartées : campagnes, genre, jour, heure
# =============================================================
ads = demarres[demarres["source_clean"] == "google_ads"]
tester("Finir : les 3 campagnes Google Ads", pd.crosstab(ads["campaign_name"], ads["complete"]))
ads2 = ads[ads["vue_q1"]]       # contrôle de sensibilité : "démarrer" = avoir vu la Q1
tester("Finir : les 3 campagnes Ads (parmi ceux qui ont vu la Q1)", pd.crosstab(ads2["campaign_name"], ads2["complete"]))

genre = demarres[demarres["gender_clean"].isin(["female", "male"])]
tester("Finir : femmes / hommes", pd.crosstab(genre["gender_clean"], genre["complete"]))

res_genre = o.merge(f[["session_id", "gender_clean"]], on="session_id")
res_genre = res_genre[res_genre["gender_clean"].isin(["female", "male"])]
tester("Catégorie de résultat : femmes / hommes", pd.crosstab(res_genre["gender_clean"], res_genre["outcome_category"]))

heure = demarres["started_paris"].dt.hour
tester("Finir selon l'heure (4 tranches)", pd.crosstab(pd.cut(heure, [-1, 5, 11, 17, 23]), demarres["complete"]))
tester("Finir selon le jour de la semaine", pd.crosstab(demarres["started_paris"].dt.dayofweek, demarres["complete"]))

# =============================================================
# E. Résumé et enregistrement
# =============================================================
tableau = pd.DataFrame(resultats)
print("\n" + "=" * 70)
print("RÉSUMÉ DES TESTS (chi-deux)")
print("=" * 70)
print(tableau.to_string(index=False))

tableau.to_csv(OUT / "06_tests_significativite.csv", index=False)
print("\nRésultats enregistrés dans outputs/06_tests_significativite.csv")