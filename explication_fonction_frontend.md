# Explication des fonctions frontend — Remonte RH

Ce document explique les écrans React et leur communication avec l’API. Les règles métier côté Django sont décrites dans [explication_fonction_backend.md](explication_fonction_backend.md).

## Organisation

### Configuration de l'éditeur — 2026-10-27

`frontend/jsconfig.json` décrit les sources JavaScript/JSX dans `src`, le JSX React et l'alias `@/*` vers `./src/*`. L'option `baseUrl` a été retirée : TypeScript 7.0.2 la refuse avec TS5102. Le chemin de l'alias est déjà relatif au fichier de configuration et reste valide sans cette option. Vite conserve son alias `@` vers le même dossier. Le contrôle `tsc --project jsconfig.json --noEmit` et la compilation Vite réussissent après correction ; la vérification exhaustive des types JavaScript n'est pas activée par ce changement.

### Navigation SPA — 2026-10-27

`app/main.jsx` monte une seule racine React avec `AppRouter`. Le routeur observe l'URL via `useSyncExternalStore` et `shared/lib/navigation.js`, qui centralise les destinations reconnues, `pushState`, `replaceState` et l'écoute de `popstate`. Aucune bibliothèque de routage supplémentaire n'est nécessaire pour les onze écrans actuels.

`AppLink` conserve de vrais liens accessibles avec leurs `href`. Un clic simple sur une destination interne appelle `navigate` ; les clics Ctrl/Cmd, les autres boutons de souris, les ouvertures dans un onglet, les téléchargements et les liens externes gardent leur comportement natif. Les routes sont sans extension : `/connexion`, `/employes`, `/departements`, `/roles`, `/conges`, `/coordonnees-bancaires`, `/paie`, `/mes-bulletins`, `/masse-salariale`, `/tgm` et `/feuilles-de-temps`. `routeKey` reconnaît les anciennes adresses pour les convertir vers la route actuelle avec `replaceState`, sans conserver de fichiers HTML par module. Les paramètres et fragments d'URL sont conservés. `/` ouvre `/connexion` ; une adresse inconnue affiche une page React « Page introuvable ».

`frontend/src/index.html` contient seulement le conteneur `root` et le chargement de `app/main.jsx`. Vite est configuré en SPA et ne déclare plus onze entrées de compilation. Le serveur de production doit servir `dist/index.html` pour les routes d'interface, conserver les assets et relayer `/api/` vers Django. Le README frontend fournit un exemple de configuration.

Le routeur protège les pages internes avec le jeton et un catalogue de permissions valide. `AppLayout` est monté au-dessus du contenu de route et reste présent pendant les changements de module ; les composants de page ne l'incluent plus. Les contrôles de permissions propres aux modules et les contrôles Django restent actifs. Les redirections des hooks/API, la connexion, la déconnexion et le changement de mot de passe utilisent `navigate`, avec remplacement de l'historique pour les redirections de session.

Chaque changement remonte le contenu du module, ferme ses dialogues par leur nettoyage habituel et réinitialise ses états locaux. Le cadre ferme le menu mobile et le profil. Le titre du document et le lien actif suivent la route ; une fois le composant chargé, le défilement revient en haut et le focus passe au titre. Le thème reste partagé. `Suspense` ne remplace que le contenu et une limite d'erreur offre une action de rechargement en cas d'échec. Les filtres et formulaires non enregistrés ne sont pas restaurés par précédent/suivant.

Validation : build Vite, cinq tests Node, parcours des dix modules à 1440 et 390 px sans rechargement du document, conservation du nœud de barre latérale, historique, accès directs et actualisations des dix adresses, connexion/déconnexion, droits du compte employé, ouverture dans un autre onglet et nettoyage des dialogues réussis sur base temporaire. Résultats dans `output/spa/verification.json`.

La recette vérifie également un lien activé par Entrée, la conservation du mode clair/nuit entre les routes et les redirections sans rechargement pour un renouvellement JWT expiré et une session contenant un catalogue de permissions invalide.

Après passage à l'entrée unique, la même recette réussit avec les dix routes sans extension : accès directs, actualisation, navigation sans rechargement et onze conversions d'anciennes adresses. La conservation des paramètres de connexion, l'ouverture de `/` et la page inconnue sont vérifiées. Le build contient uniquement `dist/index.html` comme fichier HTML ; `/connexion` est aussi disponible sur le serveur de développement actif.

### Présentation des titres — 2026-10-27

Les pages des congés, coordonnées bancaires, paies, masse salariale, TGM et feuilles de temps affichent leur titre sans la mention technique « MODULE » et son numéro. Cette simplification concerne seulement les entêtes visibles ; les routes, permissions et dossiers des modules sont conservés.

### Thème clair / nuit — 2026-10-27

`ThemeToggle` est le composant partagé de choix du thème. Le bouton natif expose `role="switch"`, `aria-checked` et le nom accessible « Mode nuit ». Une version complète est affichée au bas de la navigation et sur la connexion ; une version compacte est disponible en haut sur téléphone, ainsi que la version complète dans son menu. Il fonctionne au clavier.

`shared/lib/theme.js` utilise la clé `remonte-rh-theme` et deux valeurs, `dark` et `light`. Sans préférence valide, il choisit le mode nuit. `app/main.jsx` applique ce choix avant le montage des écrans. L'application du thème met à jour `data-theme`, la classe `dark` de la racine et la balise `theme-color`. Les composants utilisent `useSyncExternalStore` pour recevoir les changements, via un événement local et l'événement `storage` entre onglets. En cas de stockage bloqué, la préférence reste utilisable en mémoire pour la page courante. La suppression de session d'authentification ne retire pas cette préférence.

Les styles de disposition restent dans `styles.css`. Le fichier dédié `themes.css`, chargé après les styles existants et les variables shadcn, regroupe les couleurs des variantes sans modifier les données métier ou la disposition des modules. Il couvre aussi les dialogues natifs et les sélecteurs portalisés hors de l'arbre du layout. `color-scheme` adapte les contrôles de date, les listes natives et les barres de défilement. Les statuts gardent leurs indications positives, d'attente ou d'erreur sur des fonds sombres. Le lecteur peut présenter un PDF blanc, car le document généré n'est pas recoloré.

Recette : les dix modules ont été ouverts sur une base temporaire à 1440, 1024, 768 et 390 px, ainsi que huit parcours de formulaire/catalogue à 1440 et 390 px. Le script `check-theme.mjs` vérifie la bascule, la conservation au rechargement et à la navigation, la synchronisation entre onglets et entre boutons mobiles, les menus portalisés et le repli en cas de stockage bloqué. Captures et résultats dans `output/themes/`.

### Routage local de l'API — 2026-10-26

Le navigateur appelle `/api/` sur l'origine du frontend. `vite.config.js` relaie ce préfixe vers `REMONTE_RH_API_TARGET`, dont la valeur locale par défaut est `http://127.0.0.1:8001`, aussi bien en développement qu'en aperçu. Les variables sont lues depuis le dossier `frontend`, où se trouve `.env.example`. Ce routage remplace l'adresse 8000 précédemment calculée depuis le nom d'hôte, qui pouvait envoyer une connexion RH à un projet Laravel indépendant. Un déploiement statique doit configurer son propre relais `/api/`, ou fournir explicitement `VITE_API_BASE_URL` à la compilation pour une API sur un domaine distinct.

`login` conserve le message d'identifiants incorrects pour 400/401, donne une indication de configuration Django pour 404 et une indication de serveur indisponible pour les erreurs 5xx. Aucun détail de trace serveur n'est utilisé dans ces deux derniers messages. Les tests couvrent le chemin de connexion relatif, ces messages, le proxy réel et une connexion de bout en bout sur base temporaire.

### Champs, fenêtres et session — correctifs du 2026-10-26

`FormField` produit un conteneur avec un vrai `label` associé au contrôle par `htmlFor`/`id`, puis une erreur séparée avec son identifiant propre. Ses consommateurs transmettent les propriétés d'accessibilité au contrôle natif ou à leur composant de saisie. Le message d'erreur n'est donc plus ajouté au nom du champ, et les règles de style des libellés s'appliquent uniformément dans les modules.

