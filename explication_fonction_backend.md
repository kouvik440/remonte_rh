# Explication des fonctions — Planning du Module 2


## Départements du module 1 — mise à jour du 2026-10-27

Le frontend utilise le CRUD existant des départements : `DepartementListView` gère GET/POST sur `/api/departements/` ; `DepartementDetailView` gère GET/PUT/DELETE sur `/api/departements/{id}/`. `HasResourceCrudPermission` vérifie le droit `departement.*` correspondant à chaque méthode HTTP. `DepartementSerializer` valide le nom, obligatoire, unique et limité à 100 caractères. Il expose également `id` et `code` en lecture seule : un code fourni par le client est ignoré.

`DepartementService` reçoit son repository par l’interface `DepartementRepositoryInterface` ; `DepartementRepository` conserve la lecture et la persistance ORM. À la création, le service génère `DEP_` suivi des 16 premiers caractères hexadécimaux d'un UUID aléatoire en majuscules (20 caractères au total). L'unicité reste imposée en base. À la modification, il retire tout code des données reçues pour conserver celui du département, y compris les codes antérieurs. Aucun changement de modèle ni migration n'est nécessaire. Supprimer le département retire les affectations employées par `SET_NULL`, sans supprimer les employés ni réécrire les classifications historiques stockées dans les paies.

La migration 0043 ajoute les quatre droits au rôle existant `ADMIN_RH` et au profil `FRONTEND_MODULE_1_EMPLOYES_ACCES`, porté à 22 permissions à cette migration. Elle ne modifie pas les rôles des employés ni le profil module 5 en lecture seule. `test_departments.py` vérifie le CRUD autorisé, le refus des écritures en lecture seule, le refus de lecture sans droit, la validation du nom et la conservation des employés après suppression. Deux cas supplémentaires couvrent les codes automatiques distincts malgré un code client et le maintien d'un ancien code au renommage. Les sept tests réussissent sur PostgreSQL le 27 octobre 2026, sans modification des départements de la base active.

## Demandes d'absence et soldes de congé

### Identité dans la liste des demandes — 2026-10-27

`DemandeAbsenceSerializer` ajoute `employe_prenom` et `employe_nom`, lus depuis l'employé lié et non modifiables par le client. Ces champs sont hérités par `DemandeAbsenceDetailSerializer`. `DemandeAbsenceRepository.all()` et `for_employee()` chargent déjà la relation employé, donc l'affichage du nom ne nécessite pas de requête supplémentaire par demande. Les vues gardent le filtrage personnel et le droit existant `demande_absence.update` pour consulter toutes les demandes. Aucun accès à l'annuaire n'est ajouté. Les 23 tests des accès aux demandes passent sur PostgreSQL ; le nouveau cas vérifie l'identité et la visibilité selon le profil.

### Quota à la création, modification et validation

`DemandeAbsenceService` appelle `SoldeCongeService.validate_request_quota` dans une transaction. Le service découpe une demande par année civile et compte les jours du lundi au vendredi. Pour chaque année, il prend le quota `SoldeConge.acquis` s'il existe, sinon le droit annuel `TypeConge.jours_par_annee`. Un quota nul ou négatif ne permet pas de soumettre une demande.

Les jours des demandes déjà validées et encore en attente sont réservés. Une même date ouvrée qui apparaît dans plusieurs demandes est comptée une seule fois. Ainsi, plusieurs demandes en attente ne peuvent pas dépasser ensemble le quota. Au moment de la validation, le service vérifie de nouveau la règle ; si le quota a été consommé entre-temps, la validation est refusée et la demande reste en attente. Une ligne employé est verrouillée pendant la transaction afin de séquencer les demandes concurrentes.

À la première demande sur un couple employé/type/année sans solde, le backend crée la ligne avec le quota annuel configuré et `pris=0`. Pour les anciennes demandes validées, la migration `0030_backfill_leave_balances_from_approved_requests.py` crée uniquement les soldes absents associés à un quota positif, avec le nombre de jours ouvrés validés dédupliqués. Les soldes existants ne sont pas modifiés.

### Calcul des champs renvoyés par `GET /api/soldes-conge/`

- `acquis` : quota annuel du solde.
- `pris` : jours ouvrés couverts par les demandes validées, dédupliqués par date.
- `en_attente` : jours ouvrés réservés par les demandes encore en attente, hors dates déjà comptées dans `pris`.
- `disponible` : `acquis - pris - en_attente`, donc le nombre pouvant encore être demandé.
- `restant` : `acquis - pris`, champ conservé pour compatibilité avec les clients existants ; il ne déduit pas les demandes en attente.

Les absences qui chevauchent une année sont comptées séparément dans chaque année. Le calcul actuel ne soustrait pas les jours fériés : seuls les samedis et dimanches sont exclus.

### Tests associés

Les tests `DemandeAbsenceAccessTests` et `SoldeCongeTests` vérifient le dépassement de quota à la création et à la validation, la réservation des demandes en attente, la création d'un solde manquant et le calcul de `disponible`. La migration de données a été appliquée à la base PostgreSQL de développement après vérification du code.

## Objectif et périmètre

L'API expose un calendrier partagé d'événements de planning : les absences validées et les présences prévues. Elle ne mesure pas la présence réelle. Une présence réelle nécessiterait une source de pointage ou une déclaration, qui n'existe pas dans le modèle actuel.

Route : `GET /api/planning/`

Paramètres obligatoires :

- `date_debut` : première date de la période, au format `AAAA-MM-JJ`.
- `date_fin` : dernière date de la période, au format `AAAA-MM-JJ`, supérieure ou égale à `date_debut`.

Filtres facultatifs :

- `departement` : identifiant du département.
- `employe` : identifiant de l'employé. Ce filtre est ignoré pour un utilisateur qui ne possède pas le droit de consulter le planning transversal ; son identifiant authentifié est alors imposé.

Exemple : `GET /api/planning/?date_debut=2026-10-01&date_fin=2026-10-31&departement=2`

## Parcours de la requête

Le code suit le repository pattern du projet : vue HTTP → service de planning → services métier → repositories/interfaces → modèles Django. La vue ne construit pas elle-même de requête ORM.

### `PlanningEventQuerySerializer`

Dans `backend/core/serializers/demande_absence_serializer.py`, valide les paramètres de la requête. Il exige les deux dates, vérifie leur format et refuse une période dont la fin précède le début. Les identifiants facultatifs doivent être des entiers positifs.

### `PlanningEventsListView.get`

Dans `backend/core/views/demande_absence_views.py`, valide les paramètres, puis applique les permissions. La permission `demande_absence.read` est nécessaire pour appeler la route. Avec `demande_absence.update`, l'utilisateur peut consulter tous les employés ; sans ce droit, la vue limite la recherche à `request.user.pk`. Elle transmet les filtres au service et sérialise les événements avant de répondre.

