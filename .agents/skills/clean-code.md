---
name: clean-code
description: 'Utiliser pour écrire, refactoriser, revoir ou corriger du code en appliquant les principes Clean Code, SOLID, DRY/KISS/YAGNI, les bonnes pratiques Django (modèles, Repository, performance, architecture en couches) et React (composants propres). Prioriser la lisibilité, la testabilité et la maintenabilité.'
---

# Clean Code — Principes & Pratiques (Django + React)

## 1. Philosophie

- Le code est lu **10 fois plus souvent** qu’il n’est écrit. Optimiser d’abord pour la lisibilité.
- Un code est propre quand un développeur qui le découvre comprend immédiatement l’intention, sans explication orale.
- Règle du Scout : « Laissez le code plus propre que vous ne l’avez trouvé. »

## 2. Nommage

### Variables
- Un bon nom révèle l’intention. Si on doit lire le corps pour comprendre, renommer.
- Éviter : `d`, `lst`, `tmp`, `flg`, `usr_cnt`, `x`, `data2`…
- Préférer : `SECONDS_PER_DAY`, `active_users`, `is_authenticated`, `total_registered_users`

**Conventions :**
- Python : `snake_case` (variables/fonctions), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constantes)
- JavaScript/React : `camelCase` (variables), `PascalCase` (composants), `UPPER_SNAKE_CASE` (constantes)
- Django : Model au singulier (`Order` pas `Orders`), champs en `snake_case`, toujours un `verbose_name` lisible

### Fonctions
- Nom = verbe d’action + contexte : `send_welcome_email_to_user`, `calculate_order_total`, `validate_order`
- Une fonction = **une seule chose**. Si le nom contient « et », diviser.
- Nombre de paramètres idéal : 0-2. Maximum 3. Au-delà → objet de paramètres.
- Éviter les noms vagues (`process`, `handle`, `doStuff`).

## 3. Commentaires

- Le code dit le **quoi** et le **comment**. Le commentaire dit uniquement le **pourquoi**.
- Interdit : commentaires qui répètent ce que le code dit déjà.
- Utile : contraintes métier, choix d’algorithme, comportements non évidents, limites techniques (ex: BCrypt 72 chars).

```python
# ❌ Mauvais
counter += 1  # Incrémenter le compteur

# ✅ Bon
# +1 pour inclure la borne droite (comportement attendu par l'API v3)
range_end = last_index + 1
```

## 4. Longueur et complexité des fonctions

- Idéal : 5-15 lignes. Maximum acceptable : 20-30 lignes.
- Complexité cyclomatique > 10 = signal d’alarme → décomposer.
- Si on peut extraire une fonction, on doit le faire.
- Une fonction monolithique de 50+ lignes doit être découpée en responsabilités claires.

```python
# ❌ Monolithique
def process_order(order_data):
    # validation + calcul + sauvegarde + notification (50+ lignes)

# ✅ Propre
def process_order(order_data):
    validate_order(order_data)
    total = calculate_order_total(order_data)
    order = create_order(order_data, total)
    notification.send_confirmation(order)
    return order
```

## 5. Principes SOLID

| Lettre | Principe | Règle concrète |
|--------|----------|----------------|
| **S** | Single Responsibility | Une classe/fonction = une seule raison de changer |
| **O** | Open/Closed | Ouvert à l’extension, fermé à la modification (composition/héritage plutôt que if/elif en cascade) |
| **L** | Liskov Substitution | Une sous-classe doit pouvoir remplacer sa parente sans casser le comportement |
| **I** | Interface Segregation | Préférer plusieurs petites interfaces spécifiques à une grosse interface générique |
| **D** | Dependency Inversion | Dépendre d’abstractions, jamais de concrétions. Injecter les dépendances (testabilité) |

## 6. DRY · KISS · YAGNI

- **DRY** : Don’t Repeat Yourself. Une règle métier = un seul endroit. Toute duplication est une dette.
- **KISS** : Keep It Simple, Stupid. La solution la plus simple qui fonctionne est presque toujours la meilleure.
- **YAGNI** : You Aren’t Gonna Need It. Ne pas implémenter une feature « au cas où ».

