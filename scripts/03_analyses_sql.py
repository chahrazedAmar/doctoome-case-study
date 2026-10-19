# =============================================================
# 03_analyses_sql.py
# ÉTAPE 3 : lancer les requêtes SQL (dossier sql/) avec DuckDB
# DuckDB = petite base de données qui lit directement les fichiers Parquet, sans serveur.
# Chaque résultat est affiché ET enregistré en CSV dans outputs/ (pour les graphiques et les slides).
# Lancer depuis doctoome_case :  python scripts/03_analyses_sql.py
# =============================================================

from pathlib import Path
import duckdb
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

# --- Chemins ---
PROJET = Path(__file__).parent.parent
CLEAN = PROJET / "data_clean"
SQL = PROJET / "sql"
OUT = PROJET / "outputs"
OUT.mkdir(exist_ok=True)

# --- 1. Ouvrir une base DuckDB en mémoire (rien n'est écrit sur le disque) ---
con = duckdb.connect()

# --- 2. Déclarer nos tables propres comme des "vues" SQL ---
# Une vue = un nom qu'on pourra utiliser dans FROM ... ; ici elle pointe vers un fichier Parquet.
# .as_posix() écrit le chemin avec des "/" : DuckDB les comprend aussi sous Windows.
vues = {
    "funnel": "funnel_sessions.parquet",
    "visitors": "visitors_clean.parquet",
    "outcomes": "outcomes_clean.parquet",
    "answers": "answers_clean.parquet",
}
for nom, fichier in vues.items():
    chemin = (CLEAN / fichier).as_posix()
    con.execute(f"CREATE VIEW {nom} AS SELECT * FROM read_parquet('{chemin}')")

# --- 3. Lancer chaque fichier .sql, dans l'ordre alphabétique (01, 02, ...) ---
for fichier_sql in sorted(SQL.glob("*.sql")):
    requete = fichier_sql.read_text(encoding="utf-8")   # lire le texte de la requête
    resultat = con.execute(requete).df()                # exécuter et récupérer un DataFrame pandas

    print("\n" + "=" * 70)
    print(fichier_sql.name)
    print("=" * 70)
    print(resultat.to_string(index=False))

    # Enregistrer en CSV : même nom que la requête, extension .csv
    resultat.to_csv(OUT / f"{fichier_sql.stem}.csv", index=False)

print("\nRésultats enregistrés dans outputs/")