`ModalDialog` conserve le dialogue natif et ajoute un bouton « Fermer la fenêtre » dans son entête, indépendant du chargement des données internes. Ce bouton et la fermeture par Échap respectent l'état `busy`. Son contenu reste défilable à l'intérieur de la fenêtre sur téléphone. `useBodyScrollLock` compte les fenêtres actives pour ne rétablir le défilement de la page qu'après la fermeture de la dernière ; `AppLayout` réutilise ce hook pour le menu mobile. Les styles corrigent les champs et légendes encore liés aux anciennes couleurs sombres et les espacements de boutons hérités des styles de connexion.

`getUser` retourne un objet vide pour un JSON invalide, `null`, un tableau ou une valeur primitive. `hasPermission` accepte uniquement un tableau de droits et cherche le code complet. Les gardes de page existantes restent responsables de la redirection lorsque le cliché de permissions est invalide ; le layout peut maintenant se rendre pendant ce contrôle sans lever d'exception.

Validation : tests Node dans `frontend/tests/session.test.mjs`, build Vite, recette navigateur multi-écran, profil, mot de passe, navigation et fenêtres imbriquées sur bases temporaires. Aucune modification des règles métier Django ni des droits des comptes réels.

### Chargement et appels API communs — 2026-10-23

`app/AppRouter.jsx` associe chaque clé de route à un import dynamique React.lazy. Les onze pages partagent le socle React, les styles, le layout et le helper API, puis chargent uniquement les composants du module demandé. `Suspense` utilise `PageLoading` dans le cadre partagé pour les routes internes ; la connexion affiche uniquement un message de chargement.

Dans `shared/lib/api.js`, `sendApiRequest` conserve l’authentification, les erreurs et les réponses binaires. `apiRequest` partage les promesses des GET par défaut strictement identiques et en cours, avec une clé composée du chemin et du jeton d’accès. Les entrées sont retirées à la fin, y compris en cas d’erreur ; aucun cache de résultat n’est ajouté. Les requêtes ayant des options explicites, dont les téléchargements, restent séparées. Les écritures retirent les lectures partageables au début et à la fin, pour que leur rechargement ne réutilise pas une réponse antérieure à la modification.

Le renouvellement du jeton est partagé entre les appels concurrents. Si un appel reçoit 401 après un renouvellement déjà achevé, il utilise le jeton actuel pour sa seconde tentative. Un échec de renouvellement conserve la suppression de session et la redirection. `RolesPage` charge les rôles et, si autorisé, le catalogue des permissions en parallèle ; l’API demeure l’autorité pour les droits.

Validation : douze scripts frontend, dont `check-page-loading.mjs` pour les lectures simultanées, rechargements frais, mutations, séparation des sessions, renouvellement concurrent/tardif et découpage de production ; compilation réussie. Script principal compilé réduit de 497,55 à 232,87 Ko. Le graphe des imports Vite est contrôlé via `tmp/measure_frontend_modules.mjs` et les API sont mesurées en lecture via `tmp/measure_page_loading.py`. Les tailles de scripts et les temps des API locales ne constituent pas une mesure complète du délai visuel dans VS Code ; ce chronométrage reste à effectuer. Aucun backend de production, calcul métier ou droit n’est modifié.

### Module 1 — Départements, mise à jour du 2026-10-27

`/departements` charge à la demande `DepartmentsPage` dans le module 1. `AppLayout` propose la navigation avec `departement.read`. La page vérifie la session et les permissions avant le chargement, affiche la liste et coordonne les dialogues de création, modification et suppression. `useDepartments` charge `/api/departements/`, ignore les réponses périmées et gère les états chargement, erreur et nouvelle tentative. Depuis le 27 octobre 2026, `DepartmentList` présente uniquement le nom du département, sans ligne de code technique ; ses actions suivent `departement.update/delete`.

`DepartmentEditor` saisit uniquement le nom (100 caractères maximum), obligatoire et unique selon l’API. Il envoie `{ nom }` par POST ou PUT via `useApiMutation` et le helper API centralisé. Django génère le code interne à la création et le conserve lors des modifications, y compris pour les départements existants. Le champ code n'est plus affiché ni envoyé par le formulaire. Les erreurs sont associées au champ, les actions sont bloquées pendant la requête et la liste est rechargée après réussite. La suppression nécessite une confirmation intégrée et `departement.delete` ; un échec reste affiché dans le dialogue. Les employés du département supprimé sont conservés sans affectation, tandis que les paies calculées conservent leur classification historique. Les listes de choix des autres écrans sont actualisées à leur prochain chargement.

Le profil `FRONTEND_MODULE_1_EMPLOYES_ACCES` possède désormais 22 droits, dont le CRUD département. `ADMIN_RH` reçoit également ces quatre droits ; le profil de masse salariale reste en lecture seule. Aucun rôle employé n’est modifié. Une reconnexion recharge les permissions de session.

Validation : rendu des permissions/navigation/formulaires et des erreurs accessibles, sept tests API CRUD/RBAC PostgreSQL et compilation réussis. Création avec le seul nom, code généré et masqué, puis renommage sans changement du code vérifiés dans le navigateur à 1440 et 390 px sur base temporaire.

### Module 5 — Masse salariale, mise à jour du 2026-10-24

`/masse-salariale` charge `modules/module-5/pages/PayrollMassPage.jsx`. La session et `paie.read` conditionnent la consultation. Le module 4 reste en attente de reprise et n’est pas considéré comme terminé.

`MassFilters` conserve les valeurs saisies jusqu’au clic « Afficher l’analyse ». Il refuse les mois invalides et une fin antérieure au début. Le filtre département utilise `/api/departements/` seulement avec `departement.read` ; sans ce droit, l’analyse globale reste consultable. La période initiale va de janvier au mois courant de l’année courante.

Présentation shadcn du 2026-10-23 : `Card`, `Table` et `Select` sont ajoutés via la CLI au répertoire partagé `shared/components/ui/`, selon `components.json`. `MassPanel` compose Card, CardHeader, CardTitle, CardDescription et CardContent pour les filtres, synthèses, exports et ventilations. `MassSelect` utilise le Select Radix de shadcn avec un label relié au déclencheur ; la valeur interne `all` est reconvertie en département vide avant l’appel API. Les mois restent des champs HTML et les boutons conservent le style du projet. Aucun composant Button shadcn n’est introduit.

`MassEvolution` et `MassBreakdown` utilisent les composants Table de shadcn. L’adaptation locale `containerProps` permet d’associer un nom accessible et un arrêt clavier à la zone de défilement, sans créer deux conteneurs imbriqués. Les tableaux possèdent une légende, des en-têtes de colonnes et de lignes ; les montants restent ceux du serveur. Le conteneur `mass-workspace` utilise des requêtes de conteneur CSS pour adapter les colonnes à l’espace disponible, avec des styles limités au module et aux menus de sélection portés dans le portail Radix.

`usePayrollMass` charge une seule synthèse contenant les totaux, les ventilations et les deux évolutions déjà agrégées par le backend. Il sélectionne les lignes mensuelles ou annuelles selon les filtres sans refaire les calculs dans React. Il présente les erreurs et ignore les réponses après changement de filtres ou démontage. Les anciens résultats sont masqués pendant un nouveau chargement pour éviter de les associer à une autre période. Les départements sont chargés indépendamment. L’écran permet une nouvelle tentative et signale explicitement l’absence de paies finalisées.

`MassTotals` affiche les totaux du serveur en XOF : les paies VALIDEE et PAYE forment deux groupes exclusifs. `MassEvolution` compose trois `MassComparisonChart` : salaires nets, coût employeur et cotisations. Chaque graphique compare les séries validées/payées et possède une échelle graduée propre, des libellés et un tableau détaillé accessible. Les périodes sans paie ne sont pas ajoutées. `massMetrics.js` centralise les indicateurs affichés dans l’évolution et les ventilations. `MassBreakdown` expose le brut, le net, les cotisations et le coût employeur pour chaque statut, par département ou type de contrat. La note sur les types multiples est conservée : ces lignes ne sont pas additives.

