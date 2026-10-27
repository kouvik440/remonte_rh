# Roadmap frontend Remonte RH

Dernière mise à jour : 2026-10-27

## Configuration JavaScript de l'éditeur — 2026-10-27

- Suppression de `baseUrl` dans `frontend/jsconfig.json`, responsable de l'erreur TS5102 reproduite avec TypeScript 7.0.2. L'alias `@/*` reste explicitement relié à `./src/*`, conformément à l'alias Vite ; JSX et périmètre `src` sont conservés.
- Vérifications : `tsc --project jsconfig.json --noEmit` sans erreur et build Vite réussis. TypeScript a été utilisé temporairement via npm exec, sans ajout aux dépendances du projet. Ce contrôle de configuration n'active pas une vérification complète des types JavaScript.

## Navigation SPA — 2026-10-27

- `AppRouter` pilote les onze écrans dans une même racine React. Le cadre `AppLayout` reste monté entre les modules ; les pages ne créent plus chacune leur navigation.
- `AppLink` intercepte les liens internes et `navigate` utilise l'historique du navigateur. Les connexions, déconnexions et redirections de session utilisent le même mécanisme. Les boutons précédent/suivant sont pris en charge.
- Les onze fichiers HTML par page ont été supprimés. `src/index.html` est l'unique point d'entrée ; Vite compile une application SPA avec `dist/index.html`. Les liens utilisent des routes React sans extension (`/connexion`, `/employes`, `/conges`, etc.). Les anciennes adresses sont converties vers leur route actuelle, avec conservation des paramètres.
- En production, le serveur frontend doit renvoyer `index.html` pour les routes d'interface tout en relayant `/api/` vers Django. Vite assure ce repli en développement et en aperçu.
- Le menu mobile et le profil se ferment au changement de module. Le titre du document, le lien actif, le focus sur le titre de page et le défilement sont actualisés. Les modules restent chargés à la demande et un échec de rendu permet de recharger la page.
- Compilation Vite et cinq tests Node de session/connexion réussis. Recette navigateur sur base temporaire : dix modules à 1440/390 px sans aucun chargement de document entre les modules, cadre conservé, précédent/suivant, dix accès directs et actualisations, connexion/déconnexion, permissions, Ctrl+clic et fermeture des dialogues réussis. Captures et mesures dans `output/spa/`.
- Contrôles complémentaires réussis : navigation avec Entrée, conservation du thème, retour à la connexion sans rechargement après expiration du renouvellement JWT ou catalogue de permissions invalide.
- Recette après suppression des entrées multiples : dix routes sans extension à 1440/390 px, dix accès directs et actualisations, onze conversions d'anciennes adresses, paramètres de connexion préservés, accueil `/` et page inconnue vérifiés. Le build ne contient plus qu'un seul fichier HTML : `dist/index.html`. La route `/connexion` répond également sur le Vite actif 5173.

## Titres des pages — 2026-10-27

- Les six mentions « MODULE 2 » à « MODULE 7 » placées au-dessus des titres ont été retirées. Les noms des pages et leurs descriptions restent affichés.

## Affichage des départements — 2026-10-27

- La liste des départements affiche uniquement leur nom ; la ligne « Code : … » a été retirée.
- Les formulaires de création et de modification demandent uniquement le nom. Le code interne est généré automatiquement par Django à la création et conservé lors d'un renommage.
- Vérifications : compilation Vite, sept tests API PostgreSQL et création/modification dans le navigateur à 1440 et 390 px réussies sur bases de test.

## Mode nuit partagé — 2026-10-27

- `ThemeToggle` propose un bouton accessible pour passer du mode nuit au mode clair. Il est présent dans la navigation, dans la barre mobile et sur la connexion.
- Le mode nuit est la valeur initiale en l'absence de préférence. Le choix est conservé dans le navigateur, synchronisé entre les boutons et les onglets, et maintenu après navigation et déconnexion.
- `shared/lib/theme.js` centralise lecture, application et notifications du thème. Le thème est appliqué avant le montage React ; une indisponibilité du stockage n'empêche pas la bascule pendant la session.
- `themes.css` contient les variantes des surfaces, champs, tableaux, dialogues, statuts, graphiques et menus shadcn portalisés. La classe `dark`, `color-scheme` et la couleur de barre du navigateur suivent le choix.
- Vérifications : build Vite, 40 vues des dix modules à quatre largeurs et 16 ouvertures de formulaires/catalogues, persistance et synchronisation du thème, connexion et mobile. Inspection de l'annuaire nuit sans erreur bloquante ; sous-lignes à 12 px conservées.
- Limite : le thème est une préférence locale à l'appareil ; les PDF générés gardent leur présentation de document.

## Routage de la connexion locale — 2026-10-26

- Correction d'un appel codé en dur au port 8000, occupé par un projet Laravel sans la route RH. Les appels utilisent désormais `/api/`, relayé par Vite vers Django sur 8001 en développement et en aperçu.
- Cible configurable par `REMONTE_RH_API_TARGET` dans `frontend/.env.local`. Une API distante de production peut être configurée explicitement par `VITE_API_BASE_URL` ; à défaut, le serveur de production doit relayer `/api/`.
- Les erreurs 404 et 5xx de connexion affichent une indication lisible sans trace de framework. Instructions de démarrage corrigées avec chemins absolus et Python du venv.
- Vérifications : contrôle Django, build Vite, cinq tests Node, validation des proxys 5173/5191 vers le Django réel et connexion navigateur complète avec un compte sur base temporaire réussis. Aucun droit ni mot de passe de compte réel n'a été modifié.

## Correctifs communs des interfaces — 2026-10-26

État : corrections du socle React et des styles appliquées, compilation et parcours de recette effectués.

- `FormField` relie explicitement chaque libellé à son contrôle et chaque erreur à sa description, pour garder un nom accessible stable pendant une validation.
- `ModalDialog` dispose d'une fermeture visible même si son contenu est en chargement ou en erreur. Les boutons restent bloqués pendant une opération en cours.
- Le hook partagé `useBodyScrollLock` conserve le verrou du fond jusqu'à la fermeture de la dernière fenêtre, y compris lorsqu'un catalogue est ouvert depuis les contrats.
- Session : `getUser` normalise les valeurs locales non objet ; `hasPermission` refuse les catalogues de droits qui ne sont pas des tableaux. Une session invalide suit la redirection de connexion sans écran blanc.
- Styles : correction des couleurs héritées du thème sombre, des légendes et cases à cocher, des marges implicites des boutons, de l'alignement des entêtes et des séparateurs de compteurs à 1024 px. Fermeture de formulaire conservée à droite et pieds de dialogue adaptés aux petits écrans.
- Vérifications : build Vite, tests Node du lecteur de session, dix modules à 1440/1024/768/390 px, huit formulaires à 1440/390 px, navigation selon les droits, modification du profil et changement de mot de passe sur base temporaire. Captures et mesures dans `.taste-skill/bugs-before/` et `.taste-skill/bugs-after/`.
- Limite : cette recette contrôle les régressions du frontend et les parcours cités ; elle ne remplace pas une nouvelle recette métier exhaustive de tous les CRUD et calculs de paie.

Le frontend utilise React et Vite. Les interfaces sont rangées dans `frontend/src/modules/module-N/`; les fichiers backend et leurs règles sont décrits dans [ROADMAP_backend.md](ROADMAP_backend.md).