```python
# ❌ Violation DRY
prix1 = 100 * 1.20
prix2 = 50 * 1.20

# ✅ DRY
TAUX_TVA = 1.20
def calc_ttc(prix):
    return prix * TAUX_TVA
```

## 7. Gestion des erreurs

- Ne jamais avaler une exception (`except: pass`).
- Éviter les `except Exception` trop larges sans relancer ou logger correctement.
- Préférer des **exceptions métier** explicites.

```python
class OrderNotFoundError(AppException):
    def __init__(self, order_id):
        super().__init__(f'Commande {order_id} introuvable')

try:
    order = Order.objects.get(id=oid)
except Order.DoesNotExist:
    raise OrderNotFoundError(oid)
```

## 8. Tests unitaires

- Pattern **AAA** : Arrange → Act → Assert.
- 1 test = 1 comportement.
- Nommer clairement : `test_create_order_raises_error_when_stock_empty`
- Pyramide : ~70% unitaires, 20% intégration, 10% E2E.
- Objectif de couverture : > 80% sur le code critique.
- Injecter les dépendances pour pouvoir mocker facilement.

## 9. Django — Modèles propres

Tout modèle doit avoir :
- `verbose_name` et `verbose_name_plural`
- `__str__` clair
- `related_name` sur les ForeignKey
- Classe `Meta` avec `ordering` et index si pertinent
- Constantes de choix (`STATUS = [...]`) plutôt que des chaînes magiques

```python
class Order(models.Model):
    STATUS = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
    ]
    customer = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='client'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'commande'
        verbose_name_plural = 'commandes'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['customer'])]

    def __str__(self):
        return f'Order #{self.pk} - {self.customer}'
```

## 10. Django — Repository Pattern & Architecture en couches

**Architecture obligatoire : Repository Pattern, conforme au backend existant.**

- Toute création, correction ou refactorisation doit respecter cette architecture, y compris pour le code déjà écrit.
- Conserver le sens des dépendances : vues/API → services métier → interfaces de repository → repositories Django → modèles.
- Les vues gèrent HTTP, les permissions et la sérialisation ; elles délèguent les règles métier aux services.
- Les services reçoivent leurs repositories par injection et dépendent des interfaces définies dans `backend/core/interfaces/`.
- Les requêtes ORM et la persistance restent dans `backend/core/repositories/`. Ne pas les ajouter aux vues ni aux services ; y compris les appels `filter()`, `get()` et `save()`.
- Avant d'ajouter une abstraction, examiner et réutiliser les interfaces, repositories et services existants.
- Côté React, séparer l'affichage, les hooks de coordination et l'accès à l'API centralisé. Les règles métier et l'accès à la base restent dans les couches du backend ; ne pas les dupliquer dans les composants.

**Responsabilités des couches :**
1. **Views / API** → reçoivent la requête, délèguent, retournent la réponse
2. **Services** → logique métier pure (testable sans HTTP)
3. **Repository** → accès aux données (ORM isolé)
4. **Domain Models** → entités métier

```python
class IOrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, id) -> Order: ...
    @abstractmethod
    def save(self, order: Order): ...

class DjangoOrderRepository(IOrderRepository):
    def find_by_id(self, id):
        return Order.objects.get(pk=id)
    def save(self, order):
        order.save()
```

## 11. Django — Performance

- Toujours résoudre le **N+1** avec `select_related` (FK) et `prefetch_related` (M2M / reverse FK).
- Utiliser `only()` / `values()` pour ne charger que les champs nécessaires.
- `bulk_create` / `bulk_update` pour les opérations de masse.
- Cache (`cache_page`, `cache.get/set`) sur les calculs ou vues coûteuses.
- Custom Manager pour encapsuler les requêtes fréquentes.

```python
# ❌ N+1
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)

# ✅ Correct
orders = Order.objects.select_related('customer').prefetch_related('items')
```