`useMassExport` utilise `massExportPath` pour transmettre la période, le département et `granularite=mensuelle|annuelle` appliqués au téléchargement CSV, XLSX ou PDF. La section d’évolution du fichier suit le choix affiché ; son nom inclut aussi la granularité. Le helper partagé `downloadApiFile` accepte un type MIME attendu, conserve PDF par défaut pour les modules existants, utilise le JWT et son renouvellement et refuse un format inattendu. Les boutons utilisent le HTML et le CSS du projet.

Le rôle `FRONTEND_MODULE_5_MASSE_SALARIALE` dispose uniquement de `paie.read` et `departement.read`. Ces droits ne sont pas attribués automatiquement aux employés. Dans le backend actuel, `paie.read` autorise également la consultation globale des paies du module 4 ; ce rôle n’est donc pas un accès réservé à des chiffres anonymisés. Les calculs, classifications historiques et exports restent dans les services et repositories backend existants.

Contrôles automatisés : rendu des permissions, validation des filtres, séparation validé/payé, évolution annuelle et vide, téléchargements des trois formats, erreurs et authentification ; compilation Vite.

Vérifications du 2026-10-24 : trois graphiques en modes mensuel/annuel, valeurs brutes et cotisations dans les deux ventilations, cas entièrement nul sans NaN, granularité des six téléchargements et non-régressions des autres modules. Douze scripts frontend et compilation réussis ; 61 tests backend ciblés SQLite et 9 tests module 5 PostgreSQL réussis. Les exports de la base locale sont contrôlés en lecture seule dans les deux granularités ; les PDF de recette mensuel et annuel ont été rendus et inspectés. Le parcours navigateur des nouveaux graphiques/tableaux, le clavier et le mobile restent à vérifier. Aucun montant ni droit modifié.

Contrôle interactif dans l’aperçu VS Code du 2026-10-23 : consultation du tableau global et des ventilations, sélection puis application de Direction RH, passage à l’évolution annuelle et affichage des groupes validé/payé vérifiés. Les trois exports ont été téléchargés par leurs boutons et sauvegardés dans `tmp/masse-validation-vscode-20261023.csv`, `.xlsx` et `.pdf` ; leurs structures ont été contrôlées (quatre sections CSV, quatre feuilles Excel, PDF complet). Après intégration shadcn, l’ouverture et la sélection dans les deux menus, l’application des filtres, les cartes de synthèse et les zones de défilement internes des tableaux ont été vérifiées. La présentation antérieure qui débordait est remplacée ; les largeurs et espacements restent à contrôler sur plusieurs dimensions d’aperçu. Les parcours mobile et clavier complet, les dates inversées, le périmètre vide et les permissions partielles n’ont pas été vérifiés par clic pendant cette session. Aucun changement de données métier.

### Module 4 — Gestion des paies, étape 1 du 2026-10-23

Contrôle interactif complémentaire du 2026-10-23 : l’aperçu navigateur de VS Code est désormais accessible. Les trois onglets, les filtres Généré/Payée, la remise à zéro du filtre des paies, la fiche d’ordre en lecture seule, l’ouverture des formulaires, le chargement du contrat après choix d’un salarié et l’ajout d’une tranche IUTS ont été vérifiés. Les formulaires ont été fermés sans enregistrer. Un bulletin existant a été téléchargé et sauvegardé dans `tmp/bulletin-validation-vscode-20261023.pdf` ; sa signature PDF, son marqueur de fin et sa taille de 3 142 octets ont été contrôlés. Aucun test de mutation métier ni parcours clavier/mobile complet n’a été effectué.

Sur l’ordre #9, le formulaire bancaire charge le bénéficiaire et le net, mais indique l’absence de RIB UEMOA complet et désactive la génération. L’ouverture du formulaire est validée ; la génération effective du document sur ces données ne l’est pas. Les mentions de navigateur indisponible dans les contrôles ci-dessous correspondent aux vérifications antérieures à cette session.

L'entrée `/paie` charge `modules/module-4/pages/PayrollPage.jsx`. La session est vérifiée avant le chargement et la navigation nécessite `paie.read` ou `ordre_virement.read`, avec affichage des onglets selon les droits. L'écran affiche les paies de tous les employés autorisées par cette permission de gestion ; il ne s'agit pas d'un espace personnel de bulletins.

`usePayrollData` charge les paies, puis les employés et profils seulement selon les droits utiles à l'écran. Les chargements sont indépendants : une erreur sur le sélecteur d'employés ne masque pas la liste des paies. Un compteur protège contre les réponses tardives et le démontage du composant. Les filtres sont locaux à la liste.

`PayrollEditor` crée ou modifie un brouillon avec l'employé, la période et le libellé. La création nécessite `paie.create` et la lecture des employés pour le sélecteur. Les montants et statuts sont produits par le backend. `PayrollList` propose les actions permises selon le statut : modifier/calculer/supprimer le brouillon, valider une paie calculée, annuler une paie non payée avec motif, générer un bulletin après validation et télécharger un bulletin disponible. Les règles métier restent vérifiées par l'API.

`PayrollAction` utilise un dialogue intégré pour confirmer les mutations et saisir le profil, les charges familiales ou le motif selon l'action. `usePayrollActions` réutilise `useApiMutation` pour les écritures et centralise notifications et téléchargement. Le verrou de mutation empêche les doubles clics ; le dialogue reste ouvert avec les erreurs en cas d'échec. `PayrollDetail` recharge le détail et propose uniquement sa consultation et sa fermeture, avec nouvelle tentative en cas d'erreur. L'identité, les montants, l'historique des dates, les retenues, les absences, les éléments inclus et les hypothèses du calcul sont présentés sans afficher de JSON brut.

Le téléchargement utilise `downloadApiFile` dans `shared/lib/api.js`. `apiRequest` conserve l'authentification et le renouvellement JWT pour les réponses binaires, puis crée un téléchargement local via une URL temporaire. Les erreurs HTTP restent traitées comme erreurs et ne deviennent pas des fichiers PDF.

Le rôle gestionnaire `FRONTEND_MODULE_4_PAIE_VIREMENTS` contient dix droits : CRUD paie, CRUD des ordres, génération/téléchargement du document bancaire et lecture des employés. Il n'est attribué automatiquement à aucun compte. Les permissions des rôles continuent à se cumuler. Les profils de règles sont désormais gérés dans l’onglet dédié. Les ordres de virement sont désormais gérés dans leur onglet. Les éléments variables restent une prochaine étape. Compilation et contrôles automatisés réussis ; validation visuelle, clavier et mobile non effectuées faute de navigateur accessible.

### Règles et téléchargement de paie — 2026-10-23

`PayrollRuleManager` constitue l’onglet « Règles de paie ». `PayrollRuleEditor` utilise des champs identifiés pour le profil, ses dates, sa référence, les heures, le plafond CNSS et les taux ; `RuleSchedules` gère les lignes IUTS et les réductions. `rules.js` prépare les données : les pourcentages affichés deviennent des ratios à six décimales pour l’API, le dernier plafond vide devient null, les montants restent des chaînes décimales. Aucun taux légal n’est prérempli. Les contrôles définitifs restent côté backend.

Les créations suivent paie.create ; les modifications et validations suivent paie.update ; la suppression suit paie.delete. Les profils validés sont figés et peuvent être copiés vers un nouveau code. Le formulaire propose une validation distincte après l’enregistrement. Les profils actifs mais non validés ne sont pas proposés au calcul. Aucun champ de mode fictif n’existe dans le formulaire ni les nouveaux payloads.

