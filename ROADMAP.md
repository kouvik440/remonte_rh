# Documentation roadmap Remonte RH

## Dépôt Git — 2026-10-27

Le premier commit local a été nettoyé avant publication : environnements installés, caches Python, sorties temporaires, base SQLite et bulletins privés exclus du suivi par `.gitignore`. Les fichiers locaux restent présents. Les dépendances sont décrites par `requirements.txt` et les fichiers npm. Une référence de sauvegarde locale conserve le commit initial.

Navigation SPA mise en place le 27 octobre 2026 : entrée unique, routes React sans extension (`/employes`, `/conges`, etc.), cadre commun conservé et conversion des anciennes adresses. Les fichiers HTML par module ont été supprimés. Détails et validations dans la roadmap frontend.

Les roadmaps backend et frontend sont maintenant séparées :

- [Roadmap backend](ROADMAP_backend.md)
- [Roadmap frontend](ROADMAP_frontend.md)

## Avancement du 2026-10-25

- Module 5 — Masse salariale : développement fonctionnel terminé, recette visuelle finale à clôturer.
- Module 6 — TGM : API, taux journaliers/horaires, coûts projets par employé et simulation temporaire de marge sur chiffre d’affaires saisi implémentés. Hypothèses de calendrier et d’historisation à valider.

## Module 7 — Feuilles de temps, 2026-10-25

Première version fonctionnelle : préparation des projets/tâches/affectations, saisie quotidienne en heures ou fractions de jour dans une feuille hebdomadaire, soumission, validation ou correction motivée et rapprochement avec les taux du module 6. Les heures validées alimentent les coûts projets. Recette complète sur une base temporaire, sans écriture dans la base active.