## 12. React — Composants propres

- 1 composant = 1 responsabilité.
- Séparer **Container** (logique + données) et **Présentationnel** (affichage).
- Extraire la logique dans des **custom hooks**.
- Props explicites et typées (PropTypes ou TypeScript).
- `useMemo` / `useCallback` uniquement si un problème de performance est prouvé (pas d’optimisation prématurée).

```jsx
// Custom hook — logique isolée
function useUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => { fetchUsers().then(setUsers); }, []);
  return { users, loading };
}

// Composant pur
function UserCard({ user }) {
  return <div className="card">{user.name}</div>;
}

// Container
function UserDashboard() {
  const { users } = useUsers();
  return <>{users.map(u => <UserCard key={u.id} user={u} />)}</>;
}
```

## 13. Loi de Déméter

- Une méthode ne doit parler qu’à ses « amis » directs (self, paramètres, attributs, objets créés localement).
- Éviter les « train wrecks » : `order.customer.wallet.balance`
- Préférer : `order.get_customer_balance()` ou le style tell-don’t-ask.

## 14. Formatage & Outils

- **Python** : Black + Flake8 (PEP8)
- **JavaScript** : ESLint + Prettier
- Max 80-120 colonnes par ligne
- 1 ligne vide entre méthodes, 2 entre classes
- Ordre dans une classe Python : constantes → `__init__` → méthodes publiques → méthodes privées (`_prefix`)

## 15. Checklist Code Review (avant merge)

| Catégorie | Points de contrôle |
|-----------|--------------------|
| **Nommage** | Noms révélateurs, prononçables, recherchables. Pas d’abréviations cryptiques |
| **Fonctions** | ≤ 30 lignes, une seule responsabilité, ≤ 3 paramètres |
| **Structure** | Zéro duplication, SOLID respecté, pas de couplage fort |
| **Django** | `select_related`/`prefetch_related`, `verbose_name`, pas de logique métier dans les Views |
| **React** | Custom hooks, séparation Container/Présentationnel, props claires |
| **Tests** | Couverture critique > 80%, noms de tests expressifs |
| **Documentation** | Roadmap et explication fonctionnelle des parties concernées mises à jour, vérifications et limites précisées |
| **Divers** | Pas de code mort, commentaires = pourquoi uniquement, Scout rule appliquée |

## 16. Règles de travail prioritaires

1. Lire le code existant avant d’écrire.
2. Appliquer la règle du Scout à chaque modification.
3. Extraire dès que la responsabilité n’est plus unique.
4. Nommer d’abord, optimiser ensuite.
5. Tester le comportement, pas l’implémentation.
6. Préférer la simplicité (KISS) à la sur-ingénierie (YAGNI).
7. À chaque intervention sur le code, vérifier et mettre à jour la roadmap et l'explication fonctionnelle concernées avant de terminer, selon les règles ci-dessous.

## 17. Documentation à maintenir à chaque intervention

- Pour le frontend : mettre à jour `ROADMAP_frontend.md` et `explication_fonction_frontend.md`.
- Pour le backend : mettre à jour `ROADMAP_backend.md` et `explication_fonction_backend.md`.
- Si l'intervention concerne les deux parties, mettre à jour les quatre fichiers. Vérifier aussi les documents généraux `ROADMAP.md` et `explication_fonction_module.md` si l'organisation ou le périmètre des modules change.
- Dans la roadmap, actualiser la rubrique du module concerné : travail réalisé, état actuel, vérifications effectuées et tâches restantes. Distinguer clairement les travaux terminés de ceux à poursuivre.
- Dans l'explication fonctionnelle, décrire le comportement final et les responsabilités des composants, services et repositories concernés. Corriger les passages devenus obsolètes plutôt que d'empiler des notes contradictoires.
- Indiquer la date réelle de mise à jour et les limites de validation : un test non exécuté ou un parcours navigateur non vérifié ne doit pas être présenté comme réussi.
- Pour une question ou une explication sans modification du projet, aucune mise à jour documentaire n'est nécessaire.
