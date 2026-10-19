#==================================================

#01_explorer.py 
#etape 1 découvrir les donnée 6 table et reperegae les problème de qualité de donnée
#on  va rien modifier , on regarde , on compte , on note.
#lancer depuis le dossier du projet :python scripts/01_explorer.py
#=============================================


from pathlib import Path # construire des chemin de fichier qui fonctionnne sur toute les ordinateurs
import json  # pour lire les colonnes de type json(alowwed answers )
import pandas as pd # pour lire les fichiers Parquet et faire des statistiques

#--- réglage d'affichage: voir toute les colonnes dans le terminal
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 20)

# chemin relatifs vers le dossier data/ ---
#path (__fichiers) = ce fichier ; . parent= dossier scripts/ ; parents encore= dossier du projet
#comme , ça le code marche chez n'importe qui
DATA = Path(__file__).parent.parent / "data" # chemin vers le dossier data/



#---1 charger les 6 fichier Parquet dans un dictionnaire---
#un dictionnaire= des pairees "nom: tableau pour eviter d'écire 6 fois  read_parquet."

noms=["visitors","sessions", "questionnaire_questions",
        "questionnaire_events", "questionnaire_answers", "questionnaire_outcomes"]
tables = {nom: pd.read_parquet(DATA / f"{nom}.parquet") for nom in noms}

# --- 2. Vue d'ensemble de chaque table ---
for nom, df in tables.items():
    print("\n" + "=" * 60)
    print(f"TABLE : {nom}  ->  {df.shape[0]} lignes, {df.shape[1]} colonnes")
    print(df.head(3))                                   # les 3 premières lignes
    print("\nValeurs manquantes par colonne :")
    print(df.isna().sum())                              # isna() = True si vide ; sum() compte les True

# On donne des noms courts aux tables pour la suite
v = tables["visitors"]
s = tables["sessions"]
q = tables["questionnaire_questions"]
e = tables["questionnaire_events"]
a = tables["questionnaire_answers"]
o = tables["questionnaire_outcomes"]

print("\n" + "#" * 60)
print("CONTRÔLES DE QUALITÉ")
print("#" * 60)

# --- 3. Valeurs écrites de plusieurs façons (catégories incohérentes) ---
# value_counts() compte combien de fois chaque valeur apparaît. dropna=False montre aussi les vides.
print("\n[3a] Genre :")
print(v["gender"].value_counts(dropna=False))
print("\n[3b] Région :")
print(v["region"].value_counts(dropna=False))
print("\n[3c] Source d'acquisition :")
print(s["acquisition_source"].value_counts(dropna=False))

# --- 4. Années de naissance : valeurs bizarres ou pics suspects ---
print("\n[4] Années de naissance les plus fréquentes :")
print(v["birth_year"].value_counts().head(5))           # un pic énorme sur une année = suspect
age = 2026 - v["birth_year"]
print("Visiteurs de moins de 18 ans :", (age < 18).sum())

# --- 5. Période réellement couverte (le sujet dit juin à août) ---
print("\n[5] Première et dernière session :")
print(s["session_started_at"].min(), "->", s["session_started_at"].max())

# --- 6. Doublons ---
# Une même session peut-elle répondre 2 fois à la même question ?
doublons_rep = a.duplicated(subset=["session_id", "question_number"]).sum()
print("\n[6] Réponses en double (même session + même question) :", doublons_rep)

# --- 7. Réponses hors de la liste autorisée ---
# json.loads transforme le texte '["yes","no"]' en vraie liste Python
autorisees = {row.question_id: json.loads(row.allowed_answers) for row in q.itertuples()}
hors_liste = a[~a.apply(lambda r: r["answer_value"] in autorisees[r["question_id"]], axis=1)]
print("[7] Réponses non autorisées :", len(hors_liste))

# --- 8. Cohérence entre tables (identifiants orphelins) ---
# isin() vérifie si chaque valeur existe dans l'autre table ; ~ veut dire "NON"
print("[8] Sessions dont le visiteur n'existe pas :", (~s["visitor_id"].isin(v["visitor_id"])).sum())
print("    Résultats dont la session n'existe pas :", (~o["session_id"].isin(s["session_id"])).sum())

# --- 9. Questionnaires : 5 réponses mais pas de résultat ? ---
nb_questions = a.groupby("session_id")["question_number"].nunique()   # nb de questions différentes par session
sessions_5_rep = nb_questions[nb_questions == 5].index
sans_resultat = (~sessions_5_rep.isin(o["session_id"])).sum()
print("[9] Sessions avec les 5 réponses mais sans résultat :", sans_resultat)

# --- 10. Campagne présente alors que la source est "direct" (incohérent) ---
print("[10] Sessions 'direct' avec une campagne :",
      (s["acquisition_source"].eq("direct") & s["campaign_name"].notna()).sum())