### `PlanningService.get_events`

Dans `backend/core/services/planning_service.py`, orchestre la production des événements :

1. Demande au service des absences les demandes validées qui chevauchent la période.
2. Demande au service des employés les employés actifs dont la période d'emploi chevauche la période demandée.
3. Convertit chaque demande validée en un événement `ABSENCE`.
4. Repère, pour chaque employé, les dates couvertes par ses absences validées.
5. Crée un événement `PRESENCE_PREVUE` pour chaque jour du lundi au vendredi où l'employé est dans sa période d'emploi et n'a pas d'absence validée.
6. Trie les événements par date puis par nom et prénom.

Les absences sont inclusives : leurs dates de début et de fin font partie de l'absence. Les dates de début d'emploi et de sortie sont également inclusives pour le calcul des présences prévues.

### `PlanningService._absence_event`

Transforme une demande validée en dictionnaire d'événement. Le dictionnaire expose l'identifiant de demande, l'employé, le département, le type de congé et les dates. Le motif n'est pas exposé.

### `PlanningService._presence_event`

Transforme une journée ouvrée sans absence validée en événement `PRESENCE_PREVUE`. Chaque événement dure une journée et ne référence pas de demande d'absence.

### `EmployeService.get_for_calendar`

Dans `backend/core/services/employe_service.py`, transmet les critères du calendrier à l'interface du repository employé. Il conserve la règle d'accès aux données employé hors de la vue.

### `EmployeRepository.for_calendar`

Dans `backend/core/repositories/employe_repository.py`, sélectionne les employés avec `is_active=True` et `statut=ACTIF`, dont la période d'emploi chevauche la période demandée. Il applique les filtres de département et d'employé et charge le département avec `select_related`.

### `DemandeAbsenceService.calendar`

Dans `backend/core/services/demande_absence_service.py`, transmet la période et les filtres au repository des demandes d'absence.

### `DemandeAbsenceRepository.calendar`

Dans `backend/core/repositories/demande_absence_repository.py`, sélectionne uniquement les demandes `VALIDEE` qui chevauchent la période (`date_debut <= date_fin demandée` et `date_fin >= date_debut demandée`). Il applique les filtres de département et d'employé. Les demandes en attente, refusées ou annulées ne deviennent donc pas des événements du calendrier.

### `PlanningEventSerializer`

Dans `backend/core/serializers/demande_absence_serializer.py`, définit et sérialise le format commun des deux catégories d'événements. Les champs de congé et `demande_absence_id` sont nuls pour une présence prévue.

## Exemple de réponse

```json
[
  {
    "id": "presence-42-2026-10-19",
    "type_evenement": "PRESENCE_PREVUE",
    "demande_absence_id": null,
    "employe_id": 42,
    "employe_nom": "Martin",
    "employe_prenom": "Alex",
    "departement_id": 2,
    "departement_nom": "Ressources humaines",
    "type_conge_code": null,
    "type_conge_libelle": null,
    "date_debut": "2026-10-19",
    "date_fin": "2026-10-19"
  },
  {
    "id": "absence-18",
    "type_evenement": "ABSENCE",
    "demande_absence_id": 18,
    "employe_id": 42,
    "employe_nom": "Martin",
    "employe_prenom": "Alex",
    "departement_id": 2,
    "departement_nom": "Ressources humaines",
    "type_conge_code": "CP",
    "type_conge_libelle": "Congé payé",
    "date_debut": "2026-10-20",
    "date_fin": "2026-10-21"
  }
]
```

## Limites à connaître

- `PRESENCE_PREVUE` signifie uniquement qu'un employé actif est prévu au travail un jour ouvré, sans demande d'absence validée. Ce n'est pas une confirmation de présence réelle.
- Le calendrier ne connaît pas les jours fériés, horaires, temps partiels, télétravail, équipes ou horaires individualisés ; il considère les jours du lundi au vendredi comme ouvrés.
- Une demande validée compte comme absence, quel que soit son type de congé ; le calendrier ne déduit pas la rémunération.
- Une absence qui chevauche la période est renvoyée avec ses dates complètes, même si elle commence avant ou se termine après la période demandée.
- Pour un accès transversal, l'utilisateur doit avoir à la fois `demande_absence.read` et `demande_absence.update`. Le droit `update` sert actuellement aussi à identifier les gestionnaires globaux, conformément au contrôle déjà utilisé dans le module des demandes.

## Validation

La suite `core.tests` vérifie les permissions, les filtres de département et d'employé, l'absence d'exposition du motif, l'inclusion des absences validées, la génération d'une présence prévue et l'exclusion des employés inactifs. Elle a été exécutée avec `manage.py test core.tests --keepdb` : 66 tests réussis.

## Module 4 — Gestion de la paie configurable

### Prise en charge de l'écran de gestion des paies — 2026-10-23

`PaieSerializer` ajoute trois champs en lecture seule : `employe_nom`, `employe_prenom`, `employe_matricule`. Ils permettent d'identifier les paies même si le compte ne possède pas la lecture de l'annuaire. `PaieRepository.get`, comme la liste existante, charge l'employé et l'ordre associé via `select_related`, sans requête supplémentaire de sérialisation. Les vues, services, interfaces et repositories existants conservent leurs responsabilités ; aucun accès ORM ajouté dans les vues ou les services.

La migration 0034 crée `FRONTEND_MODULE_4_PAIE_VIREMENTS` avec CRUD paie et `employe.read`. Aucun compte ne reçoit automatiquement ce rôle. Les actions de calcul, validation, annulation et génération du bulletin utilisent toujours `paie.update`. La consultation `paie.read` est globale et destinée aux gestionnaires ; elle ne limite pas la liste au propriétaire. Le téléchargement conserve les contrôles existants propriétaire ou gestionnaire autorisé et le stockage privé des bulletins.

138 tests core ont réussi sur SQLite isolé. Les 6 tests ciblés PostgreSQL vérifient le rôle et ses cinq droits, l'absence d'attribution automatique, le refus d'accès sans droit, la lecture seule, l'identité non modifiable, l'absence de requête supplémentaire et le CRUD brouillon avec ce seul profil. Migration 0034 appliquée sur PostgreSQL local ; aucune paie active créée/modifiée pour ces tests. Les nouvelles interactions frontend ne sont pas validées dans un navigateur.

### Routes