## Chargement commun des pages — 2026-10-23

- Les onze écrans (connexion, employés, départements, rôles, congés, banque, paie, bulletins personnels, masse salariale, TGM, feuilles de temps) sont chargés à la demande. Depuis le 27 octobre, leurs imports sont regroupés dans `app/AppRouter.jsx`, monté par `app/main.jsx`. `PageLoading` affiche le message d'attente dans le cadre partagé, qui reste présent entre les modules.
- Script principal de production : 497,55 Ko avant, 232,87 Ko après séparation ; le fragment Départements représente 5,54 Ko, avec ses petites dépendances communes. Ces tailles ne sont pas des durées de chargement navigateur.
- Dans Vite en développement, le graphe statique initial passe de 84 modules / 5,27 Mo à 15 modules / 1,59 Mo. En ajoutant le code propre aux départements : 22 modules / 1,66 Mo. Mesures des réponses JavaScript locales non compressées via `tmp/measure_frontend_modules.mjs` ; ce n’est pas une mesure réseau à cache vide dans VS Code.
- Le helper API partage uniquement les GET identiques encore en cours pour le même jeton, notamment lors du double lancement des effets en développement. Aucune donnée n’est conservée après résolution ; une actualisation repart au serveur. Les écritures invalident les lectures partageables avant et après leur exécution. Téléchargements et requêtes personnalisées restent indépendants.
- Les demandes simultanées de renouvellement JWT partagent une seule requête. Une réponse 401 tardive réutilise le jeton déjà renouvelé. Les rôles et leur catalogue de permissions sont chargés en parallèle.
- Vérifications : compilation Vite, douze scripts de contrôle frontend dont les cas de concurrence/absence de cache/sessions et téléchargements, analyse des imports servis par Vite et lectures authentifiées des API réussis. L’API département répondait entre 76 et 95 ms pendant les mesures locales ; aucune lenteur équivalente au chargement de tous les modules n’a été observée côté backend. Aucun changement de données métier ni de permissions. Chronométrage interactif à cache vide dans l’aperçu VS Code, clavier et mobile non réalisé pour cette correction.

## Module 1 — Employés et accès

### État : en cours — revue du code et vérifications locales effectuées

- Connexion React, session JWT et redirection vers l’annuaire.
- Annuaire des employés : recherche locale, filtres département/statut et indicateurs d’effectif.
- Suppression employé : utilise `DELETE /api/employes/{id}/`, demande une confirmation mentionnant la suppression des données RH rattachées et empêche les clics répétés pendant la requête. L’API a été vérifiée avec un employé temporaire (204, puis ligne absente).
- Création, modification et suppression selon les permissions. Le formulaire d’employé utilise des cases à cocher pour attribuer plusieurs rôles et affiche un compteur de sélection.
- Écran « Rôles et accès » : consultation, création, modification du nom/description/permissions et suppression confirmée selon les permissions `role.*` du compte.
- Profils de permissions créés dans la base PostgreSQL de développement : `FRONTEND_MODULE_1_EMPLOYES_ACCES` (22 permissions, contrats, types et CRUD départements inclus) et `FRONTEND_MODULE_2_CONGES_ABSENCES` (9 permissions de gestion du module 2, détaillées ci-dessous). Ils ne sont attribués à aucun compte.
- Appels à l’API centralisés dans `src/shared/lib/api.js`; navigation commune dans `src/shared/components/AppLayout.jsx`.
- Corrections de revue : comparaison numérique des identifiants département/rôle, erreurs API lisibles et erreurs de validation reliées aux champs.
- Vérifications locales : `manage.py check` et compilation Vite réussissent; Vite répond sur le port 5174 et les routes API attendues sont présentes.

### À poursuivre

- Correction du 2026-10-22 : les suppressions employé et rôle utilisent un dialogue intégré partagé (`DeleteConfirmation`) à la place de `window.confirm`, afin de ne plus dépendre des fenêtres natives du navigateur. Annulation, confirmation explicite et blocage pendant la requête sont conservés. Compilation vérifiée ; parcours navigateur à confirmer.

- Refaire le parcours dans un navigateur avec un compte de test jetable et des permissions partielles. La validation CRUD réelle reste en attente de ce compte; ne pas utiliser les comptes de la base active pour ces essais.
- Ajouter les filtres poste/contrat et les champs poste/responsable après évolution de l’API backend.
- Refaire les parcours création/modification/suppression dans un navigateur avec des comptes jetables ayant des permissions distinctes (`role.create`, `role.update`, `role.delete`).
- Vérifier visuellement les états chargement, erreur et absence de résultats dans un navigateur disponible.
- La base active contient des comptes existants et le compte de démonstration du dépôt n’y existe pas; aucun dossier n’a été écrit pendant cette revue.

Les composants React du module sont rangés dans `frontend/src/modules/module-1/pages/`. Les routes `/connexion`, `/employes` et `/roles` sont rendues depuis le point d'entrée unique `frontend/src/index.html`.

### Contrats par employé — 2026-10-23

- Bouton « Contrats » dans chaque ligne de l’annuaire avec contrat.read. Dialogue avec historique des contrats, création, modification et suppression confirmée selon les droits CRUD correspondants. Dates, salaire mensuel XOF, heures journalières, statut et types multiples sont éditables ; l’employé reste fixé au dossier ouvert.
- Chargement limité côté serveur à l’employé sélectionné ; libellés des types disponibles en lecture. Les erreurs, chargement, absence de contrats et échecs de mutation sont affichés. Les calculs de paie déjà établis conservent leur snapshot.
- Profil module 1 étendu à 19 droits : CRUD contrat et CRUD type_contrat inclus. Aucun rôle d’un employé modifié ; reconnexion nécessaire pour actualiser le cache des droits.

### Types de contrat et aperçu du contrat dans la paie — 2026-10-23

- Bouton « Types de contrat » dans l’annuaire et « Gérer les types de contrat » dans le dialogue Contrats. Création/modification du libellé et de la description, liste, suppression confirmée. Les droits type_contrat.read/create/update/delete contrôlent ces actions ; un type utilisé est protégé contre la suppression côté backend.
- Un type créé depuis le dialogue des contrats actualise les choix du formulaire sans effacer la saisie du contrat en cours. Aucun code technique à saisir.
- Profil module 1 : 19 droits constatés après migration 0039 ; aucun rôle attribué automatiquement aux employés. Reconnexion pour actualiser les permissions frontend.
- Le formulaire Nouvelle paie et l’action Calculer affichent désormais le contrat correspondant à l’employé et au mois : types, base mensuelle XOF, heures journalières, statut et dates, en lecture seule. Absence de contrat ou plusieurs contrats sur le même mois signalés ; les anciens résultats ne sont pas réécrits.
- Vérifications : 160 tests core SQLite et 79 tests ciblés PostgreSQL réussis ; compilation et huit contrôles frontend réussis. Migrations 0038–0039 appliquées sur PostgreSQL local. Types, contrats, liaisons et paies préservés ; aperçu HTTP comparé à un contrat existant. Parcours navigateur réel non vérifié.

### Départements — 2026-10-23

