# Roadmap Remonte RH

Dernière mise à jour : 2026-10-27

Ce document décrit l'état vérifié du backend. Le stockage bancaire chiffré est activé depuis le 23 octobre 2026 ; sa portée est décrite au module 3.

### Départements du module 1 — mise à jour du 2026-10-27

- Le CRUD existant `GET/POST /api/departements/` et `GET/PUT/DELETE /api/departements/{id}/` est utilisé par l’écran frontend des départements. Seul le nom, obligatoire et unique, est saisi. `DepartementService` génère un code interne `DEP_` suivi de 16 caractères hexadécimaux à la création ; la contrainte d'unicité du modèle est conservée. Le code est en lecture seule dans le serializer et ne change pas lors d'un renommage. Les anciens codes sont conservés, sans migration de données.
- Architecture conservée : vues → `DepartementService` → interface du repository → `DepartementRepository` → modèle. Aucun accès ORM ajouté aux vues ou services.
- Migration 0043 appliquée sur PostgreSQL : droits `departement.read/create/update/delete` pour `ADMIN_RH` et `FRONTEND_MODULE_1_EMPLOYES_ACCES`. Le profil module 1 passe à 22 droits ; le profil module 5 reste à deux droits de lecture. Aucune attribution de rôle à un employé.
- Suppression : les employés restent en base, leur département passe à null (`SET_NULL`). Les snapshots historiques des paies ne sont pas modifiés.
- Vérifications du 27 octobre : sept tests départements PostgreSQL réussis, couvrant aussi la génération de codes distincts, le refus de leur modification et la conservation des anciens codes. Build Vite et création/modification dans le navigateur à 1440 et 390 px réussis. Les essais utilisent des bases de test ; les départements de la base active n’ont pas été modifiés.

## Module 1 â€” Gestion des employÃ©s

### Ã‰tat du backend

- Les routes `GET/POST /api/employes/` et `GET/PUT/DELETE /api/employes/{id}/` permettent de consulter et gÃ©rer les comptes employÃ©s, avec des permissions dÃ©diÃ©es.
- Le modÃ¨le et le serializer couvrent les informations personnelles, les dates d'entrÃ©e et de sortie, le statut, le dÃ©partement et les rÃ´les. Les contrats sont gÃ©rÃ©s sÃ©parÃ©ment par `/api/contrats/` et peuvent conserver plusieurs pÃ©riodes contractuelles pour un employÃ©.
- La liste des employÃ©s ne propose actuellement pas les filtres demandÃ©s par le cahier des charges (dÃ©partement, poste, statut et contrat). Le modÃ¨le employÃ© ne porte pas de poste ni de responsable hiÃ©rarchique.
- Les contrats historisent certaines pÃ©riodes et leurs types, mais il n'existe pas de fonctionnalitÃ© dÃ©diÃ©e retraÃ§ant les Ã©volutions de poste et de contrat dans une fiche employÃ©.

### Travaux restant Ã  couvrir

Ajouter les filtres d'annuaire prÃ©vus au cahier des charges, dÃ©finir oÃ¹ sont gÃ©rÃ©s le poste et le responsable hiÃ©rarchique, puis complÃ©ter l'historique des Ã©volutions de poste et de contrat. VÃ©rifier les permissions de consultation avec les profils RH, paie, manager et employÃ© avant de dÃ©clarer le module conforme.

## Module 2 â€” CongÃ©s et absences

### Identité des demandeurs — 2026-10-27

- `DemandeAbsenceSerializer` expose le prénom et le nom de l'employé en lecture seule dans la liste et les réponses de mutation. Le serializer de détail hérite de ces champs. Le repository charge déjà l'employé avec `select_related`.
- Le périmètre de consultation reste personnel, ou global avec le droit de décision existant. Aucun droit supplémentaire ni migration n'est nécessaire.
- Les 23 tests `DemandeAbsenceAccessTests` passent sur PostgreSQL, dont la vérification des noms dans la liste personnelle et les demandes reçues, avec maintien du filtrage des accès.

Architecture utilisÃ©e : vue/API â†’ service â†’ interface du repository â†’ repository Django â†’ modÃ¨le. Les serializers dÃ©finissent les champs acceptÃ©s et renvoyÃ©s.

### Types de congÃ© â€” terminÃ©

- `TypeConge` contient le code, le libellÃ©, le droit annuel en jours, le caractÃ¨re payÃ© et l'Ã©tat actif.
- Le CRUD passe par `TypeCongeSerializer`, `CongeService` et `TypeCongeRepository`.
- Routes : `GET/POST /api/conges/types/`, puis `GET/PUT/DELETE /api/conges/types/{id}/`.
- Le rÃ´le RH reÃ§oit des permissions de gestion spÃ©cifiques par migration ; aucun bypass cachÃ© par nom de rÃ´le n'est requis pour ces opÃ©rations.

### Demandes d'absence â€” terminÃ©

- `DemandeAbsence` est l'unique modÃ¨le de demande. Il rÃ©fÃ©rence `Employe` et `TypeConge` et contient les dates, le motif, le statut, les dates de demande/dÃ©cision et le valideur.
- Le serializer rend le statut, le valideur et les dates systÃ¨me non modifiables par le client. La vue associe une nouvelle demande Ã  l'employÃ© connectÃ©.
- L'interface/repository/service portent l'accÃ¨s aux donnÃ©es et les rÃ¨gles mÃ©tier ; les vues ne gÃ¨rent que HTTP et permissions.
- Routes : `GET/POST /api/demandes-absence/` et `GET/PUT/DELETE /api/demandes-absence/{id}/`.
- Chaque création, modification et validation vérifie le quota annuel par année, sur les jours du lundi au vendredi. Les demandes `EN_ATTENTE` réservent les jours pour éviter les dépassements par demandes multiples ; les dates déjà couvertes ne sont comptées qu'une fois. La validation refuse une demande devenue hors quota.
- Le contrôle verrouille la ligne de l'employé durant la transaction pour sérialiser les demandes concurrentes. Le champ employé est en lecture seule lors des mises à jour.
- Les anciennes lignes `DemandeConge` ont Ã©tÃ© copiÃ©es vers `DemandeAbsence` par migration, puis le modÃ¨le et les anciennes routes ont Ã©tÃ© supprimÃ©s. La migration 0013 effectue ce transfert.

### Circuit de dÃ©cision â€” terminÃ©

- Valider et refuser sont des actions distinctes ; seules les demandes `EN_ATTENTE` peuvent changer d'Ã©tat.
- Le service renseigne `statut`, `date_validation` et `valideur`. La permission `demande_absence.update` autorise la dÃ©cision.
- Routes : `POST /api/demandes-absence/{id}/valider/` et `POST /api/demandes-absence/{id}/refuser/`. Aucun body n'est nÃ©cessaire.

### Soldes â€” terminÃ©

- `SoldeConge` reprÃ©sente un droit par employÃ©, type et annÃ©e ; `acquis` est le quota annuel et `pris` le cumul des jours consommÃ©s.
- Le repository recherche toutes les demandes validÃ©es qui chevauchent l'annÃ©e. Le service compte les jours du lundi au vendredi et dÃ©duplique les dates qui se chevauchent.
- Ã€ la validation, le service recalcule et persiste `pris`. La migration 0016 a recalculÃ© les soldes dÃ©jÃ  prÃ©sents.
- Routes : `GET/POST /api/soldes-conge/`. La lecture prend `annee` et Ã©ventuellement `employe`; la crÃ©ation exige `employe`, `type_conge`, `annee` et `acquis`. `pris` est calculÃ©, ne pas l'envoyer.

### Planning d'Ã©quipe â€” API des Ã©vÃ©nements en place