`downloadApiFile` envoie désormais Accept: */* : DRF effectue sa négociation avant de retourner le FileResponse, et refusait le précédent Accept: application/pdf avec HTTP 406. Le Blob reçu doit être un PDF. Le serveur continue de vérifier le propriétaire ou paie.read. `bulletin_generable`, exposé en lecture seule par l’API, évite de proposer une génération quand le statut, la date de calcul ou les totaux historiques manquent. Les anciens calculs ne sont ni réinventés ni recalculés pour produire un document.

Tests de rendu, conversions, permissions, immutabilité et téléchargement authentifié réussis ; compilation et contrôles des autres modules réussis. La validation visuelle dans un navigateur reste indisponible.

### Contrats du module 1 et ordres du module 4 — 2026-10-23

Dans l’annuaire, le bouton « Contrats » ouvre EmployeeContracts pour l’employé de la ligne. useEmployeeContracts charge /api/contrats/?employe=<id> et les types uniquement avec type_contrat.read. Les réponses tardives sont ignorées. ContractEditor fixe l’employé et saisit dates, base mensuelle XOF, heures par jour, statut et types multiples. Le salaire reste une chaîne décimale dans le payload. Les mutations réutilisent useApiMutation, les erreurs sont reliées aux champs et la suppression exige une confirmation intégrée. L’historique de paie ne se recalcule pas lors d’une modification de contrat.

PayrollPage propose les onglets selon paie.read et ordre_virement.read. usePayrollData charge les ordres indépendamment des paies. TransferOrders orchestre la liste, les filtres et les dialogues. TransferEditor choisit une paie validée sans ordre actif pour le même employé/période ; la date de génération est attribuée à la création côté serveur. Le détail TransferDetail est en lecture seule. TransferDecision gère confirmations, motif requis pour rejet/annulation et association d’un ordre traité à sa paie validée. Les droits et statuts contrôlent les boutons ; l’API vérifie à nouveau chaque opération.

transfers.js centralise l’éligibilité et l’association de l’ordre à la paie. Les ordres rejetés/annulés permettent une nouvelle tentative. Le net affiché provient de la paie, sans saisie d’un montant bancaire indépendant. Une association PAYE exige paie.update, un ordre traité/daté correspondant et non déjà utilisé. Le statut traité représente un suivi interne ; aucun fichier n’est transmis à une banque.

ModalDialog est partagé par les modules 1 et 4, sans dépendance du module 1 au module 4. Boutons HTML et CSS existants conservés. Les profils gestionnaires comprennent désormais 22 droits pour le module 1, CRUD départements inclus, et 10 pour le module 4, sans nouvelle attribution à un employé. Après changement de droits, une reconnexion actualise la session frontend.

Compilation et sept contrôles frontend réussis, dont check-contracts-transfers.mjs (formulaires, accès partiels, états, éligibilité et détails en lecture seule). Les tests API vérifient également les refus de droits et les transitions. Le parcours navigateur réel reste non vérifié.

### Types de contrat et contexte de paie — 2026-10-23

ContractTypeManager réutilise ModalDialog et useApiMutation pour gérer les types. ContractTypeEditor saisit le libellé et la description ; ContractTypeList limite Modifier/Supprimer aux droits correspondants. useContractTypes gère chargement, erreur, réponse tardive et session expirée. Le gestionnaire est accessible depuis l’annuaire et depuis EmployeeContracts. Une mutation depuis ce dernier recharge ses types tout en conservant la saisie du contrat. Le backend refuse la suppression d’un type lié à un contrat.

PayrollContractPreview est intégré à PayrollEditor et à PayrollAction pour le calcul. usePayrollContract appelle GET /api/paiements/contexte-contrat/?employe=<id>&periode=AAAA-MM à chaque changement d’employé ou de période. Il efface l’ancien aperçu et ignore les réponses qui ne correspondent plus au choix courant. Les états choix incomplet, chargement, erreur avec nouvelle tentative, contrat absent et contrats multiples sont explicites.

PayrollContractInformation présente les types, salaire mensuel contractuel, heures journalières, statut et dates en lecture seule. Le salaire affiché est la base du contrat ; le salaire de base proratisé, le brut et le net restent calculés par le serveur. L’aperçu utilise la même sélection de contrats et les mêmes bornes mensuelles que le moteur. Un brouillon peut être enregistré avant correction d’un contrat manquant, mais le calcul reste refusé tant que le contexte est invalide.

Le contexte est autorisé par paie.read sans attribuer le CRUD contrat au module 4. Le module 1 reçoit les droits de gestion des types (19 droits après migration 0039, puis 22 avec le CRUD départements de la migration 0043) ; le module 4 compte désormais 10 droits avec la génération du document bancaire. Compilation et contrôles automatisés réussis, dont check-contract-types-context.mjs ; rendu visuel et interactions dans le navigateur non validés.

### Visibilité des actions sur les ordres — 2026-10-23

TransferOrders affiche « Créer un ordre de virement » avec ordre_virement.create et la consultation des paies disponible pour le sélecteur. TransferList utilise les libellés explicites « Modifier l’ordre » et « Supprimer l’ordre ». Ces actions sont proposées seulement pour GENERE, avec les droits correspondants ; la modification nécessite aussi paie.read. Pour un ordre traité, rejeté ou annulé, une explication visible remplace l’absence inexpliquée de boutons. Les contrôles backend et les confirmations restent identiques. Le contrôle de rendu couvre les boutons présents pour un ordre généré et absents avec justification pour un ordre traité. Compilation vérifiée ; navigation visuelle non validée.

### Document de virement Burkina Faso — 2026-10-23

TransferDocumentDialog prépare le document depuis un ordre GENERE. useTransferDocumentContext charge le bénéficiaire, le montant net validé et ses comptes masqués depuis le backend. Le gestionnaire renseigne l’entreprise, le compte à débiter, l’agence, les instructions, le lieu et le signataire. Ces données ne sont pas stockées dans localStorage. Le montant et le nom du bénéficiaire ne sont pas des champs éditables.

Le bouton génère le PDF, recharge la liste et déclenche son téléchargement via le helper API authentifié existant (Accept: */* et renouvellement JWT). En cas d’échec de téléchargement après archivage, un bouton permet de le retenter sans refaire le document. useTransferDocumentDownload bloque les doubles demandes. Les comptes invalides ou absents sont signalés et la génération est bloquée jusqu’à renseignement du RIB dans le module bancaire.

transfers.js propose la génération seulement avant archivage, puis le téléchargement avec le droit spécial et les lectures des ordres/paies. Un document archivé fige les instructions : modification/suppression retirées de la liste, annulation possible avec motif. Les détails restent en consultation seule. Le PDF se signe manuellement et se remet à la banque ; sa génération ne change ni le statut de traitement ni celui de paiement.

Le modèle est un document Remonte RH paramétrable inspiré des rubriques du formulaire BDU-BF cité dans les sources backend. Il n’utilise aucun logo bancaire et ne constitue pas un formulaire approuvé par toutes les banques. La banque destinataire peut demander son propre support. Le PDF A4 a été rendu et contrôlé visuellement ; les interactions navigateur restent non vérifiées.

### Module 3 — Coordonnées bancaires

`EmployeeRecordsPage` n'affiche et ne charge plus que les coordonnées bancaires et, pour un gestionnaire autorisé, la liste des employés. Aucun onglet ni appel de documents/types de document ne subsiste dans cette page. `resources.js` décrit uniquement la ressource bancaire ; `RecordSummary` présente la banque, le propriétaire, les quatre derniers caractères de l'IBAN et la date de modification.

`RecordManager` conserve les boutons HTML, les permissions CRUD, le formulaire et la confirmation de suppression. Les libellés sont Banque, IBAN, BIC et SWIFT. Le compte d'un employé ne peut pas être réaffecté à la modification. Les permissions des rôles se cumulent ; l'accès aux dossiers tiers requiert toujours coordonnees_bancaires.manage et la sélection d'un employé requiert employe.read.

Le profil module 3 a perdu ses permissions documentaires ; ses droits bancaires existants sont conservés. Les API documentaires et leurs données restent disponibles côté backend. Depuis le 2026-10-23, IBAN, BIC et SWIFT sont chiffrés au stockage. EmployeeRecordsPage retire l'ancien avertissement ; le formulaire, les permissions et le masquage des cartes restent identiques. Le déchiffrement est effectué par le backend pour les requêtes autorisées.

