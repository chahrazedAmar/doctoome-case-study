# =============================================================
# 05_analyse_linguistique.py
# ÉTAPE 5 : analyse linguistique (NLP) des questions + cohérence sémantique des réponses
# Idée : relier la FORME des questions (longueur, temporalité, négation...) au COMPORTEMENT
# (temps de réponse, abandon), puis vérifier si les réponses respectent le SENS des questions.
# Lancer depuis doctoome_case :  python scripts/05_analyse_linguistique.py
# =============================================================

from pathlib import Path
import json
import re
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

PROJET = Path(__file__).parent.parent
DATA = PROJET / "data"
CLEAN = PROJET / "data_clean"
OUT = PROJET / "outputs"

q = pd.read_parquet(DATA / "questionnaire_questions.parquet")
e = pd.read_parquet(DATA / "questionnaire_events.parquet")
a = pd.read_parquet(CLEAN / "answers_clean.parquet")      # dernière réponse par question
o = pd.read_parquet(CLEAN / "outcomes_clean.parquet")

# =============================================================
# A. CARACTÉRISTIQUES LINGUISTIQUES DE CHAQUE QUESTION
# =============================================================
def caracteristiques(texte, reponses_json):
    """Calcule des indicateurs simples sur le texte d'une question."""
    mots = re.findall(r"[A-Za-z0-9']+", texte.lower())          # découpe en mots (tokenisation simple)
    reponses = json.loads(reponses_json)
    return pd.Series({
        "nb_mots": len(mots),
        # Temporalité : "ever" = fait acquis (ne peut pas redevenir faux) ; "last 3 months"/"usually" = état qui varie
        "temporalite": ("fait acquis (ever)" if "ever" in mots
                        else "fait acquis (been diagnosed)" if "diagnosed" in mots and "been" in mots
                        else "habitude (usually)" if "usually" in mots
                        else "période récente (last)" if "last" in mots else "autre"),
        "negation_ou_exclusion": any(m in mots for m in ["not", "without", "never"]),
        "plusieurs_idees (or/and)": "or" in mots or "and" in mots,   # question "double" = 2 idées en 1
        "seuil_a_calculer": bool(re.search(r"at least \d+", texte.lower())),  # oblige à calculer ("at least 30 minutes")
        "nb_reponses": len(reponses),
        "longueur_moy_reponses": round(sum(len(r) for r in reponses) / len(reponses), 1),
    })

ling = q.set_index("question_number").apply(
    lambda r: caracteristiques(r["question_text"], r["allowed_answers"]), axis=1)

# =============================================================
# B. COMPORTEMENT : temps de réponse médian et taux d'abandon par question
# =============================================================
vue = e[e["event_type"] == "question_view"].groupby(["session_id", "question_number"])["event_timestamp"].min()
rep = e[e["event_type"] == "question_answer"].groupby(["session_id", "question_number"])["event_timestamp"].min()
temps = (rep - vue).dt.total_seconds().dropna()                       # secondes entre affichage et 1re réponse
ling["temps_median_s"] = temps.groupby(level="question_number").median().round(1)

# Abandon à la question n = parmi ceux qui ont vu la question, % qui n'y répondent pas
vus = vue.reset_index().groupby("question_number")["session_id"].nunique()
repondus = a.groupby("question_number")["session_id"].nunique()
ling["abandon_pct"] = (100 * (1 - repondus / vus)).round(1)

print("=" * 70)
print("A+B. FORME DES QUESTIONS vs COMPORTEMENT")
print("=" * 70)
print(ling.to_string())