- `GET /api/planning/` renvoie les Ã©vÃ©nements de planning sur une pÃ©riode. ParamÃ¨tres requis : `date_debut`, `date_fin` ; filtres facultatifs : `departement`, `employe`.
- La rÃ©ponse distingue `ABSENCE` (demande validÃ©e) et `PRESENCE_PREVUE` (employÃ© actif, jour ouvrÃ© couvert par sa pÃ©riode d'emploi, sans absence validÃ©e ce jour-lÃ ). Elle contient les dates, l'employÃ© et son dÃ©partement, sans exposer le motif. Les demandes en attente, refusÃ©es ou annulÃ©es ne sont pas incluses.
- La route exige `demande_absence.read`. Un utilisateur sans `demande_absence.update` ne voit que ses Ã©vÃ©nements ; un utilisateur possÃ©dant aussi `demande_absence.update` peut consulter tous les employÃ©s et filtrer par dÃ©partement ou employÃ©. Cette consultation transversale n'est pas limitÃ©e automatiquement au dÃ©partement du gestionnaire : l'accÃ¨s dÃ©pend des permissions attribuÃ©es, pas du seul nom du rÃ´le.
- La prÃ©sence renvoyÃ©e est prÃ©visionnelle, pas un pointage rÃ©el. Il n'existe pas encore de source de donnÃ©es de prÃ©sence/pointage.

### Notifications â€” reportÃ©es

- Les notifications Ã  l'employÃ© lors de la crÃ©ation, validation ou du refus restent Ã  implÃ©menter.

## Module 3 — Données bancaires et juridiques

### Accès bancaires existants

Le CRUD `/api/coordonnees-bancaires/` conserve le contrôle propriétaire et le droit transversal `coordonnees_bancaires.manage`. Le serializer ajoute les nom/prénom de l'employé pour la liste. Le repository charge les relations nécessaires. La réaffectation d'une fiche existante reste interdite.

### Références documentaires sécurisées — 2026-10-23

- Nouvelle permission `document.manage` créée par la migration 0032 et attribuée à ADMIN_RH. La lecture personnelle utilise `document.read`; la lecture globale et les écritures exigent aussi `document.manage`, en complément du droit CRUD correspondant.
- Les listes et détails de documents et de liaisons document-employé sont limités au propriétaire hors gestionnaire. Le même droit transversal protège les écritures sur les liaisons, pour empêcher une auto-attribution d'un document tiers.
- Les vues délèguent aux services puis interfaces/repositories ; aucune requête ORM ajoutée aux vues. Création et modification des documents/associations transactionnelles. Dates d'expiration antérieures au dépôt refusées.
- Codes de types de document automatiques et immuables via l'API. Types utilisés protégés contre la suppression, types inactifs refusés pour une nouvelle référence.
- Profil FRONTEND_MODULE_3_DOSSIERS_BANCAIRES_JURIDIQUES créé avec 15 droits de gestion : CRUD bancaire et manage, CRUD document et manage, CRUD type_document, employe.read. Aucun compte n'a reçu ce profil automatiquement. Les routes de liaison ne sont pas utilisées directement par cet écran, donc pas de droits document_employe ajoutés au profil.

### Chiffrement activé — 2026-10-23

Le stockage des champs IBAN, BIC et SWIFT est chiffré (Fernet), avec empreinte HMAC pour l'unicité de l'IBAN. La migration 0033 est appliquée sur PostgreSQL local : deux fiches conservées et vérifiées par comparaison à la sauvegarde chiffrée. La clé est chargée hors dépôt ; voir [BANK_DATA_ENCRYPTION.md](BANK_DATA_ENCRYPTION.md). Les réponses API autorisées restent lisibles ; les permissions sont inchangées.

Document.fichier reste une référence textuelle ; aucune API de stockage privé ou de téléchargement de justificatifs n'existe pour ce module. Aucun lien de fichier n'est publié par le frontend. Les champs fiscaux personnels existants restent gérés dans la fiche employé, sans nouveau module fiscal.

### Vérifications

133 tests core réussis sur SQLite isolé et 15 tests chiffrement/accès bancaire réussis sur PostgreSQL isolé. Migration depuis des données en clair vérifiée sur base temporaire. Migration 0033 appliquée sur PostgreSQL local, deux fiches converties et contrôlées sans perte. Parcours interactif navigateur non vérifié pendant cette intervention.

## Étape actuelle — 2026-10-25

**Modules 6 et 7 — TGM, feuilles de temps et rapprochement : premières versions intégrées et vérifiées.** Les heures déclarées, soumises puis validées alimentent le calcul des coûts projets et la simulation de marge du module 6. Le module 5 est terminé fonctionnellement ; sa recette visuelle complète reste à clôturer. Le calendrier lundi-vendredi, les contrats actuels et la portée de la marge personnel restent les hypothèses du TGM. Voir les sections des modules 6/7 et leurs bilans du 2026-10-25.

Le module 7 dispose désormais de son interface de saisie, soumission, décision, préparation des projets et rapprochement des coûts. Les temps validés alimentent le module 6. Les bilans précédents sont conservés dans les sections correspondantes.

## Module 7 â€” Feuilles de temps

**Interface opérationnelle depuis le 2026-10-25 ; lien avec les coûts du module 6 vérifié en recette isolée.**

### Intégration frontend et durées en jours — 2026-10-25

- Les routes existantes `/api/feuilles-temps/`, `/{id}/`, `/projets/`, `/a-valider/`, `/{id}/soumettre/`, `/{id}/valider/` et `/{id}/refuser/` sont reliées à l’interface. Les lectures/écritures personnelles utilisent l’employé authentifié ; la file et les décisions exigent `feuille_temps.decide`. Les coûts exigent séparément `paie.read`.
- Une ligne d’entrée doit contenir exactement une durée : `heures` (0,01 à 24) ou `jours` (0,01 à 1), avec deux décimales maximum. Le service convertit les jours en heures selon l’unique contrat couvrant la date, puis vérifie le total quotidien de toutes les lignes. Contrat absent, chevauchement, horaire manquant, durée trop petite après arrondi ou dépassement refusés. Les modèles et anciennes entrées en heures sont conservés.
- La réponse de feuille ajoute `total_heures`, `jours_saisis` (dates distinctes), le matricule et les noms du décideur. Ces totaux sont calculés sur les lignes préchargées, sans exposer de données de paie.
- Modification, soumission et suppression personnelles verrouillent désormais la feuille en transaction, comme les décisions du manager. Une modification d’une feuille validée retire sa validation ; la soumission est interdite sans ligne. Les semaines dépassant la fin du calendrier sont refusées proprement.
- `/api/analyses/couts-projets/` ajoute `rapprochement` par projet, employé et mois avec taux horaire chargé affichable, heures et coût. Le coût conserve le taux précis avant arrondi final. Les brouillons et feuilles soumises sont exclus ; une correction après validation les retire automatiquement du rapport. Les coûts incomplets restent explicitement indisponibles.
- Le frontend réutilise les API projets, tâches et affectations, avec leurs permissions existantes. Aucun rôle ou compte actif n’est modifié ; aucun modèle ni migration supplémentaire nécessaire.
- La validation est centrale selon la permission de décision ; un périmètre hiérarchique par manager, les notifications, le gel historique des taux et la clôture définitive des feuilles restent hors de cette première version. Le coût obtenu correspond aux heures déclarées et validées valorisées par un TGM estimé, sans intégrer les autres charges d’un projet.


### Ã‰tape 1 â€” Projets, tÃ¢ches et affectations

Les modèles Projet, TacheProjet et AffectationProjet, leurs routes CRUD et permissions sont câblés. Les migrations 0027 à 0029 sont appliquées sur PostgreSQL de test et les 13 tests ciblés feuilles de temps/coûts ont réussi le 2026-10-22. La base de développement et les tests Postman manuels restent à vérifier.

### Ã‰tape 2 â€” ModÃ¨le hebdomadaire et horaire contractuel

Les modÃ¨les `FeuilleTemps` et `LigneFeuilleTemps` sont implÃ©mentÃ©s. Une feuille appartient Ã  un employÃ© et Ã  une semaine commenÃ§ant le lundi ; une contrainte limite Ã  une feuille par employÃ© et par semaine. Ses Ã©tats sont `BROUILLON`, `SOUMISE` et `VALIDEE`. Les lignes portent une date, un projet, une tÃ¢che, un nombre d'heures et un commentaire. La validation mÃ©tier du modÃ¨le refuse une semaine ne commenÃ§ant pas le lundi, une ligne hors de la semaine ou une tÃ¢che n'appartenant pas au projet. Les projets et tÃ¢ches liÃ©s Ã  des lignes existantes ne peuvent pas Ãªtre supprimÃ©s.

Le champ `Contrat.heures_journalieres` reprÃ©sente l'horaire quotidien prÃ©vu ; l'API de contrat l'exige lors de la crÃ©ation ou mise Ã  jour et accepte une valeur de 0,01 Ã  24,00 heures. Il reste nullable en base pour prÃ©server les anciens contrats : ils doivent Ãªtre renseignÃ©s avant de contrÃ´ler une saisie. L'API de saisie vÃ©rifie le total de chaque journÃ©e par rapport Ã  l'horaire du seul contrat couvrant cette date et refuse un contrat absent, un horaire non renseignÃ© ou plusieurs contrats couvrant la journÃ©e.

La migration `0028_feuille_temps_and_contrat_hours.py` crÃ©e ces modÃ¨les et ajoute le champ au contrat.

### Ã‰tape 3 â€” API de saisie et soumission hebdomadaire (implÃ©mentÃ©e)

Les endpoints `/api/feuilles-temps/`, `/api/feuilles-temps/{id}/` et `/api/feuilles-temps/{id}/soumettre/` sont ajoutÃ©s selon le pattern serializer â†’ vue â†’ service â†’ interface/repository â†’ modÃ¨les. L'employÃ© est dÃ©terminÃ© par l'authentification, jamais par le JSON ; chaque compte ne consulte et ne modifie que ses propres feuilles.

- `GET /api/feuilles-temps/?semaine_debut=AAAA-MM-JJ` filtre par semaine ; `?date_travail=AAAA-MM-JJ` filtre par jour.
- `POST /api/feuilles-temps/` crÃ©e un brouillon avec ses lignes en une transaction.
- `GET/PUT/DELETE /api/feuilles-temps/{id}/` consulte, remplace toutes les lignes d'un brouillon, ou supprime un brouillon.
- `POST /api/feuilles-temps/{id}/soumettre/` soumet une feuille non vide. Aucun statut ni employÃ© n'est acceptÃ© dans le body.
- Les lignes doivent rester dans la semaine, relier une tÃ¢che au projet sÃ©lectionnÃ©, utiliser un projet/tÃ¢che actifs et un projet affectÃ© Ã  l'employÃ©. Le total journalier est plafonnÃ© par l'horaire du contrat.
- Une feuille soumise est verrouillÃ©e jusqu'Ã  une dÃ©cision. Modifier une feuille validÃ©e la remet en brouillon pour imposer une nouvelle soumission/validation.

Les migrations 0027 à 0029 et les parcours ciblés ont été vérifiés sur PostgreSQL de test le 2026-10-22 ; la base de développement est restée inchangée.

### Ã‰tape 4 â€” DÃ©cision manager (implÃ©mentÃ©e, tests rÃ©ussis sur SQLite)

La migration `0029_feuille_temps_decision.py` ajoute la date de dÃ©cision, le valideur et le motif de refus, ainsi que la permission dÃ©diÃ©e `feuille_temps.decide` (attribuÃ©e au rÃ´le `ADMIN_RH` existant Ã  la migration). Cette permission est nÃ©cessaire pour consulter la file et dÃ©cider ; elle peut Ãªtre attribuÃ©e Ã  d'autres rÃ´les depuis la gestion des permissions.

- `GET /api/feuilles-temps/a-valider/` retourne uniquement les feuilles `SOUMISE`.
- `POST /api/feuilles-temps/{id}/valider/` valide une feuille soumise et conserve le dÃ©cideur et la date.
- `POST /api/feuilles-temps/{id}/refuser/` exige un corps JSON `{ "motif": "..." }`, conserve la dÃ©cision et remet la feuille en `BROUILLON`.
- Les dÃ©cisions ne s'appliquent qu'aux feuilles soumises. Une nouvelle soumission efface les mÃ©tadonnÃ©es de refus prÃ©cÃ©dentes ; une modification aprÃ¨s validation invalide l'ancienne dÃ©cision.

Les décisions sont transactionnelles et verrouillent la feuille lors du changement de l'état. Les tests ciblés de décision ont réussi sur PostgreSQL de test le 2026-10-22 ; la base de développement est restée inchangée.

### Ã‰tape 6 â€” Calcul backend des coÃ»ts par projet et tÃ¢che (implÃ©mentÃ©, tests rÃ©ussis)

Mise à jour du 2026-10-25 : le module 6 remplace le diviseur fixe `/ 8` décrit dans le bilan historique ci-dessous par les heures prévisionnelles contractuelles. Les horaires absents ou ambigus produisent un coût incomplet. Voir la section Module 6 pour le comportement actuel.

`GET /api/analyses/couts-projets/?date_debut=AAAA-MM-JJ&date_fin=AAAA-MM-JJ` agrÃ¨ge uniquement les lignes dont la feuille est `VALIDEE`, par projet et tÃ¢che. Pour chaque employÃ© et mois concernÃ©, le service rÃ©utilise le TGM chargÃ© journalier et calcule le taux horaire comme `TGM chargÃ© journalier / 8`. Ce diviseur fixe de huit heures est une hypothÃ¨se de calcul, pas une rÃ¨gle du cahier des charges ; il ne tient pas compte de `Contrat.heures_journalieres` ni des horaires Ã  temps partiel. La pertinence de cette formule doit Ãªtre validÃ©e avant d'utiliser le rÃ©sultat comme coÃ»t rÃ©el. Le coÃ»t estimÃ© est ensuite calculÃ© Ã  partir des heures validÃ©es.

La rÃ©ponse distingue le coÃ»t calculable du coÃ»t estimÃ© complet. Si le TGM manque pour tout ou partie des heures, `cout_estime` est `null`, `cout_calculable` expose uniquement le sous-total chiffrable, et `heures_sans_tgm`/`cout_complet` signalent l'incomplÃ©tude. L'accÃ¨s est protÃ©gÃ© par `paie.read`. Cette estimation ne remplace pas une comptabilitÃ© analytique validÃ©e.

Des tests couvrent l'inclusion des seules feuilles validÃ©es, l'application du taux mensuel, l'absence de TGM et la permission. `manage.py check` passe, aucune migration modÃ¨le n'est manquante, et les 93 tests backend rÃ©ussissent sur SQLite en mÃ©moire. Les 13 tests ciblés feuilles de temps/coûts ont réussi le 2026-10-22 sur PostgreSQL (`test_remonte_rh`) ; la base de développement n'a pas été modifiée.

### Ã‰tape 7 â€” Validation backend

La suite backend a Ã©tÃ© exÃ©cutÃ©e : 93/93 tests rÃ©ussis sur une base SQLite en mÃ©moire. Le runner a appliquÃ© les migrations `0027` Ã  `0029` Ã  cette base temporaire, puis l'a dÃ©truite. Le 2026-10-22, 13 tests ciblés ont validé migrations et parcours d'API sur PostgreSQL (`test_remonte_rh`). La base de développement n'a pas été modifiée.

## Vérifications

- Suite backend vÃ©rifiÃ©e le 2026-10-22 : `USE_SQLITE=1 python manage.py test core.tests` â€” 93 tests rÃ©ussis ; le runner a crÃ©Ã© une base SQLite en mÃ©moire et l'a dÃ©truite Ã  la fin.
- VÃ©rification de l'Ã©tat des modÃ¨les : `USE_SQLITE=1 python manage.py check` et `USE_SQLITE=1 python manage.py makemigrations --check --dry-run core` â€” aucune erreur, aucun changement de migration manquant.
- Les migrations 0027 à 0029 sont appliquées dans la base PostgreSQL de test `test_remonte_rh`; la base de développement n'a pas été modifiée.
- Les migrations jusqu'Ã  0018 sont appliquÃ©es dans la base de dÃ©veloppement ; `makemigrations --check --dry-run` ne dÃ©tecte aucun changement de modÃ¨le manquant.

## Module 4 â€” Gestion de la paie et ordres de virement

### Écran frontend de gestion des paies — 2026-10-23

- Identité en lecture seule ajoutée à `PaieSerializer` (nom, prénom, matricule). Le détail utilise `select_related` dans `PaieRepository`, comme la liste, sans requête d'identité supplémentaire. Architecture vue → service → interface → repository conservée.
- Migration 0034 appliquée sur PostgreSQL local : création du rôle `FRONTEND_MODULE_4_PAIE_VIREMENTS`, avec `paie.read/create/update/delete` et `employe.read`. Aucun employé affecté automatiquement. Les contrôles existants restent la source de vérité : `paie.update` pour les actions métier et `paie.read` pour la consultation globale de gestion.
- Vérifications : 138 tests core réussis sur SQLite isolé, puis 6 tests ciblés sur PostgreSQL isolé (profil, droits, identité, requêtes, CRUD brouillon). Contrôles Django et absence de migrations de modèle manquantes vérifiés. Les paies de la base active n'ont pas été modifiées par les tests.
- Prochaine étape frontend : gestion des variables ; règles et suivi des ordres sont implémentés. Cette intervention ne crée aucun paiement ni fichier bancaire. Validation navigateur toujours non effectuée.

### Ã‰tat actuel

- `Contrat.salaire_base` fournit dÃ©jÃ  un montant de base liÃ© Ã  un employÃ© et Ã  une pÃ©riode de contrat.
- `Paie` conserve période, brut, net, coût employeur, cotisations, statut, devise, audit et snapshot de calcul. Le champ est_simulation a été retiré ; le champ est_fictif du profil est également supprimé par la migration 0035. Les calculs établis restent immuables.
- `OrdreVirement` enregistre pÃ©riode, statut, date de gÃ©nÃ©ration, date de traitement et employÃ©.
- Un ordre traitÃ© ne peut Ãªtre associÃ© qu'Ã  une seule paie ; le service refuse sa rÃ©utilisation.
- Le workflow d'ordre est encadrÃ© : crÃ©ation en `GENERE`, puis actions dÃ©diÃ©es `traiter`, `rejeter` ou `annuler`. Le statut et la date de traitement ne se modifient pas par CRUD ; la date est attribuÃ©e lors du traitement. Migration 0024 ajoute `REJETE`.
- Un ordre traitÃ© reprÃ©sente une confirmation enregistrÃ©e dans l'application ; aucun fichier bancaire n'est encore gÃ©nÃ©rÃ© ni transmis. Il ne constitue pas Ã  lui seul une confirmation provenant de la banque.
- Les CRUD sont `/api/paiements/` et `/api/ordres-virement/`. Les profils sont gÃ©rÃ©s par `/api/regles-paie/`, les Ã©lÃ©ments variables par `/api/elements-variables-paie/`.
- Le calcul est explicite via `POST /api/paiements/{id}/calculer/`. Les actions mÃ©tier dÃ©diÃ©es sont `/valider/`, `/annuler/` et `/marquer-payee/`.
- `ReglePaie` porte des paramÃ¨tres datÃ©s et configurables ; primes, heures supplÃ©mentaires, avantages, retenues et charges patronales sont stockÃ©s dans `ElementVariablePaie`.
- Tout nouveau profil exige une référence et une validation distincte avant calcul. Aucun contournement par mode DEBUG. L’ancien profil de démonstration est désactivé par la migration 0035 ; aucun de ses taux n’est certifié automatiquement.
- `Paie.ordre_virement` est facultatif : le calcul prÃ©cÃ¨de la validation puis lâ€™association d'un ordre dÃ©jÃ  traitÃ©.
- Contexte confirmÃ© : Burkina Faso, devise FCFA (code ISO `XOF`). Une paie mensuelle est l'hypothÃ¨se de travail, Ã  confirmer avec l'organisation.
- La paie dÃ©marre en `BROUILLON`, en `XOF`, sans virement. Les champs calculÃ©s sont dÃ©sormais produits par le moteur et ne sont plus saisissables par le CRUD.

### Ã‰tape 1 â€” rÃ¨gles de paie Ã  valider

Contexte confirmÃ© pour le projet : pays Burkina Faso, devise FCFA (`XOF`). Pour prÃ©parer la paie, la base de travail est une paie mensuelle, le salaire contractuel comme base, les primes et heures supplÃ©mentaires en Ã©lÃ©ments sÃ©parÃ©s, et l'emploi de `Decimal` avec dÃ©tail conservÃ©. Ces choix de conception n'Ã©tablissent pas Ã  eux seuls une formule lÃ©gale de calcul.

Les paramètres de prorata, CNSS, TPA, IUTS, retenues et arrondis sont configurés dans les profils datés. Les taux ne sont pas préremplis. L’utilisateur renseigne les valeurs applicables et leur référence, puis valide le profil. Les tests automatisés utilisent des valeurs de test isolées. Les absences validées distinguent congés payés et absences non rémunérées.

Sources officielles repÃ©rÃ©es au 2026-10-19 : le site DGI publie une Ã©dition du CGI datÃ©e de 2021 et une loi de finances 2026 ; la CNSS publie l'arrÃªtÃ© 2022-067 sur le plafond soumis Ã  cotisation ; le Gouvernement a publiÃ© le nouveau Code du travail, loi nÂ°013-2026/ALP. Les documents fiscaux et sociaux ne sont pas encore consolidÃ©s dans une version vÃ©rifiÃ©e pour le calcul Ã  implÃ©menter ; le texte 2026 du travail est disponible en PDF scannÃ© et ses articles applicables doivent encore Ãªtre vÃ©rifiÃ©s. Ne pas reprendre un ancien barÃ¨me ou un taux de site tiers comme rÃ¨gle officielle.

Livrable restant côté métier : renseigner les profils de l’organisation avec leurs références et valider des exemples de calcul. L’interface complète et le contrôle de validation des profils sont implémentés ; aucune règle réglementaire n’est automatiquement choisie par l’application.

### Ã‰tape 2 â€” donnÃ©es variables et modÃ¨le de calcul

RÃ©alisÃ© : devise XOF, snapshot `detail_calcul`, paie sans ordre obligatoire, profils configurables et Ã©lÃ©ments variables par employÃ©/pÃ©riode. Les Ã©lÃ©ments doivent Ãªtre approuvÃ©s par une action distincte `paie.update`. Migrations 0018â€“0023.

### Ã‰tape 3 â€” calcul reproductible

RÃ©alisÃ© dans `PaieCalculationService` avec `Decimal` et les repositories de contrats, Ã©lÃ©ments variables, rÃ¨gles et absences. Le calcul exige un contrat unique couvrant la pÃ©riode et un profil explicite ; il produit le brut, les retenues, CNSS/TPA/IUTS, net, coÃ»t employeur et un snapshot des entrÃ©es, assiettes, taux et rÃ¨gles.

Les doublons actifs sont empÃªchÃ©s par employÃ©/pÃ©riode. Le cycle est `BROUILLON â†’ CALCULE â†’ VALIDEE â†’ PAYE`; une paie calculÃ©e est immuable. L'annulation exige un motif et permet de crÃ©er un remplacement ; le recalcul implicite est interdit.

Le calcul refuse Ã©galement les donnÃ©es historiques oÃ¹ un mÃªme jour ouvrÃ© est couvert Ã  la fois par une absence payÃ©e et une absence non rÃ©munÃ©rÃ©e. La validation d'absence empÃªche dÃ©jÃ  les nouveaux chevauchements ouvrÃ©s.

### Ã‰tape 4 â€” gÃ©nÃ©ration et archivage du bulletin PDF

PremiÃ¨re version rÃ©alisÃ©e : gÃ©nÃ©ration Ã  la demande depuis le snapshot aprÃ¨s validation de la paie, sans dÃ©pendre d'un ordre de virement ; archivage hors du rÃ©pertoire public et tÃ©lÃ©chargement contrÃ´lÃ© pour l'employÃ© concernÃ© ou un utilisateur ayant `paie.read`. Le PDF est rattachÃ© Ã  la paie et n'est gÃ©nÃ©rÃ© qu'une fois. La migration `0026_paie_bulletin_pdf` est appliquÃ©e. Le circuit et le test d'accÃ¨s passent, mais la validation finale du rendu texte (accents Ã  l'extraction), du contenu rÃ©glementaire, de la personnalisation employeur et des exigences locales de conservation reste ouverte.