- `POST /api/paiements/` crée un brouillon en XOF, sans montants calculés ni virement.
- `POST /api/regles-paie/` crée un profil daté. Tous les taux, plafonds, tranches IUTS et réductions doivent être fournis ; aucun taux réglementaire n'est supposé.
- `POST /api/elements-variables-paie/` crée une prime, heure supplémentaire, avantage, retenue ou charge patronale en brouillon.
- `POST /api/elements-variables-paie/{id}/valider/` approuve un élément (`paie.update`). Seuls les éléments approuvés entrent dans le calcul.
- `POST /api/paiements/{id}/calculer/` calcule un brouillon ; corps optionnel : `{"regle_paie": 1, "charges_familiales": 1}`. Sans profil indiqué, un seul profil actif doit couvrir toute la période.
- `POST /api/paiements/{id}/valider/` valide une paie calculée.
- `POST /api/paiements/{id}/annuler/` annule une paie non payée avec `{"motif": "..."}`.
- `POST /api/paiements/{id}/marquer-payee/` exige `{"ordre_virement": 1}` et un ordre traité/daté qui correspond à l'employé et à la période.
- `POST /api/paiements/{id}/bulletin/` (permission `paie.update`) génère et archive le bulletin PDF depuis le snapshot d'une paie validée ou payée. L'opération est idempotente : si le fichier existe déjà, il est conservé. L'ordre de virement n'est pas nécessaire pour créer le bulletin.
- `GET /api/paiements/{id}/bulletin/` télécharge le PDF en privé. L'employé concerné ou un utilisateur avec `paie.read` peut le télécharger ; le fichier n'est pas servi par une URL média publique.
- Le PDF est stocké hors du répertoire média public et rattaché à la paie. Le rendu est en place ; la validation finale de l'extraction des caractères accentués et la validation réglementaire du contenu restent à faire.
- `POST /api/ordres-virement/` crée toujours un ordre `GENERE`. Un client ne peut pas le créer directement comme traité et ne peut pas saisir sa date de traitement.
- `POST /api/ordres-virement/{id}/traiter/` fait passer un ordre `GENERE` à `TRAITE` et attribue automatiquement `date_traitement`.
- `POST /api/ordres-virement/{id}/rejeter/` et `/annuler/` terminent un ordre encore `GENERE`. Les statuts terminaux ne peuvent pas être changés à nouveau. Les actions acceptent un motif facultatif, mais celui-ci n'est pas encore conservé par le modèle.
- Le `PUT` et la suppression sont réservés aux ordres encore `GENERE`; le statut et la date de traitement sont gérés par les actions dédiées.
- Le statut `TRAITE` signifie qu'un utilisateur autorisé a enregistré la confirmation dans l'application. Comme aucun fichier n'est envoyé à une banque, il ne s'agit pas encore d'un retour bancaire vérifié.
- Un ordre traité ne peut être rattaché qu'à une seule paie ; une seconde association est refusée.

Les routes de calcul, validation de profils/variables, annulation et paiement exigent `paie.update`. Les routes CRUD appliquent les permissions `paie.read/create/update/delete`. Le CRUD des ordres utilise ordre_virement.read/create/update/delete ; les POST de décision traiter/rejeter/annuler exigent ordre_virement.update.

### `PaieSerializer.validate_periode` et `PaieSerializer.validate`

Dans `backend/core/serializers/paie_serializer.py`, valident `AAAA-MM`, refusent les doublons pour un employé et une période via le service/repository, et empêchent le client de saisir le brut, net, cotisations, statut ou snapshot calculés.

### `ReglePaieSerializer`

Dans `backend/core/serializers/regle_paie_serializer.py`, valide les périodes d'effet, le profil Burkina Faso/XOF, les taux compris entre zéro et un, les tranches IUTS contiguës et les réductions familiales. Tout profil doit fournir une référence ; sa validation passe par une action distincte.

### `ElementVariablePaieSerializer`

Dans `backend/core/serializers/element_variable_paie_serializer.py`, exige un montant pour les primes, avantages, retenues et charges. Les heures supplémentaires exigent une quantité et un coefficient positif ; le moteur calcule leur montant par `salaire contractuel / heures mensuelles × quantité × coefficient`. L'état `valide` ne peut pas être fourni dans le JSON.

### `PaieCalculationService.calculate`

Dans `backend/core/services/paie_calculation_service.py`, applique une seule règle active couvrant toute la période, exige un contrat unique, calcule le prorata selon les jours du lundi au vendredi, retire les jours couverts par une absence validée non rémunérée, puis calcule les gains variables, CNSS, TPA, IUTS progressif, réduction familiale, net et coût employeur. Les congés payés sont comptés dans le snapshot mais ne réduisent pas le salaire de base. Si les absences payées et non payées couvrent le même jour ouvré (données historiques incohérentes), le calcul est refusé avec les dates conflictuelles.

Le résultat enregistre un snapshot contenant le profil et ses paramètres, le contrat, les absences, les éléments, les assiettes, les tranches et chaque total. Il devient `CALCULE` une seule fois ; lecture, mise à jour et suppression ne recalculent ni ne modifient un calcul établi.

### Workflow d'état

`BROUILLON → CALCULE → VALIDEE → PAYE`. En `BROUILLON`, la paie est créée mais pas encore calculée ; elle peut être complétée avec les éléments variables avant le calcul. Le champ `Paie.est_simulation` a été retiré pour permettre de tester toute la séquence. Le champ `est_fictif` est supprimé par la migration 0035. Les nouveaux calculs conservent un profil référencé et validé, sans mode de démonstration. Les anciens snapshots restent conservés pour l’audit. Une paie annulée conserve son motif et permet une nouvelle tentative pour la même période. Les résultats calculés sont immuables.

Pour l'ordre associé : `GENERE → TRAITE`, `GENERE → REJETE` ou `GENERE → ANNULE`. Le statut et la date de traitement ne sont pas saisissables par CRUD. `TRAITE` est actuellement une confirmation enregistrée par l'utilisateur ; l'intégration et le rapprochement bancaire ne sont pas implémentés.

Après la validation, `POST /api/paiements/{id}/bulletin/` crée le PDF depuis `detail_calcul` et l'enregistre dans le stockage privé, puis l'employé concerné ou un lecteur RH autorisé peut le télécharger par GET sur la même route.

### Hypothèses et limites