# =============================================================
# C. COHÉRENCE SÉMANTIQUE 1 : contradiction entre Q1 et Q5 (même session)
# Q1 = "diagnostiqué(e) diabète type 2 ?" ; Q5 = "glycémie élevée SANS avoir reçu de diagnostic ?"
# Répondre OUI aux deux est contradictoire... ou révèle une ambiguïté de portée de "without".
# =============================================================
large = a.pivot(index="session_id", columns="question_number", values="answer_value")
contradiction = ((large[1] == "yes") & (large[5] == "yes")).sum()
diag_q5 = large.loc[large[1] == "yes", 5].notna().sum()
print("\n" + "=" * 70)
print("C. CONTRADICTION Q1 / Q5")
print("=" * 70)
print(f"Personnes 'diagnostiquées' (Q1=yes) qui ont quand même répondu à Q5 : {diag_q5}")
print(f"Dont Q5=yes ('glycémie élevée sans diagnostic') : {contradiction} "
      f"({100 * contradiction / diag_q5:.0f} %)")

# =============================================================
# D. COHÉRENCE SÉMANTIQUE 2 : un "fait acquis" ne peut pas passer de OUI à NON
# Un même visiteur qui revient : sa réponse à "Have you EVER been told..." devrait rester OUI.
# Comparaison avec les questions qui peuvent légitimement changer (Q2 = 3 derniers mois).
# =============================================================
print("\n" + "=" * 70)
print("D. UN MÊME VISITEUR RÉPOND-IL PAREIL D'UNE VISITE À L'AUTRE ?")
print("=" * 70)
lignes = []
for n in [1, 2, 3, 5]:
    x = a[a["question_number"] == n]
    nb_sessions = x.groupby("visitor_id")["session_id"].nunique()
    revenants = nb_sessions[nb_sessions > 1].index                    # visiteurs ayant répondu plusieurs fois
    ens = x[x["visitor_id"].isin(revenants)].groupby("visitor_id")["answer_value"].agg(set)
    oui_et_non = ens.apply(lambda s: "yes" in s and "no" in s)
    lignes.append({"question": f"Q{n}", "temporalite": ling.loc[n, "temporalite"],
                   "visiteurs_revenus": len(revenants),
                   "ont_dit_oui_ET_non": int(oui_et_non.sum()),
                   "pct": round(100 * oui_et_non.mean(), 1)})
coherence = pd.DataFrame(lignes)
print(coherence.to_string(index=False))
print("-> Pour un fait acquis (Q1, Q3, Q5), le % devrait être proche de 0.")

# =============================================================
# E. RÈGLE DE CLASSEMENT RECONSTITUÉE : comment "not_sure" est-il traité ?
# =============================================================
pas_sur = {f"Q{n}": float(round(100 * (large[n] == "not_sure").mean(), 1)) for n in [2, 3, 5]}
print("\n" + "=" * 70)
print("E. RÉPONSES 'not_sure' (comptées comme 'no' par la règle de classement)")
print("=" * 70)
print(pas_sur)

# =============================================================
# F. RÈGLE DE CLASSEMENT RECONSTITUÉE (rétro-ingénierie)
# Hypothèse : Q1=yes -> declared_diagnosed ; sinon on compte 1 point par réponse "à risque"
# (Q2 yes, Q3 yes, Q4 rarely_or_never, Q5 yes) ; 2 points ou plus -> possible_risk.
# =============================================================
points = ((large[2] == "yes").astype(int) + (large[3] == "yes")
          + (large[4] == "rarely_or_never") + (large[5] == "yes"))
predit = pd.Series("no_current_indication", index=large.index)
predit[points >= 2] = "possible_risk"
predit[large[1] == "yes"] = "declared_diagnosed"
reel = o.set_index("session_id")["outcome_category"]
taux = (predit.reindex(reel.index) == reel).mean()
print("\n" + "=" * 70)
print("F. RÈGLE DE CLASSEMENT RECONSTITUÉE")
print("=" * 70)
print(f"La règle reproduit {100 * taux:.1f} % des résultats officiels")
print("-> 'not_sure' et 'prefer_not_to_say' comptent comme 'no' ; l'âge n'entre pas dans le calcul.")

# --- Enregistrer pour les slides ---
ling.to_csv(OUT / "07_linguistique_questions.csv")
coherence.to_csv(OUT / "08_coherence_visiteurs.csv", index=False)
print("\nRésultats enregistrés dans outputs/")