### Ã‰tape 5 â€” gÃ©nÃ©ration SEPA et cycle de vie des virements

DÃ©finir la version ISO 20022 `pain.001` exigÃ©e par la banque. GÃ©nÃ©rer un fichier XML Ã  partir des paies validÃ©es et des coordonnÃ©es bancaires, valider sa structure et ses champs requis, puis enregistrer le fichier et son Ã©tat sans l'envoyer automatiquement Ã  une banque au premier stade.

Les tests utilisent des coordonnées fictives. Le chiffrement bancaire du module 3 est activé et vérifié. Les fichiers de virement restent à implémenter et leur conformité à valider ; aucune génération réelle n’est activée par cette intervention. Empêcher de générer deux fois le même ordre pour la même paie/période.

Le cycle applicatif des statuts (`GENERE` vers `TRAITE`, `REJETE` ou `ANNULE`) est implÃ©mentÃ© par actions dÃ©diÃ©es. La gÃ©nÃ©ration, l'envoi bancaire, le rapprochement avec un retour bancaire et l'historique dÃ©taillÃ© restent Ã  faire. Un ordre ne peut pas Ãªtre modifiÃ© ou supprimÃ© aprÃ¨s changement de statut.

### Ã‰tape 6 â€” suivi et tests de bout en bout