### Gestion des congés et des jours acquis — 2026-10-22

`LeaveTypeManager` permet de créer, modifier et désactiver un type, ou supprimer un type inutilisé après confirmation intégrée. L'administrateur renseigne le libellé, le droit annuel, le caractère payé et l'état actif. Le code est généré par le backend à la création et ne peut pas être modifié. Les codes existants sont conservés. Les boutons suivent `conge.create/update/delete` ; la lecture nécessite `conge.read`. Le droit annuel est commun à tous les employés : modifier ce droit recalcule les soldes, sans modifier leurs demandes.

`LeaveBalanceManager` est un écran de consultation uniquement. Il affiche identité, matricule, type, année, droit annuel commun, jours pris, en attente et disponibles. Aucun formulaire d'attribution ou de modification individuelle n'est proposé. Les droits apparaissent automatiquement, même sans demande préalable. L'API limite un employé à ses propres soldes ; la consultation de tous les employés nécessite `demande_absence.update` en plus de `solde_conge.read`.

`useLeaveMutation` centralise les écritures des types via `apiRequest`, les erreurs et le blocage des doubles envois ; `LeaveField` relie les erreurs aux champs. Les listes sont actualisées après succès. Le Repository Pattern backend est conservé. Le profil module 2 dispose de 9 permissions : CRUD des types et demandes, lecture des soldes. Les droits d'écriture individuelle et la lecture des employés précédemment nécessaires au sélecteur ont été retirés de ce profil.

### Fiche d'une demande d'absence

Depuis le 27 octobre 2026, les cartes de l'onglet Demandes utilisent `employe_prenom` et `employe_nom` renvoyés par la liste API pour afficher le nom complet en gras. Le motif est placé sur une ligne distincte. Une identité absente affiche « Nom non renseigné », sans identifiant technique. Le frontend ne charge pas l'annuaire des employés pour construire ces libellés et n'exige pas `employe.read`.

Validation : build Vite et parcours liste/détail dans le navigateur à 1440 et 390 px sur base temporaire réussis, sans erreur JavaScript ni débordement horizontal.

Dans l'onglet Demandes, « Voir le détail » ouvre `modules/module-2/components/LeaveRequestDetail.jsx` pour l'identifiant sélectionné. Son hook charge le détail avec `apiRequest` et ignore les réponses après fermeture. Le contenu présente les informations de l'employé, les dates, le motif, le statut et l'identité/date de décision. Le dialogue gère le focus et Échap, les erreurs disposent de « Réessayer ». Aucun droit de validation n'est ajouté par cette fiche : l'API conserve les contrôles existants de lecture personnelle ou transversale.

- `frontend/src/app/main.jsx` démarre React ; `app/AppRouter.jsx` choisit l'écran et assure la navigation SPA selon l'URL.
- `frontend/src/modules/module-1/pages/` contient les composants React de connexion, d’annuaire et de gestion des rôles.
- `frontend/src/index.html` est l'unique entrée navigateur ; les pages d'interface sont des composants JSX sélectionnés par le routeur.
- `frontend/src/shared/components/AppLayout.jsx` contient la navigation et le cadre communs aux pages internes.
- `frontend/src/shared/lib/api.js` centralise la connexion, les requêtes, les jetons JWT et leur renouvellement.
- `frontend/src/shared/styles/styles.css` contient les styles communs.

## Démarrage d’une page

Chaque fichier HTML d’entrée contient `#root` et importe `../app/main.jsx`. `createRoot` monte l’application React dans cet élément. `main.jsx` examine l’adresse et affiche `LoginPage`, `EmployeesPage` ou `RolesPage`.

Dans un fichier `.jsx`, **JSX** décrit le contenu de l’écran. `useState` mémorise les valeurs qui changent et déclenche un nouveau rendu; `useEffect` exécute les opérations liées à l’affichage, par exemple le chargement initial; `useRef` conserve une référence DOM sans déclencher de rendu. Les props transmettent des données entre composants. Les gestionnaires `onClick`, `onChange` et `onSubmit` répondent aux actions utilisateur.

## Connexion et session

`modules/module-1/pages/LoginPage.jsx` affiche le formulaire de connexion. À la soumission, `shared/lib/api.js` envoie l’email et le mot de passe à `POST /api/auth/login/`. Les jetons `access` et `refresh` et les informations utilisateur sont stockés dans `localStorage`, puis l’utilisateur est redirigé vers l’annuaire.

Les requêtes authentifiées incluent `Authorization: Bearer <jeton>`. Si le jeton d’accès a expiré, `api.js` tente `/api/auth/refresh/`; si le renouvellement échoue, la session est effacée et l’utilisateur revient à la connexion.

En développement, Vite sert le frontend sur le port 5173 et Django l’API sur le port 8000. Django autorise l’origine Vite via CORS; les deux serveurs doivent fonctionner simultanément.

## Module 1 — Annuaire des employés

`modules/module-1/pages/EmployeesPage.jsx` charge les employés depuis `GET /api/employes/`, ainsi que les départements et rôles autorisés. Il affiche les actions selon les permissions de l’utilisateur.

- La recherche locale porte sur le nom, le prénom, l’email et le matricule; les filtres locaux portent sur le département et le statut.
- Le formulaire contrôlé par l’état React crée un employé via `POST /api/employes/` et modifie un employé via `PUT /api/employes/{id}/`.
- Les erreurs de validation Django s’affichent sous le champ concerné et disparaissent lorsque le champ est corrigé.
- Les identifiants de département et de rôle sont comparés comme des nombres pour afficher correctement leurs noms.
- La suppression appelle `DELETE /api/employes/{id}/` après confirmation.
- Le bouton de suppression dépend de `employe.delete`. La confirmation précise que le backend supprime également les données liées à l’employé ; le bouton est désactivé pendant la requête pour éviter les doubles envois. En cas de réponse API négative, le détail de l’erreur est affiché. Si le droit vient d’être accordé, une déconnexion/reconnexion actualise le snapshot de permissions utilisé pour afficher le bouton.
- Les rôles sont présentés avec une case à cocher chacun. L’état `form.roles` contient les identifiants numériques sélectionnés; le compteur se recalcule à chaque changement et le payload les transmet à l’API.
- Le formulaire s’ouvre avec défilement et focus automatiques. Les champs sont désactivés durant l’enregistrement pour éviter une soumission répétée.

Les filtres poste/contrat et les champs poste/responsable ne sont pas disponibles dans le contrat actuel de l’API.

## Module 1 — Rôles et accès

`modules/module-1/pages/RolesPage.jsx` utilise `shared/components/AppLayout.jsx`.

- `role.read` autorise l’affichage de la liste via `GET /api/roles/`.
- `permission.read` permet de charger les permissions via `GET /api/permissions/`.
- `role.create` affiche le formulaire et autorise l’envoi de `nom`, `description` et des identifiants sélectionnés à `POST /api/roles/`.
- `role.update` affiche « Modifier » pour chaque rôle. Le formulaire partagé `modules/module-1/components/RoleForm.jsx` préremplit les données et envoie `PUT /api/roles/{id}/`. Si l’utilisateur n’a pas `permission.read`, il peut modifier le nom et la description ; le payload omet les permissions pour que l’API conserve les attributions existantes.
- L’affichage des actions s’appuie sur la liste de permissions stockée dans la session au login. Après un changement de rôles en base, il faut se déconnecter puis se reconnecter pour recharger cette liste. Si `role.update` manque, la page explique ce droit requis et cette reconnexion.
- `role.delete` affiche « Supprimer ». Après confirmation explicite, React envoie `DELETE /api/roles/{id}/`; le message prévient que le rôle sera retiré des comptes qui le portent. Le backend reste responsable du contrôle d’accès et de l’exécution.
- Si `role.update` ou `role.delete` n’est pas dans la session courante, les actions correspondantes sont masquées et la page indique les permissions requises ainsi que la reconnexion à effectuer après une attribution récente. L’API applique le même contrôle côté serveur.
- Les erreurs de validation des champs nom, description et permissions sont associées au formulaire. Les retours de succès ou d’échec de lecture, création, modification et suppression sont annoncés avec une zone accessible.
- L’interface affiche le nombre de permissions de chaque rôle, et leurs noms lorsque l’utilisateur peut lire les permissions.

