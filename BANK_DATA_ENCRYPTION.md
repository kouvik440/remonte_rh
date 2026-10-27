# Stockage bancaire chiffré

Activation locale : 23 octobre 2026, migration `core.0033_encrypt_bank_details` appliquée sur PostgreSQL.

## Périmètre

Les colonnes IBAN, BIC et SWIFT sont chiffrées avec Fernet avant leur stockage et déchiffrées lors de la lecture ORM. Les champs facultatifs vides restent vides. Le nom de la banque, le propriétaire et les dates restent lisibles en base. L'API autorisée restitue les valeurs utilisables par l'application ; les droits CRUD et le contrôle propriétaire/gestionnaire restent inchangés.

Les champs personnalisés se trouvent dans `backend/core/fields.py`. Le chemin applicatif reste vue → service → interface → repository → modèle. Le repository traite les conflits d'unicité, puis le service les traduit en erreur de validation. Une empreinte HMAC de l'IBAN normalisé assure l'unicité sans comparer les valeurs chiffrées aléatoires. L'empreinte n'est pas exposée dans l'API.

## Clé et sauvegarde

La clé locale est dans `C:\Users\HP\.remonte-rh\bank-data.key`, hors dépôt. Le répertoire utilise une ACL Windows réservée au compte courant. Le chargement suit cet ordre :

1. Variable `BANK_DATA_ENCRYPTION_KEY`, si renseignée.
2. Fichier indiqué par `BANK_DATA_ENCRYPTION_KEY_FILE`.
3. Fichier par défaut `~/.remonte-rh/bank-data.key`.

La clé doit être sauvegardée dans un emplacement sécurisé distinct de la base. Sa perte rend les valeurs chiffrées illisibles. Ne pas régénérer ou remplacer cette clé : aucune procédure automatique de rotation n'est implémentée. Un autre déploiement doit disposer de sa configuration de secret et de la clé correspondant à ses données. Ne jamais versionner ni afficher la clé.

Une sauvegarde chiffrée des deux fiches avant migration est conservée dans `C:\Users\HP\.remonte-rh\bank-backup-20261023-2f67c13d.fernet`. Elle nécessite cette même clé. Les anciennes copies de base ou exports antérieurs à cette migration ne sont pas chiffrés rétroactivement.

## Migration et écritures

La migration est transactionnelle et vérifie la clé ainsi que l'absence de doublons d'IBAN normalisés avant la conversion. Elle conserve les propriétaires, valeurs et dates existantes. Le retour arrière automatique vers des colonnes en clair est volontairement indisponible.

Utiliser le repository pour les écritures applicatives. Les écritures ORM `save`, `create`, `bulk_create` et `QuerySet.update` avec du texte littéral chiffrent les valeurs. Les mises à jour par expressions et `bulk_update` des champs sensibles sont refusées. Les recherches directes sur les colonnes chiffrées sont interdites, sauf `isnull` ; les recherches d'IBAN utilisent son empreinte. Les écritures SQL directes contournent ces protections et ne doivent pas servir à alimenter ces colonnes.

Une restauration doit associer la base, son schéma et la bonne clé. Une clé absente, invalide ou différente fait échouer l'accès aux valeurs sensibles, sans repli en clair.

## Vérifications réalisées

- 133 tests `core` réussis sur SQLite isolé.
- 15 tests chiffrement et accès bancaire réussis sur PostgreSQL de test, puis base de test supprimée.
- Migration depuis des données en clair vérifiée sur une base temporaire.
- Base PostgreSQL active : deux fiches conservées, comparaison avec la sauvegarde, contrôle SQL du chiffrement et des empreintes réussis.
- Le lanceur Django de tests utilise une clé éphémère, indépendante de la clé locale.

Commandes de contrôle : `manage.py test core --noinput` avec `USE_SQLITE=1`, puis les tests ciblés `core.test_bank_storage core.tests.BankDataSecurityTests core.tests.CoordonneesBancairesAccessTests` sur PostgreSQL isolé. Le parcours interactif dans le navigateur n'a pas été vérifié lors de cette intervention.

## Instantané des ordres de virement — 23 octobre 2026

Depuis la migration 0040, document_donnees contient les instructions et les RIB d’un ordre PDF sous forme de JSON chiffré avec la même clé Fernet. La liste API n’expose ni cet instantané ni le chemin du PDF. Les PDF eux-mêmes contiennent les coordonnées complètes, sont conservés dans le stockage privé sur disque et sont téléchargés avec ordre_virement.generate_document, ordre_virement.read et paie.read. Leur stockage fichier n’est pas chiffré par ce mécanisme de champ SQL ; les sauvegardes de fichiers doivent donc rester protégées. Le téléchargement n’utilise aucune URL média publique.