ComplÃ©ter la traÃ§abilitÃ© des transitions et conserver les motifs de rejet/annulation. Terminer la validation textuelle et rÃ©glementaire du PDF. Ajouter tests unitaires des formules rÃ©glementaires validÃ©es, tests de conformitÃ© XML SEPA et scÃ©narios Postman avec des donnÃ©es fictives.

### Ordre de rÃ©alisation

1. Valider les rÃ¨gles de paie et les exemples de rÃ©fÃ©rence.
2. CrÃ©er les modÃ¨les/repositories/services des primes et heures supplÃ©mentaires et prÃ©parer l'instantanÃ© de paie.
3. ImplÃ©menter et tester le calcul de paie.
4. GÃ©nÃ©rer et archiver les bulletins PDF avec accÃ¨s contrÃ´lÃ©.
5. Le chiffrement bancaire du Module 3 étant activé, générer et valider les fichiers SEPA avec des données fictives lors du chantier dédié aux virements.
6. ComplÃ©ter la traÃ§abilitÃ© des ordres, puis tester le workflow via Postman ; le cycle de statuts de base est dÃ©jÃ  implÃ©mentÃ©.

## Module 5 â€” Analyse de la masse salariale

**Revue du 2026-10-25 : développement fonctionnel terminé, recette visuelle à clôturer.** Les 61 tests ciblés de la masse salariale passent ; le module 6 devient le chantier actif.