Dans la base PostgreSQL de développement, deux profils ont été créés comme modèles d’accès aux interfaces actuelles :

- `FRONTEND_MODULE_1_EMPLOYES_ACCES` : `employe.read/create/update/delete`, `employe.assign_roles`, `departement.read`, `role.read/create/update/delete` et `permission.read`.
- `FRONTEND_MODULE_2_CONGES_ABSENCES` : `demande_absence.read/create/update/delete`, `solde_conge.read` et `conge.read`.

Ces rôles ne sont attribués à aucun compte. Ils ne donnent pas les permissions d’administration des types ou soldes, car ces écrans ne les proposent pas encore.

L’API Django applique elle-même les permissions; le masquage des actions dans React ne remplace pas le contrôle backend. Les essais d’écriture réels restent à faire avec des comptes jetables dédiés.

## Module 2 — Congés et absences

`modules/module-2/pages/LeavePage.jsx` fournit une première interface pour les demandes, le planning, les soldes et les types de congé. L’entrée Vite `/conges` sélectionne cette page React. `AppLayout` affiche le lien si le compte peut consulter au moins une section du module.

- `demande_absence.read` charge les demandes avec `GET /api/demandes-absence/` et le planning mensuel avec `GET /api/planning/?date_debut=...&date_fin=...`. Le backend renvoie uniquement les demandes de la personne, sauf pour un profil ayant aussi `demande_absence.update`.
- `demande_absence.create` affiche le formulaire et envoie `type_conge`, `date_debut`, `date_fin` et `motif` à `POST /api/demandes-absence/`. Le backend associe le dossier à la personne connectée.
- Si le backend refuse les données (par exemple dépassement du quota), le formulaire associe les erreurs `type_conge`, `date_debut`, `date_fin` et `motif` au champ correspondant, le marque invalide et place le focus sur la première erreur. Une notification générale accessible indique si la demande a été envoyée ou si une correction est nécessaire.
- `demande_absence.update` affiche les actions de décision qui appellent `POST /api/demandes-absence/{id}/valider/` ou `/refuser/`. Une demande en attente peut être supprimée via `DELETE /api/demandes-absence/{id}/` selon le contrôle objet du backend.
- Les décisions, suppressions et actualisations affichent un message accessible de réussite ou d'erreur près du haut de la page.
- `solde_conge.read` charge les soldes via `GET /api/soldes-conge/?annee=...`; `conge.read` charge les types via `GET /api/conges/types/`.
- Chaque carte de solde montre `disponible`, `en_attente`, `pris` et `acquis`. `disponible` tient compte des demandes en attente ; `restant` reste disponible dans la réponse pour compatibilité, mais n'est pas le chiffre à utiliser pour montrer ce que l'employé peut encore demander.
- Le planning charge `GET /api/planning/` pour le mois affiché. Les boutons précédent/suivant changent le mois et rechargent ses dates ; un identifiant de requête empêche une ancienne réponse réseau de remplacer les événements du mois courant si l’utilisateur change rapidement de période.
- Les événements sont indexés par date sur le mois visible avant le rendu. Une absence couvre chaque date inclusive de sa période ; une présence prévue est affichée sur son seul jour. Les étiquettes précisent « Absence » ou « Présence prévue », le code du congé si disponible et le nom complet de l’employé. Les événements supplémentaires sont signalés au-delà de trois dans une journée.
- Si la requête du planning échoue, la grille n’est pas présentée comme vide : la section affiche l’erreur et un bouton « Réessayer ». Cette dernière opération recharge les données du module. Cette erreur est aussi annoncée dans la zone de notification en haut de page.
- `PRESENCE_PREVUE` reste une prévision sur les jours ouvrés, pas une preuve de pointage ou de présence réelle. Les jours fériés et les horaires particuliers ne sont pas calculés.

La première version permet la consultation des soldes et types; leur administration, les filtres transversaux du planning et un parcours navigateur avec un compte de test restent à faire.

### État des vérifications

`manage.py check` et la compilation Vite passent, et les routes nécessaires sont présentes. La base active contient déjà des comptes et le compte de démonstration du dépôt n’y est pas installé; aucun essai CRUD ni aucune écriture n’a donc été réalisé. La validation nécessite un compte jetable de test avec permissions partielles. Le navigateur intégré n’était pas disponible dans cette session, donc les écrans n’ont pas pu être vérifiés visuellement.

## État frontend des modules

| Module | État | Interfaces prévues ou présentes |
| --- | --- | --- |
| 1 — Employés et accès | En cours | Connexion, annuaire, rôles et contrats par employé. |
| 2 — Congés et absences | En cours | Demandes, décisions, planning mensuel, consultation des soldes et types. |
| 3 — Coordonnées bancaires | Implémenté, revue visuelle restante | CRUD bancaire, permissions et stockage chiffré. |
| 4 — Paie et virements | En cours | Préparation, règles, calcul, validation, bulletins et suivi des ordres ; formulaires des variables restants. |
| 5 — Masse salariale | Développement fonctionnel terminé ; recette visuelle à clôturer | Synthèses, évolutions, ventilations et exports validés par les contrôles automatisés ; recette complète mobile et clavier restante. |
| 6 — TGM | Première version implémentée le 2026-10-25 | Taux journaliers/horaires, coûts projets par tâche et employé, simulation temporaire de marge avec chiffre d’affaires saisi. |
| 7 — Feuilles de temps | Première version fonctionnelle du 2026-10-25 | Saisie heures/jours, soumission, décision avec correction, projets/affectations et rapprochement avec le TGM. |
# Revue clean code — 2026-10-22

Le planning du module 2 est isolé dans `frontend/src/modules/module-2/components/LeavePlanning.jsx`. La page conserve le chargement API, les permissions et les actions ; le composant gère le rendu du calendrier. Les utilitaires de dates sont dans `frontend/src/modules/module-2/lib/calendar.js`.

# Confirmation des suppressions — 2026-10-22

Les boutons de suppression des employés et des rôles ouvrent `shared/components/DeleteConfirmation.jsx`. Aucun appel DELETE n'est envoyé avant confirmation explicite. Le dialogue utilise `showModal()` pour le focus et la navigation clavier ; Annuler et Échap ferment la confirmation hors requête. Pendant la suppression, les boutons sont désactivés. En cas d'échec API, le dialogue se ferme et la page affiche le message d'erreur.


## Permissions du profil module 2 — 2026-10-22

Le profil `FRONTEND_MODULE_2_CONGES_ABSENCES` inclut désormais `demande_absence.update` : la page affiche les demandes reçues et les actions Valider/Refuser. Il s'agit d'un profil de gestion. Pour un employé, conserver un rôle avec `demande_absence.read` et éventuellement `demande_absence.create`, sans `demande_absence.update`. Après modification des rôles, une reconnexion actualise les permissions enregistrées par le frontend.

## Affichage des onglets conges - 2026-10-22

LeavePage affiche la liste et les actions dans requests, et le composant LeavePlanning dans planning. Les variables calendarDays et eventsByDay restent internes a LeavePlanning.

## Actions de la liste des demandes - 2026-10-22

LeaveRequestDetail sert uniquement a consulter. Les boutons Valider, Refuser et Supprimer de la liste ouvrent LeaveActionConfirmation ; seul Confirmer declenche la requete POST ou DELETE existante. Annuler et Echap ferment sans envoyer. Pendant la requete, les boutons sont bloques. Une erreur ferme la confirmation et affiche le message API dans la page ; apres succes, les donnees sont rechargees. La vue/service/repository backend reste responsable des autorisations et validations, notamment du quota annuel.

## Planning des effectifs - 2026-10-22

