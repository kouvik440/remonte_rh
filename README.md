# remonte_rh

Application RH : API Django et interface React. Les instructions du frontend sont dans [frontend/README.md](frontend/README.md).

## Installation locale

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
```

Les dépendances Python et JavaScript sont réinstallées depuis `requirements.txt` et les fichiers npm. Les dossiers `venv/`, `node_modules/`, les caches, les compilations, les fichiers `.env`, les bases SQLite locales, les bulletins privés et les résultats temporaires sont exclus de Git. Les modèles de configuration `.env.example` restent versionnés.