### Compléments mensuels/annuels du 2026-10-24

- La synthèse produit les évolutions mensuelle et annuelle en une seule lecture du repository, avec les mêmes montants Decimal et des employés distincts par année. La route d’évolution réutilise ces agrégats. Injection explicite de l’interface de repository, sans ORM dans les services ni vues.
- L’export accepte `granularite=mensuelle|annuelle` (mensuelle par défaut). CSV, Excel et PDF suivent le mode sélectionné, avec nom de fichier et section d’évolution correspondants. Les quatre sections, le filtre département historique et `paie.read` sont conservés.
- Le frontend présente trois graphiques (net, coût employeur, cotisations), et les ventilations incluent le brut et les cotisations. Aucun changement des règles de calcul des paies ni des permissions.
- Validation : 61 tests backend ciblés SQLite, 9 tests module 5 PostgreSQL et contrôle Django réussis. Six exports de la base locale vérifiés en lecture seule ; PDF mensuel et annuel de recette rendus et inspectés. Aucun enregistrement métier modifié. La validation visuelle complète des nouveaux graphiques dans le navigateur reste à effectuer.


### Ã‰tape 1 â€” API de synthÃ¨se en lecture seule

PremiÃ¨re tranche implÃ©mentÃ©e et vÃ©rifiÃ©e selon le pattern vue â†’ serializer â†’ service â†’ interface/repository de lecture dÃ©diÃ© : `GET /api/analyses/masse-salariale/?periode_debut=AAAA-MM&periode_fin=AAAA-MM` (permission `paie.read`), avec filtre facultatif `departement=<id>`. L'API agrÃ¨ge uniquement les paies `VALIDEE` et `PAYE`, renvoie sÃ©parÃ©ment montants validÃ©s et payÃ©s (brut, net, cotisations, coÃ»t employeur), Ã©volution mensuelle et ventilations par dÃ©partement et type de contrat. Les brouillons, calculs non validÃ©s et paies annulÃ©es sont exclus. Ã€ chaque calcul, dÃ©partement et types de contrat sont figÃ©s dans le snapshot de paie ; l'analyse ne dÃ©pend pas des changements ultÃ©rieurs. Les paies historiques sans snapshot sont identifiÃ©es comme historique indisponible. Les paramÃ¨tres calendrier et l'ordre des pÃ©riodes sont validÃ©s.

Endpoint d'Ã©volution ajoutÃ© : `GET /api/analyses/masse-salariale/evolution/?periode_debut=AAAA-MM&periode_fin=AAAA-MM&granularite=mensuelle|annuelle` (permission `paie.read`), avec filtre dÃ©partement fondÃ© sur la classification historique. Le contrÃ´le Django et 36 tests `DomainCrudTests` passent.

ContrÃ´le rÃ©alisÃ© sur la base locale avec trois employÃ©s fictifs (`DEMO-M5`), trois dÃ©partements, trois types de contrat et neuf paies sur aoÃ»tâ€“octobre 2026, dont cinq payÃ©es avec leurs ordres traitÃ©s. Les classifications historiques ont Ã©tÃ© ajoutÃ©es aux snapshots de dÃ©monstration. Les deux endpoints renvoient 200, les pÃ©riodes et filtres mensuels/annuels rÃ©pondent correctement ; une paie validÃ©e prÃ©existante d'octobre sans snapshot reste visible sous Â« Historique indisponible Â» et dans le total gÃ©nÃ©ral.

Exports réalisés : `GET /api/analyses/masse-salariale/export/?periode_debut=AAAA-MM&periode_fin=AAAA-MM&format_fichier=csv|xlsx|pdf&granularite=mensuelle|annuelle`, avec filtre facultatif `departement=<id>` et permission `paie.read`. Le CSV UTF-8, le classeur Excel multi-feuilles et le PDF reprennent la synthèse globale, l’évolution sélectionnée et les ventilations historiques. Les trois formats sont vérifiés pour les deux granularités ; les PDF sont rendus et inspectés.



### Profil frontend de masse salariale — 2026-10-23

- Migration `0042_frontend_payroll_mass_role` : rôle `FRONTEND_MODULE_5_MASSE_SALARIALE` avec uniquement `paie.read` et `departement.read`, sans attribution automatique à un compte. Le droit `paie.read` couvre aussi la consultation globale des paies du module 4 ; il n’est pas limité aux indicateurs agrégés.
- Les API, agrégations et repositories existants sont réutilisés sans modification des règles métier. Aucun droit de création, décision ou suppression n’est ajouté à ce profil.
- Vérifications : 55 tests ciblés SQLite et 55 tests ciblés PostgreSQL réussis (`DomainCrudTests` et tests module 5), contrôle Django et absence de migrations de modèle manquantes. Migration 0042 appliquée sur la base locale ; profil et API de synthèse, évolution annuelle et trois exports vérifiés en lecture seule. Aucun salaire, contrat, paiement ni rôle employé modifié.
- Le frontend du module 5 est construit ; la validation du parcours dans le navigateur reste à réaliser. Le module 4 est laissé en attente de reprise à la demande de l’utilisateur.


## Module 6 — Calcul du TGM

**API et interface de consultation implémentées le 2026-10-25, avec simulation de rentabilité sur chiffre d’affaires saisi.**

- `GET /api/analyses/tgm/?periode_debut=AAAA-MM&periode_fin=AAAA-MM`, protégé par `paie.read`, expose les paies `VALIDEE`/`PAYE`, groupées par employé et devise. Vue → serializer → service → interface/repository ; aucun ORM dans la vue ni le service.
- Taux journalier brut/chargé = somme des montants / jours ouvrés prévus couverts par les contrats, limités aux dates d’emploi et aux mois avec paie finalisée. Les jours sont dédupliqués. Un mois avec paie mais sans jour couvert rend le taux indisponible.
- Heures prévisionnelles = somme des heures journalières contractuelles pour chaque jour prévu. Le taux horaire brut/chargé divise directement le montant par ces heures ; aucun diviseur fixe de huit heures. Un horaire manquant ou des contrats qui se chevauchent rendent le taux horaire indisponible, sans supprimer le taux journalier calculable.
- `GET /api/analyses/couts-projets/` conserve les dates journalières et ne chiffre que les heures des feuilles `VALIDEE`. Taux chargé mensuel non arrondi avant multiplication, un seul calcul TGM par mois ; ventilations par projet, tâche et employé. Coûts en XOF uniquement, autres devises sans taux. Un coût incomplet reste `null`, avec heures non chiffrables et sous-total calculable.
- `GET /api/analyses/couts-projets/simulation/?date_debut=AAAA-MM-JJ&date_fin=AAAA-MM-JJ&projet=<id>&chiffre_affaires=<montant>` utilise `paie.read`. Montant Decimal positif ou nul, deux décimales au maximum. Marge personnel = chiffre d’affaires − coût estimé complet. Pourcentage = marge / chiffre d’affaires × 100 ; `null` si CA nul ou coût incomplet. Projet sans heures validées refusé. Réponse non mise en cache, aucune écriture.
- Limites : calendrier lundi-vendredi sans retrait des jours fériés ; contrats actuellement enregistrés, sans snapshot historique des horaires. La simulation exclut les autres charges et ne constitue pas une marge comptable globale. Les scénarios ne sont pas persistés.
- Validation technique et recette : voir le bilan daté en fin de document. Restent la validation métier du calendrier et l’éventuelle historisation des horaires.

## Ajustement CONG_PAY - 2026-10-22

## Détail des demandes d'absence — 2026-10-22

- Attribution vérifiée dans la base de développement : `ADMIN_RH` possède déjà `demande_absence.read` et `demande_absence.update` ; ajout de `demande_absence.update` au profil `FRONTEND_MODULE_2_CONGES_ABSENCES`, qui possédait déjà la lecture. Ce profil permet désormais la consultation transversale et les décisions. Aucun autre rôle ni affectation de compte modifié. Pas de nouvelle permission ni changement des contrôles API.

- `GET /api/demandes-absence/{id}/` enrichi avec les nom, prénom et matricule de l'employé, son département et les nom/prénom du valideur. Les champs existants (dates, motif, type, statut, date de demande et date de décision) sont conservés.
- `demande_absence.read` autorise la lecture de ses propres demandes ; consulter celles des autres nécessite aussi `demande_absence.update`, selon le contrôle existant. Cette évolution n'ajoute aucun droit de décision.
- Architecture conservée : vue → service → interface → repository. Chargement des relations en une seule requête dans le repository ; présentation des données dans un serializer de détail dédié.
- Validation : 25 tests demandes/soldes réussis sur SQLite de test isolé, dont quatre nouveaux tests du détail. La fiche frontend est désormais reliée à cette route par le bouton « Voir le détail » ; interaction navigateur restant à vérifier.