- Tous les calculs nouveaux exigent un profil actif, référencé et validé. Le champ est_fictif et le réglage PAYROLL_ALLOW_FICTIONAL_RULES sont supprimés. Les tests automatisés utilisent des valeurs isolées, sans prétendre valider des taux réglementaires.
- Les jours fériés, horaires individualisés et conventions collectives ne sont pas modélisés ; le prorata actuel suppose les jours ouvrés lundi-vendredi et des heures mensuelles configurées.
- Les tranches IUTS, réductions familiales, assiettes et taux doivent être configurés à partir des textes applicables. Un profil réel doit être sourcé et validé.
- Les sources officielles repérées au 2026-10-19 : [DGI - Code général des impôts](https://dgi.bf/code-general/), [DGI - Lois](https://dgi.bf/lois/), [CNSS Burkina Faso](https://cnssbf.org/) et [Code du travail 2026](https://gouvernement.gov.bf/wp-content/uploads/2026/06/DECRET-N%C2%B02026-0613-PF.pdf). Les versions consolidées applicables aux taux et aux règles du net restent à confirmer.
- Le bulletin PDF est généré à la demande par `POST /api/paiements/{id}/bulletin/` après validation de la paie ; le téléchargement est contrôlé par `GET` sur la même route. La génération des fichiers SEPA et leur rapprochement bancaire ne sont pas encore implémentés. Le chiffrement bancaire du Module 3 est activé ; la génération de fichiers bancaires reste un chantier distinct non implémenté.

La suite `manage.py test core.tests --keepdb` a passé avec 66 tests lors de la validation précédente ; la suite ciblée du module paie/ordres a ensuite passé avec 32 tests. La migration `0026_paie_bulletin_pdf` ajoute le fichier PDF privé à la paie. Vérifier le total de la suite complète avant de reporter son nombre ici.

## Module 5 — Analyse de la masse salariale

### Évolution et exports alignés sur le frontend — 2026-10-24

`MasseSalarialeService.summarize` renvoie désormais `evolution_mensuelle` et `evolution_annuelle` à partir de la même lecture du repository. Les totaux annuels sont agrégés en Decimal et les employés dédupliqués par ensemble pour chaque année. La méthode `evolution` réutilise ces agrégats, sans seconde logique d’addition. Le service dépend explicitement de `MasseSalarialeRepositoryInterface` ; l’ORM reste dans le repository. Le frontend utilise cette synthèse unique pour ses graphiques de net, coût employeur et cotisations, ainsi que ses ventilations incluant le brut.

`MasseSalarialeExportQuerySerializer` réutilise la validation de l’évolution et accepte `granularite=mensuelle|annuelle`, avec mensuelle par défaut pour les appels existants. La vue transmet ce choix à `MasseSalarialeExportService`. CSV, Excel et PDF conservent les quatre sections ; celle d’évolution devient mensuelle ou annuelle selon le choix. Les exports annuels utilisent les mêmes ensembles d’employés distincts que le tableau de bord. Les fichiers indiquent la granularité dans leur nom. Le filtre département reste fondé sur la classification historique.

Vérifications : 61 tests ciblés SQLite et 9 tests module 5 PostgreSQL réussis, dont déduplication annuelle, montants coût/cotisations, filtre historique, export mensuel par défaut, CSV annuel et cellules numériques Excel, PDF et refus de granularité invalide. Les six exports sont vérifiés en lecture seule sur la base locale et les PDF de recette mensuel/annuel sont rendus et inspectés. Aucun changement de modèle, migration, permission, paie ou contrat. Les parcours visuels frontend de ces nouveaux graphiques restent à effectuer.

### Profil de consultation frontend — 2026-10-23

La migration `0042_frontend_payroll_mass_role` crée le rôle `FRONTEND_MODULE_5_MASSE_SALARIALE` et lui ajoute `paie.read` et `departement.read`, sans affecter de compte à ce rôle. Aucun droit de création, modification ou suppression n’est ajouté. Le droit existant `paie.read` couvre les synthèses, l’évolution, les exports et aussi la lecture globale des paies du module 4 ; il ne limite pas la consultation à des données anonymisées.

Les trois API d’analyse restent disponibles ; depuis le 2026-10-24, le frontend utilise la synthèse enrichie pour obtenir totaux et évolutions en un appel. Les agrégations et classifications historiques demeurent côté backend. Les tests `PayrollMassRoleTests` et `PayrollMassProfileApiTests` contrôlent les droits exacts, l’absence d’attribution automatique, les trois formats d’export, le refus sans permission et l’interdiction de créer une paie avec ce profil.

### Première API de synthèse

- Le circuit suit le pattern du dépôt : la vue valide la requête avec un serializer, le service calcule les indicateurs et une interface/repository dédié lit les paies et leurs dimensions ; aucune requête ORM n'est exécutée depuis la vue ou le service.
- `GET /api/analyses/masse-salariale/?periode_debut=2026-01&periode_fin=2026-12` exige `paie.read`.
- `GET /api/analyses/masse-salariale/evolution/?periode_debut=2026-01&periode_fin=2026-12&granularite=mensuelle` fournit les points mensuels ; passer `granularite=annuelle` pour les regrouper par année. Permission : `paie.read`.
- Le filtre optionnel `departement=<id>` restreint la synthèse au département de l'employé.
- L'API utilise les paies `VALIDEE` et `PAYE` ; les brouillons, paies calculées non validées et paies annulées sont exclus.
- La réponse distingue les totaux validés des totaux payés et inclut le brut, le net, les cotisations, le coût employeur, le nombre de paies, une évolution par période, une ventilation départementale et une ventilation par type de contrat.
- Au calcul, le snapshot de paie conserve le département et les types de contrat observés à ce moment. Les analyses et leur filtre département utilisent ce snapshot même si les informations RH changent ensuite. Les anciennes paies sans cette classification apparaissent avec « Historique indisponible » ; aucun historique manquant n'est reconstitué silencieusement depuis les données actuelles. Quand plusieurs types sont attachés au contrat au calcul, la paie apparaît dans chaque catégorie et les catégories ne s'additionnent pas.
- `GET /api/analyses/masse-salariale/export/?periode_debut=2026-01&periode_fin=2026-12&format_fichier=csv` exporte le rapport complet. Formats possibles : `csv`, `xlsx` (Excel) et `pdf`. Le filtre `departement=<id>` s'applique aussi aux exports ; permission requise : `paie.read`.
- Les périodes sont validées au format `AAAA-MM`, l'année et le mois doivent exister dans le calendrier, et la période de début ne peut pas être postérieure à la période de fin. Vérification : `manage.py check` sans erreur et les 35 tests `DomainCrudTests` réussis.
- Contrôle API effectué sur la base locale avec trois employés fictifs `DEMO-M5`, trois départements, trois types de contrat et neuf paies pour `2026-08` à `2026-10` ; cinq paies ont un ordre traité associé. Les routes de synthèse et d'évolution mensuelle/annuelle, ainsi que le filtre département historique, ont été vérifiés. Une paie validée préexistante sans snapshot est indiquée « Historique indisponible » dans les ventilations et reste incluse dans les totaux globaux.

## Module 7 — Feuilles de temps

### Étape 1 — Projets, tâches et affectations

Les modèles `Projet`, `TacheProjet` et `AffectationProjet`, leurs routes CRUD et les permissions `projet.*`, `tache.*` et `projet.assign_employees` sont câblés par la migration `0027_projet_tacheprojet_affectationprojet.py`. La migration doit être appliquée avant d'utiliser ces endpoints.

### Étape 2 — Modèles hebdomadaires et horaire contractuel

`FeuilleTemps` représente une feuille d'un employé pour une semaine débutant le lundi. Une contrainte unique interdit deux feuilles pour le même employé et la même semaine. Les statuts prévus pour le workflow sont `BROUILLON`, `SOUMISE` et `VALIDEE`.

`LigneFeuilleTemps` enregistre une date de travail, un projet, une tâche, les heures décimales (de 0,01 à 24,00 par ligne) et un commentaire. La validation du modèle vérifie que la semaine commence un lundi, que la date de la ligne appartient à cette semaine et que la tâche appartient au projet sélectionné. Le modèle protège les projets et tâches référencés par des lignes contre la suppression, afin de préserver les historiques.

Le champ `Contrat.heures_journalieres` stocke l'horaire quotidien prévu entre 0,01 et 24,00 heures. Il reste nullable en base pour préserver les contrats historiques qui n'ont pas encore été renseignés ; l'API de création et de mise à jour du contrat exige désormais une valeur. Les contrats existants doivent être mis à jour avant de servir au contrôle des heures.

La migration `0028_feuille_temps_and_contrat_hours.py` ajoute le champ contractuel et crée les deux tables.

### Étape 3 — API de saisie et soumission par l'employé (implémentée)

L'API suit le pattern du projet : serializers de lecture/écriture et de filtres → vues HTTP → service → interface/repository → modèles.

Toutes les routes exigent une authentification. L'identité employé vient de l'utilisateur connecté ; le client ne peut pas choisir l'employé ni forcer un statut. Un utilisateur ne peut lire, modifier ou supprimer que ses propres feuilles.

- `GET /api/feuilles-temps/?semaine_debut=2026-10-19` liste les feuilles de cette semaine lundi-dimanche.
- `GET /api/feuilles-temps/?date_travail=2026-10-20` liste les feuilles qui comportent une ligne pour cette date.
- `POST /api/feuilles-temps/` crée le brouillon et ses lignes atomiquement. Exemple de corps JSON :

```json
{
  "semaine_debut": "2026-10-19",
  "lignes": [
    {
      "date_travail": "2026-10-20",
      "projet": 3,
      "tache": 8,
      "heures": "4.00",
      "commentaire": "Analyse"
    },
    {
      "date_travail": "2026-10-20",
      "projet": 3,
      "tache": 8,
      "heures": "3.50",
      "commentaire": "Préparation du livrable"
    }
  ]
}
```

`projet` et `tache` sont des identifiants existants. Les dates doivent appartenir à la semaine ; le projet doit être actif et l'employé affecté ; la tâche doit être active et appartenir à ce projet.

- `GET /api/feuilles-temps/{id}/` renvoie une feuille et ses lignes.
- `PUT /api/feuilles-temps/{id}/` remplace toutes les lignes d'un brouillon ; renvoyer `semaine_debut` et la liste complète `lignes`. Une feuille soumise est verrouillée. Modifier une feuille validée la remet au statut `BROUILLON`, afin d'imposer une nouvelle soumission et validation.
- `DELETE /api/feuilles-temps/{id}/` supprime uniquement un brouillon.
- `POST /api/feuilles-temps/{id}/soumettre/` soumet une feuille non vide ; aucun corps n'est nécessaire. Le statut devient `SOUMISE`.

Le total des lignes par date est comparé à `Contrat.heures_journalieres`. L'enregistrement est refusé si aucun contrat ne couvre la date, si plusieurs contrats la couvrent, si l'horaire est absent ou si le cumul dépasse l'horaire prévu. Un contrat historique sans horaire doit être complété avant la saisie.

Les 13 tests ciblés des feuilles de temps et des décisions ont réussi sur PostgreSQL de test le 2026-10-22 ; la base de développement est restée inchangée.

### Étape 4 — Validation ou refus par un gestionnaire (implémentée, tests réussis sur SQLite)

La migration `0029_feuille_temps_decision.py` ajoute `valideur`, `date_decision` et `motif_refus` à la feuille, et crée la permission dédiée `feuille_temps.decide`. La migration attribue cette permission au rôle `ADMIN_RH` déjà présent ; elle peut aussi être attribuée à un rôle gestionnaire. Un compte sans cette permission reçoit `403` sur la file de validation et les actions de décision.

- `GET /api/feuilles-temps/a-valider/` retourne les seules feuilles au statut `SOUMISE`, avec l'employé, la semaine et le détail des lignes.
- `POST /api/feuilles-temps/{id}/valider/` accepte un corps vide. Seule une feuille soumise peut être validée ; son statut devient `VALIDEE` et son valideur/date de décision sont enregistrés.
- `POST /api/feuilles-temps/{id}/refuser/` exige le corps :

```json
{
  "motif": "Merci de préciser le temps consacré à la tâche du mardi."
}
```

Le motif est nettoyé des espaces de début et de fin. Une feuille refusée revient en `BROUILLON`, avec le motif, le valideur et la date conservés pour l'employé. Au prochain envoi, les anciennes métadonnées de refus sont effacées. Toute décision répétée sur une feuille qui n'est plus soumise est refusée.

Les 13 tests ciblés des feuilles de temps et des décisions ont réussi sur PostgreSQL de test le 2026-10-22 ; la base de développement est restée inchangée.

### Étapes restantes

Les interfaces de saisie et de validation restent à construire ; les vérifications ciblées PostgreSQL sur la base de test sont terminées.

### Étape 6 — Calcul backend des coûts par projet et tâche (implémenté, tests réussis)

`GET /api/analyses/couts-projets/?date_debut=2026-10-01&date_fin=2026-10-31` fournit une estimation par projet et tâche, sur une période incluse, avec les heures validées, un sous-total éventuellement calculable et l'indication de complétude. La permission requise est `paie.read`.

Seules les lignes liées à une feuille `VALIDEE` sont incluses. Pour chaque employé et mois travaillé, le calcul reprend le taux chargé journalier du TGM pour ce mois, puis applique `taux horaire = TGM chargé journalier / 8` et `coût ligne = heures validées × taux horaire`. Une paie validée ou payée est nécessaire au calcul du TGM correspondant.

La réponse distingue ces champs :

- `heures_validees` : total des heures incluses.
- `heures_sans_tgm` : heures pour lesquelles aucun taux TGM n'est disponible.
- `cout_calculable` : sous-total des lignes pour lesquelles le TGM existe ; il peut être partiel.
- `cout_estime` : total uniquement lorsque toutes les heures ont un TGM, sinon `null`.
- `cout_complet` : indique si l'estimation couvre toutes les heures.

Les mêmes données sont retournées au total, par projet et par tâche. Ce calcul est une estimation basée sur le TGM mensuel ; il n'impute pas un coût réel et ne remplace pas la comptabilité analytique.

Les 13 tests ciblés des feuilles de temps et des décisions ont réussi sur PostgreSQL de test le 2026-10-22 ; la base de développement est restée inchangée.

### Étapes à venir

7. La validation PostgreSQL de test des migrations 0027 à 0029 et des parcours API ciblés est terminée.
# Revue clean code — 2026-10-22

`SoldeCongeService` mutualise le regroupement des jours ouvrés et la construction des soldes. Les filtres ORM de recalcul sont délégués à `SoldeCongeRepository`, conformément à son interface. Les 21 tests existants des demandes et soldes passent sur une base SQLite de test isolée ; les tests de concurrence PostgreSQL et la revue des autres services restent à poursuivre.


## Parametrage CONG_PAY - 2026-10-22

## Consultation détaillée d'une demande — 2026-10-22

Les rôles `ADMIN_RH` et `FRONTEND_MODULE_2_CONGES_ABSENCES` disposent de `demande_absence.read` et `demande_absence.update` dans la base de développement. La seconde permission a été ajoutée au profil module 2 via `RoleService.add_permissions`, sans modifier les autres permissions. Elle autorise également validation et refus : ce profil est destiné aux gestionnaires, pas aux simples employés.

La route `GET /api/demandes-absence/{id}/` utilise `DemandeAbsenceDetailSerializer`, qui conserve les champs existants et ajoute `employe_nom`, `employe_prenom`, `employe_matricule`, `departement_nom`, `valideur_nom` et `valideur_prenom`. Le département et le valideur absents sont représentés par `null`. Aucun renseignement bancaire ou numéro de sécurité sociale n'est ajouté.

La vue vérifie les permissions sur la demande avant de la sérialiser. Le service délègue la recherche au repository, qui utilise `select_related` pour charger employé, département, type de congé et valideur en une requête. Le format des listes et les règles de validation/refus sont conservés. Tests : lecture personnelle, refus de lecture d'autrui, lecture par le gestionnaire, valeurs absentes et nombre de requêtes vérifiés ; 25 tests demandes/soldes réussis.

### Paramétrage existant du quota

Le droit annuel CONG_PAY et le solde individuel 2026 existant sont fixes a 30 jours dans la base de developpement. Le service utilise maintenant uniquement le droit annuel du type, commun a tous. Les demandes sont conservees : 17 jours pris, 92 en attente et -79 disponibles apres recalcul. Aucun changement des couches API, services ou repositories pour cette correction frontend.

## Planning et roles multiples - 2026-10-22

AuthenticationRepository cumule deja les permissions de tous les roles. PlanningEventsListView utilise demande_absence.update pour la vue transversale et demande_absence.read pour la lecture. La nouvelle presentation frontend reutilise les noms, departements et libelles deja renvoyes par PlanningService. Le Repository Pattern est conserve ; aucun role unique suppose. Test du cumul sur deux roles verifie dans les 26 tests demandes/soldes.

## Droits annuels communs et codes automatiques — 2026-10-22

`TypeConge.jours_par_annee` est la source unique du droit annuel pour tous les employés. `SoldeCongeService.get_balances` et `validate_request_quota` utilisent cette valeur, même si une ancienne ligne `SoldeConge.acquis` indique autre chose. Les jours pris et en attente sont déduits des demandes. Les demandes existantes ne sont jamais supprimées lors d'un changement de quota.

Le repository `entitlements` regroupe les soldes enregistrés et complète les droits manquants pour les employés présents dans l'année et les types actifs, sans écriture dans un GET. Les soldes calculés sans ligne persistée ont un identifiant null. Les types inactifs ayant un historique restent visibles. Toutes les requêtes restent dans les repositories.

Les anciennes routes POST de création et PUT de modification individuelle ne permettent plus d'écrire : 405 pour les comptes disposant encore des anciens droits, 403 sinon. Le seul moyen de changer le droit est de modifier le type, pour tous. `TypeCongeRepository.update` synchronise les valeurs `acquis` enregistrées ; la migration 0031 a aligné les anciennes valeurs dans la base de développement. Ces droits communs s'appliquent aussi aux années historiques consultées, sans mécanisme de droit annuel par période.

Le code est en lecture seule dans `TypeCongeSerializer`. `CongeService.create_type` génère un code `CONGE_` avec un suffixe aléatoire ; le service de modification ignore toute tentative de changement du code. Les codes des types existants sont conservés. Les contraintes d'unicité restent assurées par le modèle.

`FRONTEND_MODULE_2_CONGES_ABSENCES` dispose de 9 droits : CRUD des types, CRUD des demandes, `solde_conge.read`. La lecture de tous les soldes nécessite aussi `demande_absence.update`. Les permissions de tous les rôles se cumulent. L'ancienne attribution individuelle ne demande plus de sélecteur d'employé. Les 38 tests couvrent notamment la source de quota commune, les anciens quotas divergents, les droits automatiques sans demande, l'absence d'écritures dans le GET, la génération/immutabilité des codes et le refus des anciennes écritures individuelles.
## Scénario de validation API — 2026-10-23

`test_complete_leave_workflow_with_jwt_and_common_quota` enchaîne les routes HTTP avec des jetons obtenus par `/api/auth/login/`, en alternant un employé et un gestionnaire de test. Il vérifie le droit commun, les jours en attente/pris/disponibles, le refus d'une décision non autorisée, la validation, le planning, le refus d'une autre demande et la suppression d'une demande en attente. Ce scénario appartient aux 117 tests `core` réussis sur SQLite isolé ; il ne constitue pas une validation navigateur. Aucun changement des couches applicatives ni de leurs règles métier n'a été nécessaire pendant cette passe.


## Module 3 : accès documentaires et interface — 2026-10-23

La migration 0032 crée document.manage pour la gestion transversale, attribuée à ADMIN_RH. HasDocumentAccess exige le droit CRUD correspondant et, pour toute écriture, document.manage. Une lecture sans ce droit est limitée aux documents associés au compte : liste via service.get_for_employee, détail via check_object_permissions et service.belongs_to. HasDocumentEmployeeAccess applique la même isolation aux liaisons : un employé ne peut pas se rattacher à un document tiers. L'accès aux données reste dans les repositories, via leurs interfaces.

DocumentSerializer ajoute le libellé du type, vérifie les dates et refuse les nouveaux types inactifs. Les associations de plusieurs employés sont conservées et leurs écritures sont transactionnelles. TypeDocumentService génère les codes DOC_ automatiquement ; le serializer les rend non modifiables. Le repository refuse de supprimer un type utilisé et le service renvoie une erreur lisible invitant à le désactiver.

Le profil frontend module 3 avait initialement été créé avec des droits bancaires et documentaires. Son périmètre actuel est limité aux droits bancaires décrits ci-dessous. Aucun compte n’a changé de rôle. Les références documentaires ne sont ni un stockage de fichiers ni un téléchargement authentifié.

Validation : 124 tests globaux réussis, puis 8 tests module 3 ciblés réussis après le dernier ajustement. Ils couvrent lecture personnelle, refus de lecture d'autrui, refus d'écriture sans manage, gestion des associations, dates, types utilisés/inactifs et cumul de permissions sur plusieurs rôles. Tous utilisent SQLite de test isolé. Aucune validation navigateur n'est revendiquée.

## Réduction du périmètre frontend module 3 — 2026-10-23

À la demande utilisateur, les sections documentaires sont retirées du frontend, sans suppression des données ni des API. Les permissions document.*, document_employe.* et type_document.* ont été retirées du seul rôle FRONTEND_MODULE_3_DOSSIERS_BANCAIRES_JURIDIQUES. Ses droits bancaires existants ont été conservés : coordonnees_bancaires.read/create/update/delete et employe.read (5 droits constatés). Aucun nouveau droit manage bancaire n'a été attribué. Les autres rôles conservent leurs permissions. Les champs frontend perdent les mentions fictif/fictive ; le chiffrement bancaire a ensuite été activé le 2026-10-23, comme décrit dans le guide dédié.

## Stockage bancaire chiffré — 2026-10-23

Le stockage des champs IBAN, BIC et SWIFT est chiffré (Fernet), avec empreinte HMAC pour l'unicité de l'IBAN. La migration 0033 est appliquée sur PostgreSQL local : deux fiches conservées et vérifiées par comparaison à la sauvegarde chiffrée. La clé est chargée hors dépôt ; voir [BANK_DATA_ENCRYPTION.md](BANK_DATA_ENCRYPTION.md). Les réponses API autorisées restent lisibles ; les permissions sont inchangées.

Les champs personnalisés assurent le chiffrement à la frontière ORM/base. Le repository utilise iban_fingerprint pour détecter les doublons ; le service les convertit en erreur de validation HTTP 400. Aucune requête ORM ajoutée aux vues ou services. La migration transactionnelle conserve les valeurs, propriétaires et dates ; aucun retour automatique en clair.

Vérifications : 133 tests core sur SQLite, 15 tests ciblés sur PostgreSQL, migration de données historiques sur base temporaire et contrôle SQL des deux fiches actives réussis. Clé éphémère pour les bases de test ; sauvegarde chiffrée préalable hors dépôt. Parcours navigateur non vérifié.

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

## Module 6 — TGM et rentabilité simulée, 2026-10-25

`TgmListView` expose `TgmQuerySerializer` puis `TgmService.calculate` sur `/api/analyses/tgm/`. `TgmRepositoryInterface` sépare les lectures des paies finalisées et contrats. Les montants restent en Decimal ; les taux sont arrondis à deux décimales avec `ROUND_HALF_UP` uniquement à la présentation.

Le service compte les jours lundi-vendredi couverts par un contrat pendant l’emploi, uniquement dans les mois ayant une paie validée ou payée. Chaque jour est compté une fois. Les heures prévues proviennent de l’unique contrat couvrant ce jour ; un horaire absent ou un chevauchement rend le dénominateur horaire indisponible. Les journées à quatre ou six heures et les changements de contrat au milieu du mois sont pris en compte. Les jours fériés et calendriers hebdomadaires individualisés ne sont pas modélisés. Une modification des contrats actuels peut modifier les estimations historiques.

`CoutProjetService` réutilise un rapport TGM par mois, calcule le taux chargé à partir du coût et des heures sans arrondi intermédiaire, puis multiplie par les heures validées. Les lignes non validées sont exclues ; les résultats sont ventilés par projet, tâche et employé. Les coûts sont limités à XOF ; les autres devises ne sont pas converties. Toute heure non chiffrable rend `cout_estime` nul et conserve `cout_calculable` comme sous-total.

`RentabiliteProjetView` utilise `RentabiliteProjetQuerySerializer` (dates, projet, chiffre d’affaires Decimal positif ou nul) et `CoutProjetService.simulate`. La marge correspond uniquement à CA − coût du personnel complet ; le taux de marge rapporte ce montant au CA. Coût incomplet : marge et pourcentage nuls au sens JSON (`null`), sans masquer les heures sans taux. CA égal à zéro : marge calculable, pourcentage `null`. Aucun modèle ni scénario n’est créé ; `paie.read` protège les trois consultations.

## Module 7 — Saisie en heures/jours et rapprochement, 2026-10-25

`LigneFeuilleTempsInputSerializer` exige exactement une unité : `heures` ou `jours`. Le service `FeuilleTempsService` transforme chaque fraction de journée par l’horaire journalier du contrat couvrant cette date, arrondit à deux décimales puis applique les validations existantes de semaine, affectation, tâche active et plafond quotidien cumulé. Le stockage reste en heures ; une demi-journée sur un contrat à six heures devient trois heures. Contrat absent, horaire manquant et contrats concurrents sont refusés.

Les lectures personnelles restent limitées à l’employé connecté. `FeuilleTempsRepository.get_for_employee_for_update` verrouille la feuille pendant une modification, une soumission ou une suppression ; la décision utilise déjà un verrou. Une feuille soumise est immuable jusqu’à la décision. Le refus la remet en brouillon avec motif ; une nouvelle soumission efface l’ancienne décision. Modifier une feuille validée la remet également en brouillon, ce qui l’exclut des coûts jusqu’à sa prochaine validation.

`FeuilleTempsSerializer` renvoie les lignes, leurs heures totales, le nombre de dates distinctes saisies, le matricule et le décideur. Les relations sont préchargées dans le repository. Le nombre de dates n’est pas une conversion en journées équivalentes : deux heures sur une date représentent une date saisie, pas une journée complète.

`CoutProjetService.summarize` construit le champ `rapprochement` pour chaque triplet projet/employé/mois. Il prend exclusivement les lignes des feuilles validées, réutilise le taux chargé du mois calculé par le module 6 et multiplie les heures par ce taux sans arrondi intermédiaire. Le rapport expose aussi le taux arrondi pour lecture, le coût calculable et les heures sans TGM ; les coûts incomplets restent `null`. Son accès reste limité à `paie.read`, indépendamment des droits de saisie ou de décision.

Le circuit est donc : projet/tâche/affectation → brouillon personnel → soumission → décision → heures validées × taux mensuel → coût projet. Les API de projets et affectations gardent leurs contrôles existants. La décision est centralisée pour les comptes possédant `feuille_temps.decide` ; aucun modèle de rattachement hiérarchique n’a été ajouté. Aucun schéma ni droit actif n’a été modifié pour cette livraison.

## Profils personnels et modules 6/7 — 2026-10-25

La migration `0044_remaining_module_and_employee_roles` crée les profils `EMPLOYE_SIMPLE`, `FRONTEND_MODULE_6_TGM` et `FRONTEND_MODULE_7_FEUILLES_TEMPS`, sans rattacher d’employé. Les sept droits du profil simple sont `conge.read`, `demande_absence.read/create`, `solde_conge.read` et `coordonnees_bancaires.read/create/update`. Les API personnelles limitent les listes au propriétaire et refusent les lectures/écritures d’un tiers. Les routes personnelles de temps reposent déjà sur l’authentification et le propriétaire, sans utiliser de droits CRUD génériques.

Le profil TGM contient `paie.read`, qui couvre aussi les paies globales et la masse salariale. Le gestionnaire module 7 contient `feuille_temps.decide`, `projet.read/create/assign_employees`, `tache.read/create` et `employe.read` ; il ne reçoit aucun accès financier implicite. Les profils peuvent être cumulés pour un gestionnaire explicitement autorisé aux coûts.

L’activation sur la base locale a ajouté uniquement `EMPLOYE_SIMPLE` à Awa (id 18) et Moussa (id 19), après vérification exacte des comptes. Les autres rôles et affectations, mots de passe et statuts sont conservés. Le script `tmp/activate_remaining_roles.py` conserve des instantanés avant/après sans mot de passe. `test_remaining_role_profiles.py` vérifie les jeux de droits, l’isolation propriétaire, les refus d’administration/paie/validation et les fonctions des gestionnaires. Les parcours réels après attribution ont été contrôlés uniquement en lecture.

## Références automatiques projets/tâches — 2026-10-25

Les créations via `ProjetService` ajoutent un code à partir d’un UUID : `PROJ_<24 hex>` ou `TASK_<24 hex>`, sur 29 caractères maximum dans un champ de 30. Le code est calculé côté serveur, indépendamment de la saisie du client. `ProjetSerializer` et `TacheProjetSerializer` le déclarent en lecture seule, tandis que les méthodes de mise à jour du service retirent aussi toute tentative de modification du code. Aucun modèle ni code historique n’est migré.

La validation du nom unique d’une tâche dans son projet est conservée. Les codes restent protégés par les contraintes existantes de base de données. `FeuilleTempsProjectOptionsView` renvoie une réponse personnelle non mise en cache, contenant uniquement les projets actifs affectés et leurs tâches actives. Aucune permission de gestion ou de consultation globale des tâches n’est nécessaire à l’employé pour choisir sa tâche dans une feuille personnelle.

`test_project_time_entry.py` couvre création sans code, code fourni ignoré, codes distincts, noms de tâches en doublon, préservation des anciens codes, actualisation des options après affectation et ajout d’une tâche, exclusion des autres projets/tâches inactifs, enregistrement/soumission avec un rôle simple et refus d’auto-affectation. Les vérifications réelles d’Awa/Moussa restent en lecture seule ; les écritures de recette sont isolées.

## Génération et archivage automatiques du bulletin - 2026-10-26

PaieService.valider est transactionnel et verrouille la ligne de paie. Après les contrôles d'état, il enregistre le valideur, la date et l'état VALIDEE dans la transaction puis appelle generate_bulletin. Cette méthode verrouille également la ligne, réutilise un bulletin existant ou produit le PDF à partir de detail_calcul et le sauvegarde via PaieRepository.save_bulletin.

Une erreur remonte avant la fin de la transaction et annule les changements en base. Une erreur de stockage est traduite en message lisible. Le repository nettoie le nouveau fichier si la sauvegarde du modèle échoue après l'écriture du PDF. Les contenus téléchargés restent identiques à l'archive, y compris après modification ultérieure du nom de l'employé. Les anciennes paies validées sans bulletin conservent l'action de génération de rattrapage.

Les tests couvrent création du PDF à la validation, téléchargement propriétaire sans génération préalable, conservation des octets archivés, absence de doublon, refus d'une seconde validation, données de calcul incomplètes, panne de stockage avec nouvelle tentative et nettoyage après panne de sauvegarde.

## Liste personnelle des bulletins - 2026-10-26

PaieRepository.for_employee filtre strictement employe_id et les états VALIDEE/PAYE. PersonalPayslipListView appelle ce filtre avec request.user.pk et sérialise uniquement les données personnelles nécessaires via PersonalPayslipSerializer. Un paramètre employe externe n'élargit pas ce périmètre. Les brouillons, calculs non validés et annulations sont exclus de la liste. Le contrôle d'accès du fichier reste celui de PaieBulletinView.

## Historique professionnel et rattachement hiérarchique - 2026-10-26

EmployeService accepte responsable et poste_nom, valide la hiérarchie et délègue la sauvegarde du poste à PosteService. Les champs restent sous les droits existants de gestion des employés. EmployeRepository charge poste/responsable et les contrats courants sans exposer les salaires dans les métadonnées de l'annuaire.

Les services de contrat/poste et de liaison contrat-type construisent des instantanés limités aux champs professionnels. record_change n'inscrit aucun événement lorsque les valeurs restent identiques. Les écritures et événements sont atomiques ; un échec d'historisation annule la modification. Les auteurs sont imposés depuis request.user ; le nom d'auteur est conservé même si son compte est supprimé. Les identifiants d'objet sont de simples références, ce qui conserve les événements après suppression d'un poste ou d'un contrat.

Le journal n'a aucun endpoint d'écriture. La suppression complète d'un dossier employé conserve le comportement existant de suppression de ses données rattachées, dont son historique. Ce suivi applicatif des postes/contrats ne remplace pas un audit global de toutes les opérations critiques ni une interception des écritures SQL externes. Le responsable enregistré n'introduit pas encore les restrictions de validation d'équipe des modules congés/temps, qui restent une étape distincte.

## Catalogue des postes - 2026-10-26

La relation directe Poste.employe est remplacée par Contrat.poste. PosteService gère le catalogue, intercepte les violations d'unicité et les suppressions protégées, et historise les modifications d'un poste pour les employés ayant des contrats associés. ContratService conserve dans ses instantanés le nom et la description du poste au moment de la modification. Une affectation, un changement ou un retrait de poste crée un événement POSTE en plus de l'événement contractuel.

EmployeRepository précharge le poste de chaque contrat courant pour l'affichage et les filtres de l'annuaire. EmployeSerializer renvoie postes_actuels et un libellé poste_nom calculé. Les informations sensibles des contrats ne sont pas ajoutées à ces métadonnées. L'ancien champ de saisie libre sur l'employé est rejeté avec une indication de passer par le contrat.

La migration conserve le plus ancien identifiant lors de la fusion des noms équivalents et concatène les descriptions distinctes. Elle rattache les anciens postes uniquement aux contrats couvrant la date de migration, sans attribuer rétroactivement le poste courant à un ancien contrat. Les anciens états restent consultables dans l'historique même sans contrat courant.
