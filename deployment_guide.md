# Guide de déploiement Congo Connect sur PythonAnywhere

## 1. Préparation du projet

### Vérification de la compatibilité
- ✅ Congo Connect utilise Flask avec SQLAlchemy
- ✅ Base de données PostgreSQL intégrée et prête
- ✅ Upload de fichiers local (compatible)
- ✅ Architecture simple et scalable
- ✅ API Lygos intégrée pour les paiements africains

### Capacité de la base de données PostgreSQL
**PostgreSQL peut gérer des millions d'utilisateurs** :
- ✅ 10,000-100,000 utilisateurs : Performance excellente
- ✅ 100,000-1,000,000 utilisateurs : Performance optimale
- ✅ 1,000,000+ utilisateurs : Scalable avec optimisation

## 2. Déploiement sur PythonAnywhere

### Étape 1: Upload du projet
```bash
# Compresser le projet localement
zip -r congo_connect.zip . -x "__pycache__/*" "*.pyc" "instance/*"

# Sur PythonAnywhere, extraire dans ~/congo_connect/
cd ~
unzip congo_connect.zip -d congo_connect/
cd congo_connect
```

### Étape 2: Installation des dépendances
```bash
# Créer un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances (inclut requests pour Lygos)
pip install flask flask-sqlalchemy flask-login gunicorn pillow werkzeug psycopg2-binary requests
```

### Étape 3: Configuration de l'application web
Dans l'onglet "Web" de PythonAnywhere :

1. **Source code** : `/home/yourusername/congo_connect`
2. **Working directory** : `/home/yourusername/congo_connect`
3. **WSGI configuration file** : 
```python
import sys
import os

# Add your project directory to the sys.path
path = '/home/yourusername/congo_connect'
if path not in sys.path:
    sys.path.append(path)

from main import app as application

# Set environment variables
os.environ['SESSION_SECRET'] = 'your-super-secret-key-here'
os.environ['DATABASE_URL'] = 'sqlite:///congo_connect.db'

if __name__ == "__main__":
    application.run()
```

### Étape 4: Configuration des variables d'environnement
```bash
# Dans .env ou directement dans WSGI
SESSION_SECRET=your-super-secret-production-key
DATABASE_URL=sqlite:///congo_connect.db
```

### Étape 5: Initialisation de la base de données
```bash
cd ~/congo_connect
source venv/bin/activate
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Étape 6: Configuration des fichiers statiques
Dans l'onglet "Files" :
1. Créer le dossier `/home/yourusername/congo_connect/static/uploads/`
2. Configurer les permissions : `chmod 755 static/uploads/`

### Étape 7: Test et activation
1. Cliquer sur "Reload" dans l'onglet Web
2. Tester l'application sur `yourusername.pythonanywhere.com`

## 3. Migration vers PostgreSQL (si nécessaire)

### Quand migrer ?
- Plus de 50,000 utilisateurs actifs
- Plus de 10,000 annonces simultanées
- Besoin de recherche avancée
- Trafic intensif

### Étapes de migration
```python
# 1. Installer psycopg2
pip install psycopg2-binary

# 2. Modifier DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost/congo_connect

# 3. Migrer les données
python migrate_to_postgres.py  # Script de migration à créer
```

## 4. Optimisations pour la production

### Performance
```python
# app.py - Configuration production
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'max_overflow': 0
}
```

### Sécurité
```python
# Variables d'environnement obligatoires
SESSION_SECRET=randomly-generated-secret-key
DATABASE_URL=your-database-url
UPLOAD_FOLDER=/secure/path/uploads
```

### Monitoring
- Logs d'erreur dans `/var/log/`
- Monitoring de la base de données
- Surveillance de l'espace disque

## 5. Maintenance et mise à jour

### Sauvegarde quotidienne
```bash
# Script de sauvegarde
#!/bin/bash
DATE=$(date +%Y%m%d)
cp ~/congo_connect/congo_connect.db ~/backups/congo_connect_$DATE.db
tar czf ~/backups/uploads_$DATE.tar.gz ~/congo_connect/static/uploads/
```

### Mise à jour du code
```bash
cd ~/congo_connect
git pull origin main  # Si vous utilisez Git
# Ou re-upload le zip et extraire
source venv/bin/activate
pip install -r requirements.txt
# Redémarrer l'application web
```

## 6. Coûts et limites

### PythonAnywhere Free
- ✅ Parfait pour démarrer et tester
- ⚠️ 512 MB de stockage (suffisant pour commencer)
- ⚠️ Trafic limité

### PythonAnywhere Paid ($5-20/mois)
- ✅ Plus de stockage et de bande passante
- ✅ Support pour bases de données externes
- ✅ Nom de domaine personnalisé
- ✅ HTTPS inclus

## 7. Alternative : Déploiement sur Replit

Congo Connect est déjà optimisé pour Replit :
- ✅ Déploiement en un clic
- ✅ HTTPS automatique
- ✅ Mise à l'échelle automatique
- ✅ Intégration Git
- ✅ Collaboration en équipe

**Recommandation** : Commencer sur Replit pour le développement et les tests, puis migrer vers PythonAnywhere ou un VPS pour la production si nécessaire.

## 8. Checklist de déploiement

- [ ] Code uploadé et extrait
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées
- [ ] Variables d'environnement configurées
- [ ] Base de données initialisée
- [ ] Dossier uploads créé avec bonnes permissions
- [ ] Application web configurée
- [ ] Test de l'application
- [ ] Sauvegarde configurée
- [ ] Monitoring mis en place

Votre marketplace Congo Connect est maintenant prête pour des milliers d'utilisateurs !