### Paramétrage existant du quota

Parametrage de la base de developpement : droit annuel CONG_PAY de 0 a 30 jours et solde individuel 2026 de 25 a 30 jours acquis, selon la demande utilisateur. Autres types et annees conserves, sans migration. Recalcul : 17 jours pris, 92 en attente, -79 disponibles. Depassement existant a regulariser ; aucune demande supprimee. Les 21 tests des demandes et soldes passent sur une base SQLite de test isolee.

## Planning et roles multiples - 2026-10-22

Test ajoute : permission de lecture dans un role et permission de gestion dans un second role donnent acces au planning transversal, sans evenements dupliques. Les 26 tests demandes/soldes passent sur SQLite isole. Aucun changement des permissions ni des requetes backend.

## Droits communs et codes automatiques — 2026-10-22

- Source unique : `TypeConge.jours_par_annee`, identique pour tous les employés. `SoldeCongeService` utilise toujours cette valeur pour l'affichage et la validation des demandes, jamais un ancien quota individuel.
- `GET /api/soldes-conge/?annee=...` affiche automatiquement les droits des types actifs pour les employés dont la période d'emploi chevauche l'année, même sans demande ni ligne de solde. Les lignes historiques sont conservées. Le GET ne crée aucune donnée ; un solde non encore enregistré a `id: null`.
- Consultation personnelle avec `solde_conge.read`. La consultation transversale exige aussi `demande_absence.update`. Les anciennes écritures individuelles POST/PUT sont retirées fonctionnellement : un compte ayant les anciens droits reçoit 405, sans ces droits 403. Aucune exception individuelle possible via ces routes.
- Modifier le droit annuel d'un type synchronise `acquis` des soldes existants dans une transaction. La migration de données 0031 aligne les anciennes valeurs et a été appliquée en développement. Demandes et jours pris sont conservés. Les quotas communs s'appliquent à toutes les années consultées ; une baisse peut rendre le disponible négatif.
- Code de type généré par CongeService au format `CONGE_` suivi de 14 caractères hexadécimaux. Code en lecture seule dans l'API ; codes existants conservés. Les types utilisés ne peuvent toujours pas être supprimés.
- Profil module 2 limité à 9 permissions : CRUD des types et demandes, lecture des soldes. Retrait des droits d'écriture individuelle et d'annuaire de ce seul profil ; aucun compte n'a changé de rôle.
- 38 tests demandes/soldes réussis sur SQLite isolé, contrôle Django et vérification des migrations réussis. Parcours navigateur et concurrence PostgreSQL non testés.
## Validation complète des tests backend — 2026-10-23

117 tests `core` réussis sur une base SQLite de test isolée. Ajout d'un parcours métier avec authentification JWT réelle via l'API : demande de deux jours ouvrés sur un droit de dix jours, réservation du solde, décision interdite à l'employé, validation par le gestionnaire, soldes recalculés, absence dans le planning, refus et suppression d'autres demandes en attente avec libération des jours. Aucun enregistrement de la base active modifié. La concurrence PostgreSQL et les interactions navigateur restent hors de cette validation.


## Réduction du périmètre frontend module 3 — 2026-10-23

À la demande utilisateur, les sections documentaires sont retirées du frontend, sans suppression des données ni des API. Les permissions document.*, document_employe.* et type_document.* ont été retirées du seul rôle FRONTEND_MODULE_3_DOSSIERS_BANCAIRES_JURIDIQUES. Ses droits bancaires existants ont été conservés : coordonnees_bancaires.read/create/update/delete et employe.read (5 droits constatés). Aucun nouveau droit manage bancaire n'a été attribué. Les autres rôles conservent leurs permissions. Les champs frontend perdent les mentions fictif/fictive ; le chiffrement bancaire a ensuite été activé le 2026-10-23, comme décrit dans le guide dédié.

## Règles de paie et téléchargement PDF — 2026-10-23

La migration 0035 supprime ReglePaie.est_fictif après désactivation de l’ancien profil de démonstration. Le réglage PAYROLL_ALLOW_FICTIONAL_RULES et les branches correspondantes sont retirés. Tout profil exige une référence à la création/modification et une validation distincte avant calcul. La validation fige les paramètres. Les snapshots historiques ne sont pas réécrits ; les nouveaux n’incluent plus ce champ. Aucun ancien taux n’est transformé automatiquement en règle officielle.

La sélection par période et le filtre actif restent dans ReglePaieRepository, via l’interface ; ReglePaieService ne filtre plus directement un QuerySet. Les vues et services conservent le Repository Pattern. Les permissions paie existantes sont conservées. Le rôle gestionnaire inclut désormais aussi le CRUD des ordres, ajouté par la migration 0037.