LeavePlanning orchestre le mois, les filtres et la date selectionnee. PlanningRoster affiche les groupes presents prevus et absents sans limiter le nombre de personnes visibles. lib/planning.js indexe les dates et regroupe par identifiant employe. Une absence prime sur une presence prevue. Les permissions sont cumulees sur tous les roles ; les roles ne servent pas a identifier les personnes. Les donnees API restent limitees par les droits backend. Les presences prevues ne constituent pas un pointage reel. Verification : node check-planning.mjs et node check-leave-tabs.mjs depuis frontend/.
## Retour de validation utilisateur — 2026-10-23

L'utilisateur confirme également le bon fonctionnement des boutons du module 2 et valide leur comportement dans son navigateur. Cette confirmation complète les tests automatisés des parcours API. Le rendu mobile et la navigation clavier ne sont pas explicitement confirmés par ce retour.

Contrôles complémentaires automatisés : compilation Vite et scripts de rendu/permissions, d'onglets et de planning réussis le 2026-10-23. Le contrôle de gestion vérifie également que les codes ne sont pas affichés dans les cartes des types. Ces scripts exécutent le rendu React côté serveur et des fonctions de regroupement ; ils ne pilotent pas de navigateur et ne prouvent pas le fonctionnement des clics ou la présentation mobile.

Les écrans du module 2 affichent le libellé du type de congé sans son code technique généré. Le code reste disponible côté backend pour l'identification ; il n'est présenté ni dans les cartes des types, ni dans le choix d'une demande, ni en remplacement du libellé dans le planning ou le détail.

L'utilisateur confirme que le code des types est généré sans saisie et conservé lors d'une modification du libellé. Il confirme aussi, avec un compte employé distinct du gestionnaire : choix du type, refus des dates inversées, envoi correct d'une demande en attente, consultation limitée à ses propres demandes, absence des actions Valider/Refuser et détail exact en lecture seule. Le droit du type de test a été remis à 10 jours. Ces résultats sont déclarés par l'utilisateur ; les soldes, décisions, suppressions, planning, rôles multiples et présentation restent à valider avant de déclarer le module terminé.

## Utilisation de shadcn/ui — 2026-10-23

Le frontend est configuré pour ajouter des composants shadcn en `.jsx` dans `src/shared/components/ui/`. `components.json` définit les chemins partagés ; `jsconfig.json` et Vite résolvent `@/` vers `src/`. `utils.js` expose `cn` pour la fusion des classes. Les styles shadcn sont chargés depuis `app/main.jsx` et compilés par Tailwind v4. Les couleurs `--ui-*` évitent les collisions avec les variables des anciens écrans.

Après retour utilisateur sur le rendu, les actions de `RecordManager` et les boutons de `RecordEditor` du module 3 utilisent de nouveau des boutons HTML avec `primary-button`, `outline-button` et `danger-button`. Les callbacks, états occupés, permissions et payloads sont conservés. shadcn reste configuré pour les futurs besoins. Le composant inutilisé `ui/button.jsx` et ses styles spécifiques ont été supprimés ; les règles CSS générales des boutons sont rétablies. Réserver son adoption aux besoins de cohérence ou aux composants élaborés, selon le skill React. Compilation et contrôle de rendu du module 3 réussis ; appréciation visuelle à confirmer par l'utilisateur.


## Module 6 — TGM et simulation, 2026-10-25

`modules/module-6/` porte la page `TgmPage`, ses composants, le hook `useTgmReport` et les utilitaires de période. `/tgm` est une route React chargée à la demande depuis `app/AppRouter.jsx`. La navigation et le contrôle d’accès suivent `paie.read` ; les vérifications de session et les appels passent par les helpers partagés.

Les filtres début/fin conservent un brouillon jusqu’à « Afficher les coûts ». Le dernier jour du mois est déterminé avec les années bissextiles, y compris les années 0001 à 0099. Deux requêtes indépendantes chargent les taux par mois et les coûts par dates ; erreurs, chargements et reprises sont distincts. Les anciens résultats et réponses tardives ne sont pas présentés sous un nouveau périmètre.

Les tableaux shadcn sont défilables au clavier, avec légende, en-têtes et lignes identifiées. Les fiches projet détaillent les employés et tâches dans des éléments `details`. Les taux indisponibles, heures sans taux et coûts partiels sont explicitement affichés ; aucun montant agrégé n’est recalculé par React.

`TgmSimulation` transmet le projet et le chiffre d’affaires XOF saisi à l’API de simulation. Les marges et pourcentages sont calculés côté serveur. Le résultat est effacé lorsque les paramètres changent ; le scénario est réinitialisé au changement de période ou au rechargement des coûts. Le chiffre d’affaires n’est pas enregistré en base ni dans le stockage navigateur.

## Module 7 — Feuilles de temps, 2026-10-25

La page `TimesheetsPage` compose quatre espaces, chargés selon les droits : `MyTimesheets`, `ReviewTimesheets`, `TimesheetProjects` et `TimesheetCosts`. L’entrée `/feuilles-de-temps` utilise le layout commun et un chargement séparé dans Vite. Chaque employé connecté peut saisir ses propres feuilles. Les onglets de validation, de préparation des projets et de coûts nécessitent respectivement `feuille_temps.decide`, `projet.read` et `paie.read`.

`TimesheetEditor` gère une semaine et ses lignes contrôlées : date, projet affecté actif, tâche active, unité heures/jours, quantité et commentaire. `validateSheet` vérifie les dates, le lundi, les choix et les bornes simples ; le serveur vérifie les affectations et la limite journalière contractuelle. Les durées en jours sont converties côté serveur. Les champs `total_heures` et `jours_saisis` sont présentés tels que retournés par l’API ; aucune valorisation financière n’est calculée dans React.

Les confirmations de soumission, suppression, validation et retrait d’affectation utilisent `ModalDialog`. Le refus exige un motif. Une feuille soumise n’est pas éditable ; modifier une feuille validée affiche un avertissement de retour en brouillon. Les erreurs imbriquées des lignes sont transformées en messages français lisibles, avec numéro de ligne. `TimesheetField` associe un label stable et un message d’erreur à chaque contrôle.

`TimesheetProjects` permet la préparation indispensable à la saisie : nouveau projet actif, nouvelle tâche active et affectations d’employés. Les actions suivent les droits projets/tâches existants ; le choix d’un employé nécessite `employe.read`. Cette tranche ne propose pas de suppression ou d’édition complète des projets/tâches.

`TimesheetCosts` consulte le rapport serveur par dates. Le tableau de rapprochement présente projet, employé, mois du taux, heures validées, TGM horaire chargé, coût estimé et heures sans taux. Les dossiers sans paie/horaire utilisable ne sont pas présentés comme un coût complet. Le lien vers le module 6 permet de consulter le dénominateur du taux ou simuler la marge.

`useApiResource` est partagé avec le module 6 : appels authentifiés, gestion de session expirée, chargement, reprise et rejet des réponses tardives. `useTimesheetMutation` verrouille les doubles envois et expose les erreurs. Les ressources sont rechargées après mutation et au retour sur un onglet. Le scénario de recette navigateur écrit uniquement dans une base temporaire, créée par `tmp/run_timesheets_browser.py`.

## Accueil et navigation des profils personnels — 2026-10-25

`shared/lib/homePath.js` détermine une route initiale autorisée à partir du profil renvoyé par la connexion. L’annuaire est conservé pour `employe.read` ; la paie, la masse salariale et le TGM suivent leurs droits respectifs. Le repli personnel est la page des feuilles de temps, ouverte à chaque employé connecté. `LoginPage` utilise ce choix après authentification et `AppLayout` l’utilise pour le logo ; le lien d’annuaire est conditionné à `employe.read`.

Awa et Moussa ont reçu uniquement `EMPLOYE_SIMPLE` : leurs demandes et soldes de congés, leurs coordonnées bancaires et leurs feuilles de temps sont accessibles. Les menus TGM, masse salariale, paie, administration des rôles et validation ne sont pas affichés. La liste détaillée des sept permissions et les conditions de recette sont dans `output/permissions/roles-et-comptes-test.md`. Une reconnexion actualise le profil stocké dans le navigateur.

