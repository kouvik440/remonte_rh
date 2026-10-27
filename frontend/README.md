# Frontend Remonte RH

Frontend React servi et compilé par Vite. Django fournit l’API et les données.

## Démarrer l’application

À la racine du projet, démarre Django :

```powershell
cd C:\remonte_rh_project
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Dans un second terminal :

```powershell
cd C:\remonte_rh_project\frontend
npm install
npm run dev
```

Ouvre `http://127.0.0.1:5173/connexion`. Les deux serveurs doivent rester actifs.

Si Django est déjà lancé sur 8001, ne le relance pas. `manage.py` se trouve à la racine du projet, pas dans `frontend`. Si le terminal est déjà dans `frontend`, lance directement `npm run dev`.

## URL des pages

La navigation est une SPA : après l'ouverture initiale, les liens entre modules changent le contenu sans recharger le document. Les routes React sont sans extension. Les anciennes adresses `.html` sont converties automatiquement vers les routes ci-dessous. Les boutons précédent/suivant fonctionnent. La navigation ne conserve pas les formulaires non enregistrés ni les filtres des modules quittés.

- `/connexion` : connexion.
- `/employes` : annuaire et gestion des employés.
- `/roles` : consultation et création des rôles.
- `/conges` : demandes, planning mensuel, soldes et types de congé (selon les permissions).
- `/departements` : gestion des départements.
- `/coordonnees-bancaires` : coordonnées bancaires des employés.
- `/paie` : paies et virements.
- `/mes-bulletins` : bulletins personnels.
- `/masse-salariale` : analyse de la masse salariale.
- `/tgm` : taux et coûts projets.
- `/feuilles-de-temps` : feuilles de temps personnelles et gestion selon les droits.

## Organisation des fichiers

```text
src/
├── app/
│   └── main.jsx                 # Démarrage de React, choix de l'écran
├── modules/
│   ├── module-1/
│   │   └── pages/               # Écrans React connexion, employés, rôles
│   └── module-2/
│       └── pages/               # Écrans React congés et absences
├── index.html                   # Conteneur unique qui démarre React
└── shared/
    ├── components/              # Navigation et cadre partagés
    ├── lib/                     # Appels API, jetons JWT, session
    └── styles/                  # Feuille de style commune
```

Les pages d’interface sont des composants JSX regroupés par module dans `modules/`. Les anciens fichiers HTML par page ont été supprimés. Seul `src/index.html` est nécessaire au démarrage de React dans le navigateur.

`app/AppRouter.jsx` sélectionne les composants chargés à la demande et conserve un seul `AppLayout` entre modules. `shared/components/AppLink.jsx` et `shared/lib/navigation.js` gèrent les liens et l'historique côté navigateur. Les PDF et téléchargements restent des liens normaux.

En production, configurer le dossier publié sur `frontend/dist` et renvoyer `index.html` pour les routes d'interface. Exemple à intégrer au serveur Nginx dont `root` pointe vers ce dossier :

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8001;
}
location /assets/ {
    try_files $uri =404;
}
location / {
    try_files $uri /index.html;
}
```

Vite assure déjà ce repli avec `npm run dev` et `npm run preview`. Une adresse inconnue est traitée par la page React « Page introuvable ».

## Notions React dans ce projet

- **Composant** : fonction qui décrit une partie de l’écran. `EmployeesPage` décrit l’annuaire; `AppLayout` fournit le cadre commun.
- **JSX** : syntaxe utilisée dans les fichiers `.jsx` pour écrire l’interface avec des expressions JavaScript entre accolades.
- **État (`useState`)** : valeurs qui changent, comme la recherche, le formulaire ou les données chargées. React rafraîchit l’écran lorsqu’elles changent.
- **Effet (`useEffect`)** : action liée au cycle d’affichage, par exemple vérifier la session et charger les données.
- **Référence (`useRef`)** : accès à un élément de la page, ici pour amener l’utilisateur au formulaire.
- **Propriétés (`props`)** : données transmises d’un composant à un autre; `AppLayout` reçoit la page active et son contenu.
- **Gestionnaires d’événements** : `onClick`, `onChange` et `onSubmit` réagissent aux clics et aux saisies.
- **Vite** : serveur de développement et outil de compilation. Node.js exécute Vite et npm.

## Connexion à Django

`src/shared/lib/api.js` centralise les appels HTTP, ajoute le jeton JWT et tente de le renouveler si nécessaire. Les requêtes utilisent `/api/` sur la même origine que React. En développement et en aperçu de compilation, Vite relaie ces appels vers Django sur `http://127.0.0.1:8001`. Le port 8000 peut ainsi être utilisé par un autre projet sans recevoir les identifiants RH.

Pour un autre port Django, copie `.env.example` vers `.env.local` dans `frontend`, ajuste `REMONTE_RH_API_TARGET`, puis redémarre Vite. Pour une API de production sur un domaine distinct, renseigne explicitement `VITE_API_BASE_URL` et recompile ; sinon le serveur de production doit relayer `/api/` vers Django. Aucune adresse d'API ne doit contenir d'identifiants ou de secrets.

## Compiler

Depuis `frontend` :

```powershell
npm run build
```

Les fichiers prêts pour la production sont générés dans `frontend/dist/`.
## Composants React avec shadcn/ui

Exécuter les commandes dans `C:\remonte_rh_project\frontend` :

```powershell
npx shadcn add card
npm run build
```

La configuration `components.json` utilise JavaScript (`tsx: false`), l'alias `@/` vers `src/` et le dossier `src/shared/components/ui/`. Le composant Button a été retiré du projet. Exemple uniquement si ce composant est réinstallé explicitement avec `npx shadcn add button` ; les boutons actuels utilisent le HTML et le CSS du projet :

```jsx
import { Button } from '@/shared/components/ui/button';

<Button type="button" onClick={openForm}>Ajouter</Button>
<Button type="button" variant="outline" onClick={cancel}>Annuler</Button>
```

Tailwind v4 est compilé par le plugin Vite. `shared/styles/shadcn.css` charge le thème et les utilitaires, avec des variables `--ui-*` distinctes des styles existants. Le reset Preflight global est omis pour conserver les bases des écrans actuels ; les resets nécessaires sont appliqués aux primitives adoptées. Les futurs composants peuvent nécessiter des styles de base ciblés supplémentaires.

Les règles métier, permissions et appels API restent dans leurs couches actuelles. shadcn fournit les composants d'interface ; son ajout ne modifie pas le Repository Pattern backend. La configuration Vite ayant changé, redémarrer `npm run dev` si nécessaire.