PaieSerializer expose bulletin_generable en lecture seule : statut validé/payé, date et totaux de calcul présents. Le frontend n’offre pas la génération lorsque l’historique est incomplet. Le GET privé renvoie une erreur 404 lisible si le fichier référencé manque. Le téléchargement frontend utilise Accept: */*, corrigeant le refus HTTP 406 observé avec application/pdf. Les autorisations du bulletin et le contrôle JWT restent conservés.

Vérifications : 143 tests core réussis sur SQLite isolé, 62 tests ciblés réussis sur PostgreSQL isolé, compilation et six contrôles frontend réussis. Migration 0035 appliquée sur PostgreSQL local ; seul l’ancien profil de démonstration est désactivé, aucune paie recalculée ou modifiée. Téléchargement HTTP local d’un PDF existant vérifié. Validation visuelle navigateur non effectuée.

## Contrats et ordres de virement — 2026-10-23

Contrats : GET /api/contrats/ accepte employe=<id positif>, validé par ContratQuerySerializer. La vue délègue à ContratService puis à l’interface et ContratRepository ; le filtre ORM et le préchargement des types restent dans le repository. ContratSerializer expose types_libelles en lecture seule, refuse une fin avant le début, un salaire négatif et des heures hors 0,01–24. Les écritures et liaisons aux types sont transactionnelles ; un contrat ne peut pas être réaffecté à un autre employé. Les snapshots de paie établis restent conservés.

Ordres : création et modification exigent une paie VALIDEE correspondante sans ordre associé. Un ordre GENERE ou TRAITE pour le même employé/période bloque un doublon ; un ordre REJETE/ANNULE permet un remplacement. La vérification verrouille l’employé dans le repository pendant la transaction. Les transitions et suppressions verrouillent l’ordre, et seules les lignes GENERE peuvent évoluer. Les décisions POST exigent ordre_virement.update (correction de l’ancien contrôle create). Rejet/annulation exigent un motif ; la migration 0036 ajoute motif_decision, date_decision et decideur. Les anciennes décisions restent sans auteur/date/motif lorsque ces données n’étaient pas enregistrées ; elles ne sont pas inventées.

PaieService.marquer_payee est transactionnel et verrouille paie puis ordre via leurs repositories. Il vérifie le statut VALIDEE, l’employé, la période, le traitement daté et l’absence d’association à une autre paie avant de renseigner PAYE, ordre_virement et date_paiement. Aucun fichier bancaire ni appel de paiement externe n’est généré.

La migration 0037 étend les seuls profils FRONTEND_MODULE_1_EMPLOYES_ACCES (16 droits, dont CRUD contrat et lecture des types) et FRONTEND_MODULE_4_PAIE_VIREMENTS (9 droits, dont CRUD des ordres). Les rôles ne sont pas attribués automatiquement à des comptes et les autres profils restent inchangés.

Validation : 152 tests core réussis sur SQLite isolé et 71 tests ciblés sur PostgreSQL isolé ; compilation et sept contrôles frontend réussis. Migrations 0036–0037 appliquées sur PostgreSQL local après comparaison des données : contrats, paies, ordres et affectations de rôles conservés. Lectures HTTP authentifiées des contrats filtrés et ordres vérifiées avec réponses 200. Aucune opération métier testée sur les données actives. Validation navigateur et scénarios concurrents simultanés non effectués. Le module 4 conserve comme travaux restants les formulaires de variables et l’intégration bancaire externe. L’ordre PDF est désormais implémenté.

## Types de contrat et contexte de paie — 2026-10-23

Le CRUD existant /api/types-contrat/ est désormais disponible dans l’interface. La migration 0038 passe la liaison ContratTypeContrat.type_contrat à PROTECT. Le repository traduit ProtectedError en ContractTypeInUseError ; TypeContratService renvoie une erreur de validation lisible. Supprimer un type utilisé ne détache plus silencieusement les contrats. La migration 0039 ajoute les droits create/update/delete de type_contrat au seul profil module 1, qui compte désormais 19 droits. Les droits de lecture existants sont conservés ; les rôles des employés ne sont pas réaffectés.

GET /api/paiements/contexte-contrat/ exige paie.read, employe positif et période AAAA-MM valide. PayrollContractContextView valide les paramètres et délègue à ContratService.payroll_context. Celui-ci utilise l’interface/repository de contrats et renvoie READY, MISSING ou AMBIGUOUS avec les contrats qui croisent le mois. ContratSerializer fournit types, salaire de base, heures, statut et dates. Aucun accès ORM ajouté aux vues ; les types sont préchargés dans le repository pour éviter les requêtes par contrat.

payroll_period_bounds centralise les bornes mensuelles utilisées par le contexte et le calcul ; l’année zéro et les mois invalides sont refusés. La sélection du contexte est identique à get_for_employee_period utilisée par le calcul : un contrat partiel peut produire un prorata, plusieurs contrats sur le même mois restent ambigus. Le frontend ne recalcule ni ne saisit les montants issus du contrat. Le module 4 peut consulter ce contexte avec paie.read sans obtenir contrat.read ni des droits de modification de contrat.

Validation : 160 tests core réussis sur SQLite isolé, 79 tests ciblés réussis sur PostgreSQL isolé, compilation et huit contrôles frontend réussis. Tests du CRUD des types, protection d’un type utilisé, permissions, absence/multiplicité de contrats, mois invalides et préchargement en deux requêtes. Migrations 0038–0039 appliquées sur PostgreSQL local ; comparaison avant/après des types, contrats, liaisons, paies et affectations de rôle sans perte. Lectures HTTP locales des types et du contexte vérifiées, salaire et types comparés au contrat existant. Aucune paie recalculée et aucun type créé pour les essais dans la base active. Validation visuelle navigateur toujours non effectuée.

## Ordre de virement PDF Burkina Faso — 2026-10-23

La préparation d’un PDF bancaire est implémentée. Référence de structure : [formulaire officiel d’ordre de virement BDU-BF](https://wp.bdu-bf.com/wp-content/uploads/2023/08/ORDRE-DE-VIREMENT-BDU.pdf). Il distingue donneur d’ordre, compte débité, montant en chiffres/lettres, bénéficiaire, banque, motif, mode, lieu/date et signature. Le document généré est un modèle Remonte RH paramétrable, sans logo ni prétention d’agrément bancaire universel. Aucun seuil de routage, frais ou règle de banque n’est inventé. Le RIB est contrôlé structurellement (UEMOA, 24 caractères ; BF pour le donneur), sans certification de clé/compte. Les virements internationaux SWIFT ne sont pas produits par ce modèle.

Routes protégées : GET /api/ordres-virement/{id}/document/contexte/ pour le net de paie et les comptes masqués ; POST /api/ordres-virement/{id}/document/ pour générer ; GET sur cette dernière route pour télécharger. Toutes exigent ordre_virement.read, paie.read et ordre_virement.generate_document. La migration 0041 accorde le nouveau droit à ADMIN_RH et au profil module 4, qui compte 10 droits. Les droits ordinaires des salariés ne sont pas étendus.

TransferDocumentService reçoit les interfaces des repositories d’ordres et de coordonnées bancaires ainsi que TransferOrderPdfService. Il vérifie ordre GENERE, paie VALIDEE correspondante, net positif en XOF et propriété du compte bénéficiaire. Les instructions du donneur sont validées par serializer ; la date d’exécution ne peut pas être passée. Le montant, la période et le bénéficiaire proviennent du backend et ne peuvent pas être remplacés par le client. Le verrouillage suit paie puis ordre comme l’association de paiement, évitant une inversion de ces deux verrous. Les requêtes et la persistance restent dans les repositories.

La migration 0040 ajoute document_donnees (texte JSON chiffré via Fernet), document_pdf (fichier dans PrivatePayrollStorage), document_genere_le et document_genere_par. Le snapshot reprend les instructions et RIB au moment de l’émission ; il n’est pas exposé par les listes. Le PDF contient les coordonnées complètes pour la banque et reste lisible dans le stockage privé sur disque ; il n’est pas chiffré comme la colonne SQL et n’est pas servi par MEDIA_URL. Le GET authentifié renvoie private, no-store. L’instantané SQL utilise la clé bancaire existante hors dépôt.

Le document est figé et une nouvelle génération conserve le fichier existant. Modifier/supprimer un ordre documenté est refusé ; une correction passe par annulation avec motif puis remplacement. Un ordre clôturé ne produit pas de nouvelle instruction, mais son PDF déjà archivé reste consultable avec les droits requis. Générer n’exécute aucun virement, ne signe pas et ne marque pas une paie PAYE. Les intégrations de fichiers d’échange bancaire et la transmission automatique restent distinctes.

Validation : 167 tests core SQLite et 86 tests ciblés PostgreSQL réussis ; compilation et neuf contrôles frontend réussis. Tests de permission d’export, propriété/masquage des comptes, montant issu de la paie, RIB/date, chiffrement SQL, téléchargement privé, idempotence et gel des instructions. PDF A4 de démonstration rendu en image et inspecté. Migrations 0040–0041 appliquées localement après comparaison : paies, ordres et affectations de rôles conservés. Aucun document bancaire réel ni paiement créé pour les essais. Parcours navigateur et acceptation du support par la banque destinataire non validés.

## Validation du module 6 — 2026-10-25

- 77 tests backend ciblés réussis sur PostgreSQL de test : 16 tests TGM/simulation et 61 tests métier, permissions et exports existants. Les 16 tests module 6 passent aussi sur SQLite isolé. Aucun changement de modèle à migrer (`makemigrations --check --dry-run`).
- Cas vérifiés : journée de six heures, horaires variables au cours du mois, chevauchements, horaires/contrats/montants absents, mois sans paie, mois avec paie sans jours couverts, exclusion des paies non finalisées, permissions et calendrier. Les coûts projets utilisent le taux non arrondi ; les coûts partiels ne produisent pas de marge complète. Simulation positive, perte, CA nul, montant/projet/dates invalides et mélange d’heures chiffrables/non chiffrables couverts.
- API sur PostgreSQL local : synthèse TGM, coûts projets et simulation répondent 200 dans une transaction explicitement en lecture seule (deux lignes employé/devise et un projet avec heures validées). Aucun salaire, contrat, projet, paiement, rôle ni affectation modifié.
- Recette navigateur Edge avec données fictives : bureau 1440 px et mobile 390 px, largeur disponible et absence de débordement de page, défilement clavier du tableau, ouverture des détails, simulation, saisies invalides, dates inversées, périmètre vide et refus sans permission. Captures `output/tgm/desktop.png` et `mobile.png` inspectées. Un second parcours navigateur connecté aux API locales charge réellement les taux, coûts et simulation via GET.
- La recette métier de l’organisation (jours fériés, calendrier hebdomadaire individualisé, historisation des horaires et autres charges de projet) reste ouverte. Cette version fournit des estimations et une marge après coût de personnel, sans persistance des scénarios.

## Validation du module 7 — 2026-10-25

- 87 tests ciblés PostgreSQL réussis : 10 tests de saisie heures/jours et circuit complet, 16 tests TGM/simulation et 61 tests métier, permissions et exports existants. Les 10 nouveaux tests passent aussi sur SQLite. Le contrôle Django ne relève aucun problème et `makemigrations --check --dry-run` ne détecte aucun changement.
- Les nouveaux cas couvrent l’exclusivité heures/jours, les bornes, le cumul quotidien mixte, les horaires absents/ambigus, les totaux serveur, l’isolation des propriétaires, la séparation des droits de décision et de paie, la soumission, le refus/correction et la prise en compte/retrait des coûts après validation/modification.
- Parcours navigateur connecté à un serveur Django et une base SQLite temporaires : préparation du projet, tâche et affectation, cycle complet employé/manager et rapprochement de 3 h au taux de 2 000 FCFA/h, soit 6 000 FCFA. Dépassement contractuel et nouvelle correction après validation vérifiés. Les écritures de recette n’atteignent jamais PostgreSQL local ; la base temporaire est supprimée après fermeture des connexions.
- PostgreSQL local consulté uniquement en transaction `READ ONLY` : feuilles personnelles, options de projets, file de décision et champ `rapprochement` répondent correctement. Les droits existants du compte ADMIN_RH de vérification couvrent la décision et la préparation des projets. Aucun rôle, compte, contrat, salaire, projet ni affectation actif modifié.
- Compilation et sept scripts frontend réussis ; captures bureau/mobile inspectées. Restent les évolutions métier hors de cette première version : hiérarchie des managers, notifications, clôture définitive des feuilles et historisation des taux.

## Profils des modules restants et employés de recette — 2026-10-25

- Migration de données `0044_remaining_module_and_employee_roles` créée et appliquée sur PostgreSQL local : `EMPLOYE_SIMPLE` (7 droits personnels), `FRONTEND_MODULE_6_TGM` (`paie.read`) et `FRONTEND_MODULE_7_FEUILLES_TEMPS` (7 droits de décision/préparation des projets). Aucun profil existant modifié ; la migration ne rattache automatiquement aucun compte.
- Affectation explicitement demandée : Awa TEST (`awa.recette@example.com`, id 18) et Moussa TEST (`moussa.recette@example.com`, id 19) possèdent chacun uniquement `EMPLOYE_SIMPLE`. Leurs mots de passe, statuts et données RH sont conservés. Aucun profil TGM ou manager attribué à ces comptes.
- Droits personnels : lecture des types et soldes de congé, lecture/création des demandes personnelles, lecture/création/modification de leurs coordonnées bancaires. Les feuilles de temps personnelles suivent déjà les contrôles d’authentification/propriétaire. Aucune permission de décision, de suppression des congés/coordonnées bancaires ou de consultation des paies globales.
- `paie.read` donne aussi accès à la paie globale et à la masse salariale : le profil TGM reste distinct du profil employé. Le profil gestionnaire module 7 ne possède pas ce droit ; le cumuler avec le profil TGM uniquement pour un gestionnaire autorisé aux coûts.
- Validation : 36 tests backend PostgreSQL ciblés, dont 7 tests des profils ; 7 tests des profils SQLite réussis. Contrôle Django et absence de migration de modèle manquante vérifiés. Accès réels des deux comptes vérifiés en transaction `READ ONLY` (routes personnelles 200, gestion 403). Les instantanés avant/après sont dans `output/permissions/`.
- Les deux comptes n’ont aucun projet affecté : l’affectation à un projet actif et une tâche active reste à préparer pour la saisie des temps. Aucune donnée métier créée ou modifiée par les vérifications. Détail : [rôles et comptes de recette](output/permissions/roles-et-comptes-test.md).

## Codes automatiques des projets/tâches et options de saisie — 2026-10-25

- `ProjetService.create_project` génère un code `PROJ_` suivi de 24 caractères hexadécimaux ; `create_task` fait de même avec `TASK_`. Les serializers exposent `code` en lecture seule. Les codes envoyés par un client ne remplacent pas cette génération ; les mises à jour via serializer ou service préservent les codes historiques.
- Les champs et contraintes de base sont conservés : code projet unique, code tâche unique dans le projet, nom de tâche unique dans le projet. Aucune migration ni réécriture des projets/tâches existants.
- L’API d’options personnelles renvoyait déjà les tâches actives des projets affectés. Son comportement est maintenant couvert pour une affectation après première lecture et une tâche ajoutée plus tard, avec exclusion des projets non affectés/inactifs et tâches inactives. La réponse est marquée `private, no-store`.
- La panne observée a été reproduite dans le navigateur avant correction : liste initiale conservée dans React. L’ouverture du formulaire, le retour à l’onglet et l’actualisation manuelle déclenchent désormais de nouvelles lectures.
- Validation : 100 tests ciblés PostgreSQL et 6 tests projet/saisie SQLite réussis ; contrôle Django sans problème et aucune migration manquante. Recette complète contre un serveur et une base SQLite temporaires, avec véritables créations, affectations et enregistrement/soumission de la feuille. TGM et parcours personnels également vérifiés après extraction de la logique d’actualisation.
- Base active vérifiée en transaction PostgreSQL `READ ONLY` : pour Awa et Moussa, l’API renvoie un projet affecté avec deux tâches actives, les contrats prévoient 8 h/jour et le payload de 2 h passe les validations de saisie. Aucun code historique ni donnée métier actif modifié ; aucune feuille fictive créée sur leurs comptes.

## Bulletin PDF automatique à la validation - 2026-10-26

- La validation d'une paie calculée génère et archive désormais son bulletin PDF dans le stockage privé, puis renvoie bulletin_disponible=true.
- La validation et l'association du fichier sont transactionnelles. Échec de rendu, instantané de calcul incomplet ou échec de stockage : la paie reste CALCULE, sans auteur/date de validation enregistrés, pour permettre une nouvelle tentative.
- Le téléchargement reprend le PDF archivé. Une nouvelle demande de génération réutilise ce fichier et ne crée pas de doublon. L'ancienne génération à la demande est conservée pour les paies historiques déjà validées sans fichier.
- Le dépôt d'un fichier suivi d'un échec d'enregistrement en base déclenche le nettoyage du nouveau fichier. Les validations et générations prennent un verrou sur la paie.
- Les tests stockent les bulletins et ordres PDF dans un répertoire temporaire, sans écrire dans les archives actives.

## Bulletins personnels - 2026-10-26

- GET /api/mes-bulletins/ est accessible à tout compte authentifié et ne renvoie que ses paies VALIDEE/PAYE, de la plus récente à la plus ancienne. L'identité est imposée par request.user, jamais par un paramètre client.
- Serializer personnel limité aux période, libellé, brut, net, devise, statut, date de validation et disponibilité du PDF. Aucun chemin de stockage ou détail RH global n'est exposé. Réponse privée sans cache.
- Le téléchargement existant reste soumis au contrôle propriétaire ou gestionnaire paie. L'accès personnel n'accorde ni lecture des paies globales, ni gestion, ni génération de bulletins.
- Les paies historiques validées dont le PDF n'a pas encore été généré restent visibles avec un indicateur d'indisponibilité.
- Vérification : 19 tests PostgreSQL ciblés incluant le scénario correspondant du cahier des charges, contrôle Django et migrations cohérents.

## Responsable hiérarchique, postes, contrats et historique - 2026-10-26

- Champ responsable sur Employe, nullable et sans affectation arbitraire des comptes existants. Les services de création/modification refusent auto-rattachement, cycles indirects et nouvelle affectation à un compte inactif. Les modifications de hiérarchie prennent des verrous pour éviter deux mises à jour concurrentes contradictoires.
- Poste courant éditable depuis le dossier employé. Plusieurs employés peuvent occuper un poste de même nom ; la relation de poste courant par employé est conservée.
- EmployeHistorique conserve catégorie, opération, auteur/date, valeurs avant/après et référence de l'objet même après suppression d'un contrat/poste. Création/modification/suppression par les API contrats, postes et liaisons contrat/type alimentent l'historique dans leur transaction.
- GET /api/employes/{id}/historique/ nécessite employe.read. Les entrées de contrat, contenant les salaires, sont renvoyées uniquement avec contrat.read. L'API d'historique est en lecture seule et privée sans cache.
- Annuaire enrichi avec poste_nom, responsable_nom et types_contrat_actuels. Filtres API poste et type_contrat ; un contrat courant doit être EN_COURS et couvrir la date du jour, sans doublonner les employés.
- Migrations 0046/0047 appliquées sur PostgreSQL : ajout du responsable et de l'historique, suppression de l'unicité globale des intitulés de poste, état initial des postes et contrats existants. Les changements anciens non enregistrés ne sont pas reconstitués. Aucune hiérarchie fictive n'est créée.
- Vérifications : 247 tests de régression réussis, puis 9 tests ciblés réussis après les ajustements finaux du serializer. Contrôle Django et migrations cohérents ; parcours navigateur sur base temporaire validé sur ordinateur et mobile.

## Catalogue des postes et sélection dans les contrats - 2026-10-26

- Poste est désormais un catalogue partagé (nom, description), indépendant d'un employé. Nom unique sans distinction de casse, suppression protégée lorsqu'un contrat le référence.
- Contrat possède une référence poste avec PROTECT ; le serializer expose poste et poste_nom. Les anciennes lignes sans poste restent valides. Le formulaire utilisateur exige de sélectionner un poste du catalogue pour enregistrer un contrat.
- L'annuaire calcule les postes depuis les contrats EN_COURS couvrant la date du jour. Il affiche plusieurs intitulés si plusieurs contrats courants occupent des postes différents. Le champ texte libre poste_nom n'est plus modifiable sur la fiche employé.
- Les changements de poste d'un contrat alimentent les historiques CONTRAT et POSTE. Le renommage d'un poste partagé conserve les anciennes valeurs dans les historiques des employés liés. Les archives PDF déjà produites ne sont pas régénérées.
- Migration 0048 : transfert des postes existants vers les contrats courants uniquement, conservation des états initiaux, fusion des noms équivalents en conservant les descriptions, ajout des droits poste.read/create/update/delete aux profils RH/module 1. Aucun poste n'est inventé pour les contrats expirés ou sans ancien poste.
- Reprise de migration vérifiée sur une base SQLite temporaire contenant deux anciens postes équivalents et des contrats courants/expirés. Tests catalogue et historique, build et recette navigateur réels validés.