## Projets/tâches sans code saisi et options actualisées — 2026-10-25

`ProjectNameForm` ne contient plus de champ Code et envoie seulement le nom et l’état actif. Les codes renvoyés par l’API sont des références automatiques ; ils ne sont ni demandés ni calculés dans le navigateur.

`MyTimesheets` recharge les projets affectés lors de chaque ouverture de `TimesheetEditor`. Il active aussi `refreshOnFocus` de `useApiResource` : retour visible dans la fenêtre/onglet et événement de focus déclenchent une lecture des options. Le bouton « Actualiser les projets et tâches » dans le formulaire permet une reprise explicite. Les lignes du brouillon sont conservées dans le parent du rendu de chargement, ce qui préserve dates, quantités et commentaires pendant ces lectures.

`useApiResource` expose un callback de rechargement stable et associe la réponse à sa révision. Dès qu’une nouvelle lecture est demandée, l’ancienne réponse est masquée ; une réponse tardive n’écrase pas les données les plus récentes. Les écouteurs de visibilité/focus sont nettoyés au démontage et cette actualisation automatique est activée uniquement pour les options de saisie.

L’affectation à un projet ouvre toutes ses tâches actives à l’employé. Un projet sans tâche active affiche un message dédié. La recette teste explicitement un compte ouvert avant la préparation du projet, puis une tâche ajoutée pendant qu’un brouillon est déjà affiché ; l’enregistrement et la soumission utilisent la liste rafraîchie.

## Visibilité et saisie personnelle des temps - 2026-10-26

AssignedTimesheetProjects partage la ressource personnelle de MyTimesheets, affiche les projets et tâches actifs et ouvre TimesheetEditor avec initialProject. Les droits de consultation globale ne sont pas ajoutés aux employés. Les feuilles restent personnelles ; les affectations autorisent la saisie sans créer automatiquement une feuille.

ProjectDetails affiche une suppression de tâche avec confirmation selon tache.delete. L'API intercepte ProtectedError et renvoie HTTP 400 si des heures référencent la tâche, sans supprimer l'historique. La migration 0045 ajoute la permission au profil FRONTEND_MODULE_7_FEUILLES_TEMPS. Les sessions déjà ouvertes doivent être reconnectées pour actualiser les permissions affichées.

## Liste des tâches restant à saisir - 2026-10-26

MyTimesheets charge une ressource dédiée /api/feuilles-temps/projets/?a_saisir=true pour AssignedTimesheetProjects. Le backend exclut les identifiants de tâches référencées dans une feuille VALIDEE du seul employé connecté, puis écarte les projets vides. Cette liste est indépendante du filtre de date de l'historique. Brouillons et feuilles soumises ne masquent pas les tâches. Les options sans filtre restent disponibles au formulaire pour conserver l'édition et les nouvelles saisies. Le retour au premier plan, le bouton d'actualisation et les mutations personnelles rechargent la liste.

## Libellés des projets et tâches - 2026-10-26

Les composants du module 7 utilisent nom, projet_nom et tache_nom pour leurs libellés visibles. Les codes PROJ_/TASK_ ne sont plus affichés. Les identifiants des options, clés React et données API sont conservés.

## Profil personnel - 2026-10-26

AppLayout affiche un lien sur l'email du compte et ouvre AccountProfile. Le formulaire lit GET /api/auth/me/, sauvegarde uniquement nom/prénom par PATCH /api/auth/me/, puis actualise localStorage et l'identité affichée. POST /api/auth/password/ exige le mot de passe actuel, le nouveau et sa confirmation ; les validateurs Django sont appliqués en français. Les champs de rôles, d'identifiants, d'email et de gestion sont rejetés sur le profil personnel. Aucun droit employe.update n'est requis pour ce parcours limité à request.user.

Après succès du changement de mot de passe, la session locale est effacée et la connexion réaffichée. Cette opération ne prétend pas révoquer les JWT déjà émis dans d'autres sessions. Les noms/prénoms font désormais partie de la réponse de connexion et du profil courant. Les mots de passe ne sont jamais enregistrés dans le stockage du navigateur par ce formulaire.

## Confirmation de l'archivage du bulletin - 2026-10-26

PayrollAction précise que la validation crée et archive le PDF. usePayrollActions confirme la disponibilité du bulletin après succès. La liste recharge les données et utilise bulletin_disponible pour proposer le téléchargement de l'archive.

## Consultation des fiches dans l'espace employé - 2026-10-26

MyPayslipsPage charge /api/mes-bulletins/ et présente les fiches personnelles validées/payées, avec filtre par année. PersonalPayslipViewer charge le PDF avec le JWT par apiRequest, vérifie son type puis l'affiche via une URL blob dans un iframe nommé. L'URL est révoquée au démontage. Le lecteur propose aussi ouverture séparée et téléchargement ; la liste utilise downloadApiFile pour le téléchargement direct. Les erreurs de fichier absent et de session sont traitées sans exposer le stockage privé. Aucun droit paie.read n'est ajouté aux employés.

## Gestion des postes et historique des dossiers - 2026-10-26

EmployeesPage envoie poste_nom et responsable dans les créations/modifications. Les noms de poste et types de contrat courants renvoyés par l'annuaire alimentent les listes de filtres sans chargement de salaires ni droit de gestion des contrats supplémentaire. L'historique est extrait dans EmployeeHistory, qui charge l'endpoint personnel au dossier et présente les instantanés avant/après en colonnes adaptatives. La reprise initiale des données est distinguée des changements effectués depuis l'activation du suivi.

## Poste sélectionné dans le contrat - 2026-10-26

PositionManager fournit le CRUD de /api/postes/ avec formulaires nom/description et confirmation de suppression. EmployeeContracts charge le catalogue avec les contrats et les types via useEmployeeContracts. ContractEditor envoie un identifiant poste et conserve ses champs lorsque le catalogue est actualisé après création d'un poste. Les erreurs de chargement des postes bloquent l'enregistrement de la sélection ; un compte sans lecture du catalogue conserve le poste existant lors d'une modification autorisée, sans l'effacer.

EmployeesPage affiche les postes_actuels dérivés des contrats, les utilise pour les filtres et supprime la saisie libre de poste sur l'employé. EmployeeHistory sait afficher les instantanés de poste imbriqués dans l'historique contractuel.
# Navigation partagée — présentation du 26 octobre 2026

`AppLayout.jsx` centralise les destinations, leurs icônes et leurs droits. Les liens « Feuilles de temps » et « Mes bulletins de paie » restent disponibles pour tout compte connecté. Les autres destinations conservent leurs permissions propres ; les autorisations serveur sont inchangées.

Sur ordinateur, la barre latérale utilise un fond clair et un état actif gris. Sur tablette et téléphone (largeur <= 1100 px), une barre compacte affiche le nom du module et ouvre un menu plein écran. Ce menu conserve le lien de profil placé sur l'email et la déconnexion. Son ouverture bloque le défilement de fond et rend le contenu inerte ; Tab et Maj+Tab restent dans le menu, Échap ferme et replace le focus sur son bouton. Le changement de format referme le menu.

Le thème de travail utilise Segoe UI, disponible localement sur Windows, des surfaces opaques, des boutons plats et des couleurs sémantiques pour les statuts. L'annuaire conserve les mêmes données et actions. Ses filtres restent visibles sur ordinateur et se déplient par « Filtres » sur téléphone, avec le nombre de filtres actifs. Les colonnes restent consultables par défilement dans le tableau et la première colonne reste fixe. Les dégradés des styles hérités et de la connexion ont été remplacés par des aplats.

La vérification visuelle porte sur le DOM rendu de l'annuaire, capturé avec ses CSS puis mesuré par l'inspecteur design-taste ; les comportements sont testés séparément dans un vrai navigateur avec Django et une base temporaire. Les captures contiennent uniquement des comptes de recette.