- Navigation « Départements » et entrée `/departements` dans le module 1, visibles avec `departement.read`. Liste, création et modification du nom et du code, suppression confirmée ; boutons contrôlés par `departement.create/update/delete`.
- Réutilisation du CRUD `/api/departements/` et `/api/departements/{id}/`, des composants de formulaire/dialogue et du helper de mutations. Chargement, erreur, liste vide, erreurs de champs et blocage des doubles soumissions gérés. La page est chargée à la demande.
- La confirmation explique que supprimer le département conserve les employés mais retire leur affectation ; les classifications des paies déjà calculées ne sont pas réécrites.
- Migration 0043 appliquée à PostgreSQL : CRUD département pour `ADMIN_RH` et le profil module 1, maintenant à 22 droits. Le profil masse salariale conserve uniquement `departement.read` ; aucun rôle ajouté à un employé. Une reconnexion actualise les permissions en session.
- Vérifications : 17 tests backend ciblés SQLite, 5 tests CRUD/RBAC PostgreSQL, trois contrôles frontend (départements, contrats/virements, masse salariale), `manage.py check`, compilation Vite et route HTML HTTP 200 réussis. Parcours visuel, clavier et mobile du nouvel écran restant à vérifier ; aucun département de la base active créé, modifié ou supprimé pendant ces tests.

## Module 2 — Congés et absences

### Identité dans les demandes — 2026-10-27

- Les cartes affichent le prénom et le nom de l'employé en gras, puis le motif sur sa propre ligne. L'identifiant « Employé #… » et l'adresse email personnelle ne servent plus de libellé dans cette liste.
- L'identité provient directement de l'API des demandes ; aucun chargement de l'annuaire ni droit supplémentaire n'est requis. Les permissions de consultation et de décision sont conservées.
- Compilation Vite et 23 tests API des accès aux demandes réussis sur PostgreSQL. Liste et détail vérifiés dans le navigateur à 1440 et 390 px sur base temporaire : nom complet, motif distinct, aucun appel à l'annuaire ni débordement horizontal.

### Revue clean code du 2026-10-22


- Bouton « Voir le détail » ajouté sur chaque demande, quel que soit son statut. Fiche modale `LeaveRequestDetail` connectée à `GET /api/demandes-absence/{id}/`, avec chargement, erreur, nouvelle tentative et fermeture par bouton ou Échap. Affiche employé, matricule, département, type, dates, motif, statut et décision. Compilation et rendu serveur des onglets vérifiés ; interaction dans le navigateur à vérifier.

- Planning extrait dans `LeavePlanning.jsx`, avec composants de jour et d'événement séparés ; utilitaires de dates regroupés dans `lib/calendar.js`.
- Compilation Vite vérifiée. La revue clean code du reste des pages demeure à poursuivre.

### État : première interface branchée à l’API

- Navigation ajoutée à `/conges`, affichée si le compte peut consulter les demandes, les soldes ou les types de congé.
- Écran des demandes : liste personnelle ou file de l’équipe selon les permissions, envoi d’une demande, décisions valider/refuser et suppression des demandes en attente selon les droits.
- Planning mensuel connecté à `/api/planning/`; la page distingue les absences validées des présences prévues et indique qu’une présence prévue n’est pas un pointage réel.
- Revue du planning : erreurs de chargement affichées dans la section avec une action « Réessayer », changements rapides de mois protégés contre les réponses réseau arrivant dans le désordre, et événements du jour indexés avant rendu. Les événements affichent le type et le nom complet de l’employé.
- Consultation des soldes annuels et des types de congé, affichée selon les permissions.
- Les cartes de solde affichent maintenant les jours disponibles (quota moins validés et demandes en attente), les jours en attente, les jours pris et le quota acquis. Le backend empêche les demandes dépassant le quota annuel.
- Le formulaire de demande affiche les erreurs de validation sous le champ concerné et signale les succès/échecs de création, validation, refus, suppression et actualisation dans une zone accessible.
- Les actions de création et de décision sont envoyées aux routes backend existantes; le backend reste la source de vérité des permissions et validations.
- Compilation de production vérifiée avec `npm run build` après l’ajout de la page et de son entrée Vite.

### À poursuivre

- Gestion des types et des jours acquis implémentée ; valider maintenant les parcours dans le navigateur avec un compte jetable et des permissions partielles.
- Vérifier le parcours dans le navigateur avec un compte de test jetable et des permissions partielles; la base active contient déjà des comptes.
- Filtres locaux de département et recherche par nom disponibles ; envisager les filtres serveur pour de gros effectifs.
- Valider visuellement dans un navigateur les états de chargement, d’erreur, d’absence de données, les événements nombreux et l’affichage mobile.

## Module 3 — Coordonnées bancaires

### Périmètre ajusté à la demande utilisateur — 2026-10-23

- Page `/coordonnees-bancaires` centrée sur les coordonnées bancaires : suppression des onglets Références documentaires et Types de document, de leurs formulaires et appels API dans cette page.
- Navigation accessible uniquement avec `coordonnees_bancaires.read`. Les boutons Ajouter/Modifier/Supprimer restent contrôlés par leurs permissions respectives. La gestion de tiers exige toujours `coordonnees_bancaires.manage`, avec `employe.read` pour le sélecteur.
- Libellés du formulaire : Banque, IBAN, BIC, SWIFT. L'IBAN reste masqué dans les cartes. Le stockage IBAN/BIC/SWIFT est désormais chiffré côté backend ; l'ancien avertissement de non-activation est retiré.
- Droits documentaires retirés du seul profil FRONTEND_MODULE_3_DOSSIERS_BANCAIRES_JURIDIQUES. Ses droits bancaires préexistants sont conservés : CRUD bancaire et employe.read (5 droits constatés). Aucun droit transversal bancaire ajouté. Les autres rôles, API et données documentaires restent conservés.
- Compilation et quatre contrôles frontend réussis ; validation visuelle utilisateur restante. Le contrôle module 3 vérifie aussi le retrait de l’avertissement obsolète de chiffrement.

## Module 4 — Paie et virements

### Étape 1 implémentée — Gestion des paies, 2026-10-23

- Nouvelle page `/paie` et navigation « Paie et virements », accessibles avec `paie.read`. Liste avec identité, matricule, période, statut, brut/net et filtres locaux par période, statut et recherche.
- Création d'un brouillon : employé, période et libellé. Modification et suppression réservées aux brouillons. Aucun montant calculé saisi à la main.
- Calcul depuis un profil existant et les charges familiales ; le backend vérifie le contrat, les absences, les variables validées et la période. Validation, annulation avec motif, génération du bulletin puis téléchargement PDF authentifié. Actions présentes uniquement dans la liste, détail en consultation seule.
- `PayrollPage` compose les écrans ; hooks distincts pour chargement et actions ; appels API partagés. Les réponses anciennes de chargement sont ignorées, les doubles soumissions bloquées et les erreurs restent visibles. Boutons HTML avec le CSS existant.
- Rôle `FRONTEND_MODULE_4_PAIE_VIREMENTS` créé par migration 0034, étendu par 0037 : CRUD paie, CRUD des ordres, génération du document bancaire et employe.read (10 permissions). Les actions de paie exigent paie.update ; les décisions d’ordre exigent ordre_virement.update. Aucun nouveau rôle attribué automatiquement aux employés. La lecture paie est globale et destinée aux gestionnaires.
- Vérifications : compilation Vite, contrôle `check-payroll.mjs` (permissions, actions par statut, formulaires, détail en lecture seule, PDF et renouvellement JWT), quatre contrôles frontend existants réussis. Backend : 138 tests core sur SQLite isolé puis 6 tests ciblés sur PostgreSQL isolé réussis. Migration 0034 appliquée sur PostgreSQL local ; aucune paie active créée ou modifiée.

