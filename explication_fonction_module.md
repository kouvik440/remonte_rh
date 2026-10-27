# Documentation fonctionnelle Remonte RH

Depuis le 27 octobre 2026, les modules frontend partagent une entrée unique, un routeur SPA et un cadre React persistant. Les pages sont des composants JSX accessibles par des routes sans extension (`/employes`, `/conges`, etc.). Les liens internes utilisent l'historique du navigateur ; les anciennes URL sont converties vers ces routes. Django continue de fournir l'API et de contrôler les permissions.

Les explications backend et frontend sont maintenant séparées :

- [Explication des fonctions backend](explication_fonction_backend.md)
- [Explication des fonctions frontend](explication_fonction_frontend.md)
