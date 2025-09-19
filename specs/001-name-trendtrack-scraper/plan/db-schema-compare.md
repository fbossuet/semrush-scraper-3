# Comparaison Schémas BDD (prod vs test)

Date: 2025-09-17

Fichiers générés:
- specs/001-name-trendtrack-scraper/plan/prod_schema.sql
- specs/001-name-trendtrack-scraper/plan/test_schema.sql
- specs/001-name-trendtrack-scraper/plan/schema_diff.txt

Résumé rapide:
- shops: Test ajoute des colonnes (dates, pixels, marchés, totaux) et durcit les types (monthly_visits INTEGER vs TEXT en Prod).
- analytics: Test durcit les types (INTEGER/NUMERIC), ajoute cpc, percent_branded_traffic en NUMERIC.
- index: Plus d’index visibles côté Prod; à harmoniser.

Écarts à valider (avec vous):
1) Types cibles (entiers/décimaux) communs Prod/Test
2) Colonnes additionnelles shops à officialiser en Prod
3) Standard d’indexation minimal commun
4) Format cible avg_visit_duration (INTEGER secondes vs TEXT MM:SS)
5) Type cible percent_branded_traffic (NUMERIC recommandé)
6) Conservation de analytics.traffic ou non
7) Introduction de cpc en Prod

Voir le diff complet: specs/001-name-trendtrack-scraper/plan/schema_diff.txt