### Règles et téléchargement PDF corrigés — 2026-10-23

- Onglet « Règles de paie » : création, modification/suppression avant validation, consultation des paramètres, validation distincte et création d’une nouvelle version d’un profil figé. Taux en pourcentage, tranches IUTS et réductions familiales sous forme de lignes ; aucun JSON à saisir ni taux prérempli. Les permissions paie existantes couvrent ces écrans, sans nouveau droit ni changement de rôle.
- Suppression du mode et des mentions fictives dans le code courant du module. Tout profil exige une référence et une validation avant calcul ; seul un profil actif et validé est sélectionnable. Migration 0035 appliquée sur PostgreSQL local : ancien profil de démonstration désactivé, paies et snapshots historiques conservés.
- Téléchargement : correction de l’en-tête Accept (application/pdf provoquait HTTP 406, */* permet le FileResponse), authentification/renouvellement JWT conservés et type PDF contrôlé. Les anciennes paies sans historique complet n’offrent plus une génération impossible ; l’interface explique l’indisponibilité. Un fichier manquant produit une erreur lisible.
- Vérifications : 143 tests core sur SQLite isolé, 62 tests ciblés sur PostgreSQL isolé, compilation et six contrôles frontend réussis. Téléchargement PDF d’un bulletin existant contrôlé sur l’API locale. Parcours visuel navigateur non vérifié.

### Ordres de virement — 2026-10-23

- Onglet « Ordres de virement », accessible avec ordre_virement.read même sans paie.read. Création/modification d’un ordre généré depuis une paie validée, filtres période/statut, détail en lecture seule et suppression confirmée.
- Traiter, rejeter ou annuler : décision explicite, auteur/date/commentaire conservés. Motif obligatoire pour rejet et annulation. Seuls les ordres générés peuvent évoluer ; aucun deuxième ordre généré/traité pour le même employé et la même période.
- Un ordre traité et daté peut être associé à une paie validée correspondante avec paie.update ; la paie passe à PAYE. Les droits d’ordre seuls ne suffisent pas à marquer la paie payée. Ce suivi ne transmet aucun fichier à une banque.
- Profil module 4 étendu à 9 droits par migration 0037. Migrations 0036–0037 appliquées sur PostgreSQL local ; contrats, paies, ordres existants et affectations des rôles employé conservés.
- Vérifications : 152 tests core sur SQLite isolé, 71 tests ciblés sur PostgreSQL isolé, compilation et sept contrôles frontend réussis. API locales contrats filtrés et ordres : réponses 200 authentifiées. Parcours visuel, clavier/mobile et concurrence simultanée non vérifiés.

### Étapes suivantes

- Étape 2 : gestion des règles réalisée ; formulaires des éléments variables restant à ajouter.
- Étape 3 réalisée : création et suivi des ordres, décisions auditées et association aux paies validées après traitement. Un ordre PDF peut être préparé et téléchargé. Les fichiers d’échange bancaire et la transmission automatique restent un chantier distinct.
- Validation partielle des clics et du rendu réalisée dans l’aperçu VS Code le 2026-10-23, détaillée ci-dessous. Les écritures complètes, le parcours clavier et le mobile restent à vérifier. Le module 4 complet n'est pas déclaré terminé.

### Visibilité du CRUD des ordres — 2026-10-23

- Bouton « Créer un ordre de virement » explicite. Les actions « Modifier l’ordre » et « Supprimer l’ordre » restent limitées au statut GENERE et à leurs permissions ; la liste explique cette règle et le verrouillage des ordres clôturés.
- Vérification en lecture seule : la base active contient quatre ordres TRAITE et un REJETE, donc aucun ordre actuellement modifiable/supprimable. ADMIN_RH et le profil module 4 possèdent les quatre droits ordre_virement. Aucun ordre ni droit modifié.
- Contrôle de rendu contrats/ordres et compilation Vite réussis. Validation visuelle navigateur toujours non effectuée.

### Génération des ordres de virement PDF Burkina Faso — 2026-10-23

- Action « Générer l’ordre PDF » sur un ordre GENERE, puis « Télécharger l’ordre PDF ». Formulaire du donneur d’ordre : entreprise, adresse, banque/agence, RIB BF complet, lieu, date d’exécution, motif, signataire et mode demandé. Le bénéficiaire et le net sont repris du salarié et de la paie validée ; aucun montant bancaire libre n’est saisi.
- Le compte bénéficiaire est choisi parmi les coordonnées bancaires du salarié, affichées masquées. Le PDF utilise un RIB UEMOA de 24 caractères ; le contrôle porte sur sa structure, pas sur la certification du compte. Le module bancaire utilise le libellé RIB / IBAN. Les modes interne, SICA, RTGS ou selon la banque sont proposés, sans choix de routage automatique.
- Génération : fichier PDF privé, téléchargement authentifié, instantané des instructions chiffré en base. Le document est figé ; modifier/supprimer l’ordre documenté n’est plus proposé, mais annuler avec motif reste possible. La génération ne traite pas l’ordre et ne paie pas la paie.
- Nouveau droit ordre_virement.generate_document, avec ordre_virement.read et paie.read, pour générer et télécharger. Accordé à ADMIN_RH et au seul profil module 4 (10 droits). Aucun rôle d’employé réaffecté ; reconnexion pour actualiser les permissions frontend.
- Vérifications : 167 tests core SQLite, 86 tests ciblés PostgreSQL, compilation et neuf contrôles frontend réussis. PDF A4 rendu et inspecté visuellement avec des données de démonstration isolées. Migrations 0040–0041 appliquées en PostgreSQL local, sans générer de document ni de paiement sur les données actives. Parcours navigateur non vérifié.

### Contrôle réel dans l’aperçu VS Code — 2026-10-23

- Page `/paie` testée dans le navigateur intégré de VS Code avec la session existante : les onglets Paies, Règles de paie et Ordres de virement s’affichent correctement.
- Filtres « Généré » des ordres et « Payée » des paies vérifiés par clic ; réinitialisation du filtre des paies vérifiée en fin de test.
- Ouverture du formulaire de création d’ordre, consultation puis fermeture d’une fiche d’ordre traité en lecture seule.
- Ouverture de « Nouvelle paie », sélection d’un salarié et affichage effectif des attributs du contrat ; fermeture sans enregistrer.
- Ouverture de « Nouvelles règles », défilement jusqu’aux barèmes, ajout d’une tranche IUTS et fermeture sans enregistrer.
- Formulaire « Générer l’ordre PDF » ouvert sur l’ordre #9 : le contexte bénéficiaire et le montant s’affichent. Aucun RIB UEMOA complet n’est disponible pour ce salarié ; le message explicatif et le bouton de génération désactivé sont vérifiés. Aucun document bancaire n’est généré.
- Bulletin existant téléchargé par le bouton de la paie, enregistré dans `tmp/bulletin-validation-vscode-20261023.pdf` : fichier de 3 142 octets avec signature PDF et marqueur de fin présents.
- Aucun enregistrement de formulaire ni décision métier exécuté par l’agent. Les validations, refus, suppressions, calculs et paiements ne sont pas déclarés validés visuellement. Aucun test mobile ni parcours clavier complet. Les mentions antérieures « navigateur non vérifié » décrivent les contrôles précédant cette session.

## Module 5 — Masse salariale

**Développement fonctionnel terminé ; recette visuelle à clôturer — revue du 2026-10-25.** Les contrôles interactifs du 2026-10-23 restent partiels. Le module 4 est laissé en attente de reprise à la demande de l’utilisateur ; il n’est pas déclaré terminé.

- Nouvelle page `/masse-salariale`, accessible depuis « Masse salariale » avec `paie.read`.
- Période de début/fin, département et évolution mensuelle ou annuelle. Les filtres sont appliqués sur demande ; les résultats et exports suivent le périmètre appliqué. Les requêtes tardives sont ignorées.
- Synthèses séparées des paies validées en attente de paiement et des paies payées : brut, net, cotisations et coût employeur en XOF. Aucun calcul de total métier dans React.
- Trois graphiques comparatifs mensuels/annuels : net, coût employeur et cotisations, chacun avec sa propre échelle et les séries validées/payées. Tableau accessible reprenant les dix indicateurs ; ventilations historiques par département et type de contrat avec brut, net, cotisations et coût employeur. Les lignes par type restent non additives lorsqu’une paie possède plusieurs types.
- Exports CSV, Excel et PDF authentifiés : période, département et granularité mensuelle/annuelle suivent les filtres appliqués. Les noms de fichier et la section d’évolution indiquent la granularité.
- Profil `FRONTEND_MODULE_5_MASSE_SALARIALE` : `paie.read` et `departement.read`, sans attribution automatique. Le droit `paie.read` existant donne aussi accès à la consultation globale du module 4 ; aucun droit d’écriture ni de génération d’ordre n’est ajouté.
- Contrôles automatisés : `node check-payroll-mass.mjs`, non-régression des téléchargements module 4 et compilation Vite. Tests API et du profil module 5 exécutés avec les tests métier de masse salariale.
- Contrôle réel dans l’aperçu VS Code : tableau initial, synthèses séparées, graphique mensuel, ventilations, filtre Direction RH appliqué et passage à l’évolution annuelle vérifiés. Le choix de filtre conserve l’ancien périmètre jusqu’au clic « Afficher l’analyse » ; le chargement masque les anciens résultats.
- Les boutons CSV, Excel et PDF ont chacun déclenché un téléchargement, enregistré dans `tmp/masse-validation-vscode-20261023.csv`, `.xlsx` et `.pdf`. Vérification des quatre sections CSV, de l’archive Excel avec quatre feuilles et de la signature/fin du PDF. Tailles : 2 063, 4 463 et 4 679 octets. Aucun montant ni aucune donnée métier modifiés.
- Présentation shadcn intégrée le 2026-10-23 : composants officiels `Card`, `Table` et `Select`, ajoutés par la CLI dans `src/shared/components/ui/`. `MassPanel` compose les cartes ; `MassSelect` gère les sélecteurs avec labels associés. Les boutons d’action gardent le HTML et le CSS existants, conformément à la préférence utilisateur.
- Le conteneur du module utilise des colonnes adaptatives à sa propre largeur. Les tableaux possèdent chacun leur zone de défilement horizontal accessible au clavier ; les styles spécifiques sont limités au module. Les cartes, l’ouverture/sélection des deux menus, l’application de Direction RH + évolution annuelle, les montants et le défilement interne des tableaux ont été contrôlés dans VS Code. L’ancienne présentation qui débordait est remplacée ; la largeur et les espacements dans l’aperçu restent à revoir sur plusieurs dimensions avant une validation visuelle complète.
- Contrôles après intégration : rendu/permissions/filtres/exports du module 5, non-régression paie et contrats/virements, compilation Vite. Aucun changement des calculs, des API ou des permissions. Le module n’est pas déclaré terminé : dates inversées, périmètre vide, permissions partielles, parcours clavier complet et mobile restent à vérifier dans l’interface.
- Compléments du 2026-10-24 : `MassComparisonChart` réutilisé pour les trois indicateurs ; colonnes de ventilation partagées via `massMetrics.js`. Un seul appel de synthèse fournit les totaux et les deux évolutions déjà agrégées par le serveur ; aucun regroupement financier effectué dans React. Card/Table shadcn et boutons HTML conservés.
- Vérifications du 2026-10-24 : 61 tests backend ciblés SQLite, 9 tests module 5 PostgreSQL, douze scripts frontend et compilation réussis. Les six exports (trois formats × deux granularités) sont vérifiés en lecture seule sur la base locale ; le serveur HTTP expose bien l’évolution annuelle. PDF mensuel/annuel de recette rendus et inspectés. Aucune donnée métier ni permission modifiée. Les trois nouveaux graphiques et les tableaux élargis restent à vérifier visuellement, au clavier et sur mobile dans le navigateur.

- Revue du 2026-10-25 : 61 tests backend ciblés, contrôle `check-payroll-mass.mjs` et compilation Vite réussis. Aucun échec détecté. La recette navigateur complète (mobile, clavier, nouveaux graphiques, dates inversées, résultats vides et permissions partielles) reste ouverte. Le module 6 devient le chantier actif.

## Module 6 — Calcul du TGM et coûts projets

**Première version implémentée le 2026-10-25, avec simulation de chiffre d’affaires demandée par l’utilisateur.**

- Page `/tgm`, chargée à la demande et accessible depuis « TGM et coûts projets » avec `paie.read`. Aucun rôle ni compte modifié.
- Périodes mensuelles appliquées sur demande ; états de chargement, erreurs et reprise indépendants pour les taux et coûts. Les réponses tardives sont ignorées ; les résultats du périmètre précédent sont masqués.
- Tableau par employé et devise : brut, coût chargé, jours et heures prévisionnels, taux journaliers et horaires bruts/chargés. Les taux viennent du serveur ; React assure uniquement la présentation.
- Coûts des heures validées en XOF, par projet, tâche et employé. Les détails sont dépliables. Les heures sans taux, le sous-total chiffrable et le coût complet sont distingués.
- Simulation temporaire : projet et chiffre d’affaires XOF de la période ; marge après coût de personnel et pourcentage calculés par le backend. Marge indisponible si le coût est incomplet ; pourcentage indisponible pour un chiffre d’affaires nul. Aucun enregistrement du scénario.
- Hypothèses affichées : lundi-vendredi, jours fériés non déduits, heures journalières des contrats actuels, mois avec paies finalisées uniquement. Les horaires manquants/ambigus sont signalés ; aucune conversion de devise automatique.
- Contrôles automatisés et recette navigateur : voir la validation datée en fin de document. La validation métier des hypothèses et l’historisation des horaires restent à traiter avant de qualifier ces estimations de coûts comptables définitifs.

## Module 7 — Feuilles de temps

**Première version fonctionnelle implémentée le 2026-10-25.** Les temps validés alimentent les coûts du module 6.

- Page `/feuilles-de-temps`, chargée à la demande depuis le menu « Feuilles de temps ». La saisie personnelle est ouverte à chaque employé authentifié ; aucun droit de consultation des salaires n’est nécessaire.
- « Mes feuilles » : liste personnelle, filtre par date travaillée, nouvelle semaine commençant un lundi, lignes quotidiennes par projet/tâche/commentaire, saisie en heures ou fractions de journée. Une journée est convertie par le serveur selon l’horaire contractuel de cette date ; le stockage et la réédition utilisent des heures.
- Brouillon enregistrable, modification et suppression avec confirmation ; soumission avec confirmation puis verrouillage jusqu’à la décision. Une feuille validée peut être corrigée avec avertissement explicite : elle retourne en brouillon et sort des coûts jusqu’à une nouvelle validation. Le total d’heures et le nombre de dates renseignées viennent du serveur ; les dates renseignées ne représentent pas des équivalents de journées complètes.
- « À valider », réservé à `feuille_temps.decide` : lignes détaillées, validation et retour pour correction avec motif obligatoire. La file est centrale, tous projets confondus, selon le contrôle existant ; aucun lien hiérarchique manager/employé n’est inventé.
- « Projets et affectations », réservé à `projet.read` : création d’un projet actif avec `projet.create`, création de tâches actives avec `tache.create`, consultation des tâches avec `tache.read`, affectation/retrait d’employés avec `projet.assign_employees`. Le sélecteur d’employés exige aussi `employe.read`. Le retrait d’une affectation est confirmé et conserve les lignes historiques. L’édition complète et l’archivage des projets/tâches ne sont pas proposés dans cette tranche.
- « Rapprochement des coûts », réservé à `paie.read` : dates de début/fin, heures validées, taux horaire chargé mensuel et coût par projet/employé/mois. Une ligne sans taux reste indisponible et conserve les heures non chiffrables ; lien vers les taux et la simulation de marge du module 6.
- Formulaires accessibles avec labels stables et erreurs associées, modales bloquées pendant l’envoi, prévention des doubles envois, états de chargement/erreur/vide et reprise. Les droits masquent les onglets et le backend reste l’autorité. Les ressources sont rechargées au retour sur un onglet pour refléter les nouvelles décisions.
- Le hook de lecture est partagé dans `shared/hooks/useApiResource.js` avec le module 6 : mêmes API/session et rejet des réponses tardives. Les tableaux shadcn défilent dans leur conteneur au clavier ; les formulaires passent sur une colonne sur mobile.
- Vérifications détaillées en fin de document. Aucun salaire, contrat, projet, affectation ni droit de la base active modifié par les essais : toutes les écritures de recette se font dans une base SQLite temporaire dédiée.

## Commandes

Depuis le dossier `frontend` : `npm run dev` démarre Vite et `npm run build` compile le frontend. En développement, Django et Vite doivent tourner en même temps.

## Permissions du profil module 2 — 2026-10-22

`FRONTEND_MODULE_2_CONGES_ABSENCES` est un profil gestionnaire de 9 permissions : CRUD des types et demandes, `solde_conge.read`. La vue globale des soldes utilise aussi `demande_absence.update`. Les droits `solde_conge.create`, `solde_conge.update` et `employe.read`, ajoutés pour l'ancien sélecteur individuel, ont été retirés de ce profil. Aucun compte n'a changé de rôle ; les droits cumulés des autres rôles restent inchangés.

## Correction des onglets conges - 2026-10-22

Demandes affiche la liste ; Planning utilise uniquement LeavePlanning. Le calendrier duplique avec variables non definies est supprime. Compilation et rendu serveur des deux onglets verifies avec `node check-leave-tabs.mjs` depuis frontend/. Clics reels dans le navigateur non verifies.

## Actions des demandes - 2026-10-22

Valider, Refuser et Supprimer restent dans la liste des demandes. Une confirmation modale integree remplace window.confirm pour les trois actions, avec blocage des doubles clics et erreurs API visibles. Le detail est en lecture seule. Les routes et permissions backend restent identiques. Compilation et rendu serveur des onglets verifies ; clics reels dans le navigateur restant a verifier.

## Planning des effectifs - 2026-10-22

Calendrier avec effectifs par jour et selection de date. Deux listes completes : presents prevus et absents, avec noms, departements, libelles et periodes des conges. Recherche par nom et filtre departement appliques aux comptes et listes. Chaque personne compte une seule fois, independamment du nombre de roles. Compilation et controles automatises verifies ; revue visuelle et clics navigateur restant a verifier.

## Droits annuels communs et codes automatiques — 2026-10-22

- Types : libellé, droit annuel, caractère payé et état actif. Le code est généré automatiquement à la création ; les codes existants sont conservés et ne sont plus saisissables.
- Soldes en consultation uniquement : chaque employé bénéficie du même droit annuel par type, sans exception individuelle ni formulaire d'attribution. Les droits sont affichés même avant toute demande. Pris et en attente restent calculés par l'API.
- Modifier le droit annuel d'un type aligne les soldes enregistrés et recalcule les disponibles. Les demandes sont conservées ; une baisse du droit peut rendre un disponible négatif.
- Rôle gestionnaire module 2 limité à 9 permissions. Migration 0031 d'alignement des anciens quotas appliquée dans la base de développement.
- 38 tests demandes/soldes, compilation et contrôles de rendu/permissions frontend réussis. Parcours interactifs navigateur et concurrence PostgreSQL restant à vérifier.
## Validation manuelle rapportée par l'utilisateur — 2026-10-23

- Affichage simplifié des congés : retrait des codes techniques de la liste des types et du sélecteur de demande ; le planning et la fiche de détail utilisent le libellé, avec « Congé » en remplacement s'il manque. Codes conservés côté backend. Compilation frontend vérifiée ; affichage navigateur à confirmer.

- Cases explicitement cochées : compte gestionnaire avec rôle module 2 ; absence de champ de saisie du code ; code généré après enregistrement ; modification du libellé sans erreur et sans changement de code.
- Réussite confirmée ensuite par l'utilisateur, avec un compte employé distinct du gestionnaire : droit de test remis à 10 jours, choix du type dans une nouvelle demande, refus des dates inversées, envoi valide et statut en attente, visibilité limitée à ses propres demandes, absence de Valider/Refuser, détail correct et en consultation uniquement.
- Les interactions navigateur des autres parcours du questionnaire restent ouvertes. Leurs règles API font l'objet des contrôles automatisés ci-dessous. Le module 2 n'est pas déclaré terminé ; les retours manuels sont fournis par l'utilisateur, pas observés directement par l'agent.

## Vérification automatisée élargie — 2026-10-23

- Validation manuelle supplémentaire : l'utilisateur confirme que les boutons fonctionnent et valide leur comportement. Le fonctionnement des boutons n'est donc plus en attente de confirmation utilisateur. Cette validation ne couvre pas explicitement l'affichage mobile ni la navigation clavier, qui restent à vérifier ; elle ne signifie pas que l'agent a piloté le navigateur.

- `manage.py test core --noinput` : 117 tests réussis sur une base SQLite de test isolée. Nouveau scénario avec connexions JWT employé/gestionnaire : droit commun de 10 jours, réservation de 2 jours, refus de décision sans permission, validation, soldes 2 pris/0 en attente/8 disponibles, planning absent sans présence simultanée, refus d'une autre demande et suppression d'une demande en attente avec contrôle 404.
- `npm run build`, `node check-leave-management.mjs`, `node check-leave-tabs.mjs` et `node check-planning.mjs` réussis. Rendu lecture/gestion, absence d'attribution individuelle, masquage du code technique, séparation des onglets et regroupement des personnes vérifiés.
- Aucun navigateur pilotable exposé lors de la nouvelle vérification. Ces contrôles ne valident ni les clics, ni la navigation clavier, ni le rendu mobile. Aucun changement des données de la base active.

## Intégration shadcn/ui — 2026-10-23

- Installation frontend de Tailwind v4/plugin Vite, CLI shadcn et dépendances des composants ; configuration JavaScript avec `components.json`, `jsconfig.json` et alias `@/` vers `src/`.
- Primitives partagées dans `shared/components/ui/`. Le fichier inutilisé `ui/button.jsx` et ses règles CSS spécifiques ont été supprimés ; son utilisation dans le module 3 a été retirée après retour utilisateur sur le rendu. Les boutons HTML reprennent les classes existantes `primary-button`, `outline-button` et `danger-button`, comme les modules 1 et 2. Aucun changement des permissions ou du backend.
- Thème `shared/styles/shadcn.css` avec variables `--ui-*` et utilitaires sans reset global Preflight. Les règles globales de bouton sont rétablies pour les boutons HTML. Adoption progressive des autres écrans restant à faire.
- Compilation et les quatre contrôles frontend réussis. Vérification visuelle dans le navigateur restant à réaliser.


## Validation du module 6 — 2026-10-25

- Compilation Vite et six scripts réussis : `check-tgm.mjs`, `check-payroll-mass.mjs`, `check-payroll.mjs`, `check-page-loading.mjs`, `check-departments.mjs`, `check-contracts-transfers.mjs`. Le nouveau module conserve un chargement séparé.
- Recette Edge avec API fictive : bureau 1440 px et mobile 390 px, filtres, erreurs de dates, résultats vides, refus sans permission sans appel API, tableaux défilables au clavier, détails projet au clavier et simulation sur CA saisi. Captures inspectées dans `output/tgm/desktop.png` et `mobile.png`. Aucun défaut JavaScript relevé.
- Correction de l’héritage `place-items: center` de la page de connexion sur les pages internes : `.hr-app-body` rétablit l’alignement normal. Le contenu TGM occupe la largeur disponible sur bureau, les tableaux défilent dans leur conteneur et les formulaires passent en colonne sur mobile. La largeur de la masse salariale a aussi été contrôlée dans le navigateur après cette correction.
- Parcours connecté aux API locales en lecture seule : les taux, coûts et simulation s’affichent sans erreur. Le backend est couvert par 77 tests PostgreSQL ciblés et 16 tests TGM/simulation SQLite isolés ; aucune donnée métier ni permission modifiée.
- Première version technique livrée. Les hypothèses de calendrier, les horaires historiques et le périmètre financier restent à valider par l’organisation. La recette finale du module 5 reste distincte et ouverte.

## Validation du module 7 — 2026-10-25

- Compilation Vite et sept contrôles frontend réussis : feuilles de temps, TGM, masse salariale, paie, chargement des pages, départements et contrats/virements.
- Recette Edge connectée à un véritable backend Django sur base SQLite temporaire : création du projet et de la tâche, affectation, saisie de 0,5 jour convertie en 3 h avec un contrat à six heures, enregistrement, soumission, verrouillage, refus avec motif obligatoire, correction, nouvelle soumission et validation. Rapprochement vérifié : 3 h × 2 000 FCFA/h = 6 000 FCFA. Modifier ensuite la feuille validée la retire du rapport de coûts ; un dépassement de 6 h est refusé.
- Vues employé/manager distinctes, coûts masqués pour l’employé ordinaire, formulaires et tableau vérifiés à 1440 px et 390 px, absence de débordement de page et défilement clavier du tableau. Captures inspectées dans `output/timesheets/employee-desktop.png`, `employee-mobile.png` et `rapprochement-desktop.png`. Aucun défaut JavaScript relevé.
- 87 tests backend ciblés réussis sur PostgreSQL de test et 10 tests module 7 sur SQLite isolé. API personnelles, projets et rapprochement consultés aussi sur PostgreSQL local en transaction explicitement en lecture seule. Les droits nécessaires existent déjà sur le compte ADMIN_RH de vérification ; aucun rôle ni compte modifié.
- Limites restantes : validation centrale selon permission, sans rattachement hiérarchique automatique ; aucune notification ; édition complète/archivage des projets et tâches hors de cette tranche. Les taux du module 6 restent estimés selon les contrats actuels. Les essais n’ont créé aucune donnée dans la base active.

## Accès employés simples et profils modules 6/7 — 2026-10-25

- Profils créés en base : `EMPLOYE_SIMPLE`, `FRONTEND_MODULE_6_TGM`, `FRONTEND_MODULE_7_FEUILLES_TEMPS`. Awa et Moussa possèdent uniquement le profil employé simple. Les profils des modules 1 à 5 sont conservés.
- Le rôle employé ouvre les congés personnels, les coordonnées bancaires personnelles et les feuilles de temps. L’annuaire RH est masqué sans `employe.read` ; le logo utilise une route d’accueil autorisée. Après connexion, un employé simple arrive sur les feuilles de temps. Les utilisateurs ayant `employe.read` gardent l’accueil annuaire ; les profils de paie/TGM suivent leurs droits.
- Les actions de validation, de gestion des projets, d’administration des rôles et les coûts globaux restent absents pour Awa et Moussa. Les sessions déjà ouvertes doivent être déconnectées puis reconnectées pour actualiser les droits.
- Compilation et quatre contrôles frontend (accueil/navigation, feuilles de temps, TGM, chargement commun) réussis. Parcours réel des deux comptes sur les API locales vérifié : temps, congés et banque ; aucun défaut JavaScript, aucune écriture métier. Tests backend : 36 PostgreSQL ciblés et 7 SQLite pour les profils.
- Pour tester les lignes de temps, les deux comptes doivent encore être affectés à un projet actif ayant des tâches actives. Détail des permissions et comptes : [profils de recette](output/permissions/roles-et-comptes-test.md).

## Projets et tâches : codes automatiques et actualisation — 2026-10-25

- Les formulaires « Nouveau projet » et « Nouvelle tâche » demandent uniquement le nom. Le code est généré par le backend ; aucun code n’est envoyé par React. Les identifiants et codes existants ne sont pas réécrits.
- Défaut reproduit en recette : un employé déjà connecté avant la création/affectation gardait l’ancienne liste de projets et tâches, ce qui bloquait la sélection et l’enregistrement de la feuille. Le chargement initial unique de `MyTimesheets` était insuffisant.
- Les options sont rechargées à chaque ouverture de la création/modification d’une feuille et lors du retour sur l’onglet ou la fenêtre. « Actualiser les projets et tâches » permet aussi une reprise dans le formulaire. Le brouillon conserve ses dates, choix, quantités et commentaires pendant l’actualisation ; les résultats périmés ne restent pas affichés sous un nouveau rechargement.
- Si le projet sélectionné n’a aucune tâche active, un message explique l’action attendue du responsable. L’espace de préparation rappelle que l’affectation au projet donne accès à toutes ses tâches actives.
- Vérifications : 100 tests backend PostgreSQL ciblés, 6 nouveaux tests SQLite, compilation et cinq scripts frontend réussis. Recette navigateur avec backend réel sur base isolée : employé ouvert avant affectation, nouveau projet sans code, tâche sans code, tâche ajoutée pendant une saisie, retour au premier onglet, actualisation manuelle sans perte du brouillon, enregistrement, soumission, refus/correction, validation et rapprochement. Captures des deux formulaires inspectées dans `output/timesheets/new-project-automatic-code.png` et `new-task-automatic-code.png`.
- Awa et Moussa : projets et tâches réellement sélectionnables sur leurs comptes locaux, contrôles de dates/affectations/horaires valides en lecture seule. Ils sont affectés à leur projet, dont les deux tâches sont actives ; leurs horaires sont de 8 h. Aucun projet, tâche, rôle, contrat ou temps de la base active modifié pendant la correction.

## Affectations visibles et suppression des tâches - 2026-10-26

- « Mes feuilles » affiche les projets et tâches personnels avant la liste des semaines. « Saisir mon temps sur… » ouvre un brouillon avec le projet présélectionné. Les affectations sont actualisées au retour dans la fenêtre ou par bouton.
- L'employé remplit sa propre feuille ; l'affectation au projet ne transfère pas la feuille d'un autre compte.
- Suppression d'une tâche avec confirmation et permission tache.delete. Migration 0045 : droit ajouté au profil gestionnaire du module 7. Une tâche utilisée par une feuille est conservée avec une erreur explicite.
- Vérifications : 25 tests PostgreSQL ciblés réussis ; parcours navigateur isolé à deux comptes (affectation, saisie, soumission, correction, validation, bureau/mobile/clavier). Awa et Moussa : sélection dans le navigateur vérifiée ; création HTTP 201 et soumission HTTP 200 sur leurs données réelles pour le 26 octobre, toutes les écritures de ce contrôle annulées par transaction.

## Retrait des tâches validées des affectations à saisir - 2026-10-26

- « Mes projets et tâches affectés » exclut les tâches présentes dans une feuille VALIDEE de l'employé connecté. Le projet disparaît lorsqu'il ne reste aucune tâche à saisir. Les validations des autres employés n'affectent pas sa liste.
- Les feuilles restent consultables dans « Mes feuilles de temps ». Si une feuille repasse en brouillon, les tâches correspondantes réapparaissent à l'actualisation. Les options complètes du formulaire sont conservées pour les saisies ultérieures et les corrections.
- Vérifications : 26 tests PostgreSQL ciblés réussis et build Vite réussi.

## Noms des projets et tâches - 2026-10-26

- Le module 7 affiche uniquement les noms des projets et tâches : listes, préparation, formulaire, détail des feuilles et rapprochement. Les codes techniques restent internes.

## Mon profil accessible depuis l'email - 2026-10-26

- L'email du compte dans la barre latérale ouvre « Mon profil » sur les pages authentifiées. Le lien devient actif après le chargement de la page.
- Formulaires personnels nom/prénom et changement de mot de passe (actuel, nouveau, confirmation). Les validations serveur protègent les champs de gestion et vérifient la robustesse du mot de passe. Le nom et les initiales affichés sont mis à jour après enregistrement.
- Le changement de mot de passe déconnecte la session locale et redirige vers la connexion avec un message explicite. Il est disponible dès la première connexion, sans imposer un changement obligatoire.
- Vérification : 229 tests PostgreSQL réussis, build Vite réussi ; recette navigateur sur base temporaire pour le profil.

## Bulletin archivé à la validation - 2026-10-26

La confirmation de validation annonce la génération et l'archivage automatiques du PDF. Le succès confirme que le bulletin est archivé et téléchargeable. La réponse de validation rend immédiatement disponible l'action de téléchargement. La génération manuelle reste proposée pour les anciennes paies sans fichier.

## Mes bulletins de paie - 2026-10-26

- Nouveau lien personnel permanent dans la navigation, sans permission de gestion RH : /mes-bulletins.
- Liste personnelle par période, filtre année, salaire brut/net et statut. Consultation de la fiche dans un lecteur PDF, ouverture dans un autre onglet ou téléchargement. Les paies historiques sans archive indiquent de contacter le gestionnaire.
- Les PDF sont récupérés avec authentification via apiRequest avant affichage dans une URL blob temporaire. Les URL sont révoquées à la fermeture du lecteur. Les états chargement, erreur et liste vide sont explicités.
- Build Vite réussi avec l'écran React des bulletins personnels. Vérifications API : 19 tests ciblés PostgreSQL réussis.
- Recette navigateur finale réussie sur base temporaire : navigation personnelle, filtre année, consultation PDF authentifiée, téléchargements depuis la liste et le lecteur, absence des paies d'un autre compte, affichage mobile sans débordement.

## Dossiers employés, filtres et historique - 2026-10-26

- La fiche de création/modification contient Poste occupé et Responsable hiérarchique. Le sélecteur exclut l'employé lui-même et les responsables inactifs, tout en gardant visible une valeur inactive déjà enregistrée.
- L'annuaire affiche poste, responsable et type(s) du contrat courant ; filtres par poste et contrat combinables avec recherche, département et statut. Des options Sans poste / Sans contrat en cours sont disponibles. Un filtre devenu invalide après une modification est réinitialisé.
- Bouton Historique par employé : dates, auteur, poste/contrat/responsable et valeurs avant/après. Les contrats supprimés restent dans l'historique ; les montants sont affichés seulement si contrat.read autorise leur lecture.
- La fermeture de la gestion des contrats recharge l'annuaire pour actualiser ses types et filtres. Les filtres passent sur plusieurs lignes en petit écran ; le tableau reste défilable horizontalement.
- Build Vite et recette navigateur réussis : filtres combinés, changement de poste/responsable, changement de salaire/type de contrat, historique comparatif et affichage mobile.

## Catalogue partagé des postes - 2026-10-26

- Bouton Postes dans Employés et Gérer les postes dans le dialogue des contrats. Catalogue avec création, consultation, modification et suppression selon les droits RH.
- Sélecteur Poste occupé dans la création/modification d'un contrat ; affichage du poste sur la carte de contrat. La création d'un poste depuis ce parcours recharge le catalogue sans effacer dates, salaire et horaires en cours de saisie.
- La fiche employé conserve le responsable hiérarchique mais ne propose plus de texte libre pour le poste : il provient des contrats courants.
- Les postes utilisés par un contrat sont conservés avec un message explicite en cas de tentative de suppression. Les profils RH/module 1 reçoivent les droits du catalogue ; les sessions déjà ouvertes doivent être reconnectées pour actualiser leur menu.
- Recette navigateur sur base temporaire : création, doublon refusé, modification, suppression libre/protégée, sélection contractuelle, ajout pendant la saisie sans perte de champs, historique, filtre et affichage mobile.
# Harmonisation de la navigation et du style — 26 octobre 2026

- Navigation partagée claire, icônes Lucide et groupes « Gestion RH » / « Mon espace », avec les permissions existantes.
- Suppression de la barre de contexte desktop redondante ; liens actifs avec `aria-current` et lien d'évitement vers le contenu.
- Menu plein écran jusqu'à 1100 px, profil sur l'email et déconnexion disponibles sur mobile, fermeture Échap, boucle de focus et contenu arrière inerte.
- Annuaire : métriques regroupées sans icônes décoratives, textes plus lisibles, tableau sans bandeau majuscule, identité fixe pendant le défilement horizontal, filtres repliables sur téléphone.
- Compilation Vite et parcours navigateur à 1440/768/390 px ; catalogue des postes et contrats revérifiés sur base temporaire.
- Captures et mesures comparatives : `.taste-skill/before/`, `.taste-skill/after/` ; choix visuels et limites détaillés dans `.taste-skill/report.md`.

