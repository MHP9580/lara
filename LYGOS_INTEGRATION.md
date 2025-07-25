# Guide d'intégration Lygos pour Congo Connect

## Vue d'ensemble de Lygos

Lygos est une solution de paiement spécialement conçue pour les marchés africains, offrant :
- **Couverture** : 13+ pays africains
- **Opérateurs** : 21 opérateurs de mobile money connectés
- **Méthodes** : Mobile Money, virements bancaires, Visa/Mastercard
- **API** : RESTful avec réponses JSON
- **Intégration** : Rapide avec quelques lignes de code

## Configuration étape par étape

### 1. Créer un compte Lygos

1. **S'inscrire sur Lygos**
   - Aller sur [lygosapp.com](https://lygosapp.com/en)
   - Cliquer sur "Sign Up" ou "Créer un compte"
   - Remplir les informations de votre entreprise

2. **Vérification du compte**
   - Vérifier votre email
   - Fournir les documents d'identité/entreprise requis
   - Attendre l'approbation (généralement 24-48h)

### 2. Obtenir votre clé API

1. **Accéder au dashboard**
   - Se connecter à votre compte Lygos
   - Aller dans la section "Développeur" ou "API"

2. **Générer votre clé API**
   - Cliquer sur "Générer nouvelle clé API"
   - Copier et sauvegarder cette clé en sécurité
   - Format typique : `lygos_live_xxxxxxxxxxxxx` ou `lygos_test_xxxxxxxxxxxxx`

### 3. Configuration dans Congo Connect

Congo Connect intègre déjà Lygos ! Voici comment l'activer :

1. **Ajouter votre clé API**
   ```bash
   # Dans vos variables d'environnement
   export LYGOS_API_KEY="your_lygos_api_key_here"
   ```

2. **Sur PythonAnywhere, dans votre fichier WSGI :**
   ```python
   os.environ['LYGOS_API_KEY'] = 'your_lygos_api_key_here'
   ```

### 4. Configuration des webhooks

1. **Dans votre compte Lygos :**
   - Aller dans "Paramètres" > "Webhooks"
   - Ajouter cette URL : `https://yourdomain.com/api/lygos/webhook`
   - Sélectionner les événements : `payment.completed`, `payment.failed`

2. **Test de webhook :**
   - Lygos enverra automatiquement des notifications à cette URL
   - Congo Connect traitera les paiements automatiquement

## Fonctionnalités intégrées

### Plans Premium avec Lygos

Congo Connect propose 3 plans Premium payables via Lygos :

| Plan | Durée | Prix FCFA | Prix € | Prix $ | Économie |
|------|-------|-----------|--------|---------|----------|
| Basique | 1 mois | 5,000 | 8€ | $9 | - |
| Populaire | 3 mois | 12,000 | 18€ | $20 | 20% |
| Premium | 6 mois | 20,000 | 30€ | $34 | 33% |

### Boutons de paiement

Les boutons Lygos sont déjà intégrés dans la page `/premium/upgrade` :

```html
<!-- Exemple pour le plan 1 mois -->
<form method="POST" action="/premium/pay-lygos">
    <input type="hidden" name="amount" value="5000">
    <input type="hidden" name="months" value="1">
    <button type="submit" class="btn btn-outline-primary">
        <i class="fas fa-credit-card"></i> Payer avec Lygos
    </button>
</form>
```

### Flux de paiement

1. **Utilisateur clique sur "Payer avec Lygos"**
   - Redirection vers la page de paiement Lygos
   - Choix du mode de paiement (Mobile Money, carte, etc.)

2. **Paiement traité par Lygos**
   - Interface sécurisée de Lygos
   - Support multi-opérateurs de mobile money
   - Confirmation en temps réel

3. **Retour automatique vers Congo Connect**
   - En cas de succès : `/premium/lygos/success`
   - En cas d'échec : `/premium/lygos/failure`
   - Activation automatique du Premium

## Code d'intégration

### Routes principales

```python
# Création du paiement Lygos
@app.route('/premium/pay-lygos', methods=['POST'])
def pay_with_lygos():
    payload = {
        'title': f'Congo Connect Premium - {months} mois',
        'amount': amount,
        'description': f'Abonnement Premium pour {current_user.full_name}',
        'success-url': url_for('lygos_success', _external=True),
        'failure-url': url_for('lygos_failure', _external=True)
    }
    
    response = requests.post('https://api.lygosapp.com/v1/products', 
                           json=payload, headers=headers)
    
    if response.status_code == 200:
        return redirect(response.json()['payment_url'])

# Gestion du succès
@app.route('/premium/lygos/success')
def lygos_success():
    # Activation automatique du Premium
    current_user.is_premium = True
    current_user.premium_end_date = datetime.utcnow() + timedelta(days=months * 30)
    db.session.commit()

# Webhook pour confirmation
@app.route('/api/lygos/webhook', methods=['POST'])
def lygos_webhook():
    # Traitement des notifications Lygos
    webhook_data = request.get_json()
    if webhook_data.get('status') == 'completed':
        # Activer le Premium pour l'utilisateur
        user.is_premium = True
        db.session.commit()
```

## Méthodes de paiement supportées

### Mobile Money
- **Orange Money** (Côte d'Ivoire, Mali, Sénégal, etc.)
- **MTN Mobile Money** (Ghana, Ouganda, Rwanda, etc.)
- **Moov Money** (Bénin, Burkina Faso, etc.)
- **Airtel Money** (Kenya, Tanzanie, etc.)

### Autres méthodes
- **Cartes bancaires** : Visa, Mastercard
- **Virements bancaires** : Banques locales africaines
- **Portefeuilles numériques** : Selon le pays

## Test de l'intégration

### Mode test
1. **Utiliser une clé API de test**
   ```
   LYGOS_API_KEY="lygos_test_xxxxxxxxxxxxx"
   ```

2. **Tester les paiements**
   - Utiliser les numéros de test fournis par Lygos
   - Vérifier les webhooks de confirmation
   - Valider l'activation du Premium

### Mode production
1. **Basculer vers la clé API live**
   ```
   LYGOS_API_KEY="lygos_live_xxxxxxxxxxxxx"
   ```

2. **Tester avec de vrais paiements**
   - Commencer par de petits montants
   - Vérifier tous les cas de figure
   - Monitorer les logs de transaction

## Monitoring et support

### Dashboard Lygos
- **Transactions** : Voir toutes les transactions en temps réel
- **Statistiques** : Revenus, taux de conversion, etc.
- **Rapports** : Exports CSV/PDF des transactions
- **Support** : Chat direct avec l'équipe Lygos

### Logs Congo Connect
- Tous les paiements sont enregistrés dans la table `premium_requests`
- Statuts : `pending`, `approved`, `rejected`
- Méthode : `lygos` pour identifier les paiements Lygos
- Référence : ID de transaction Lygos pour traçabilité

## Sécurité

### Bonnes pratiques
1. **Ne jamais exposer votre clé API**
   - Toujours en variable d'environnement
   - Jamais dans le code source
   - Différentes clés pour test/production

2. **Vérifier les webhooks**
   - Implémenter la vérification de signature (recommandé)
   - Valider l'origine des requêtes
   - Logs des tentatives de fraude

3. **Monitoring**
   - Surveiller les transactions suspectes
   - Alertes en cas d'échec répétés
   - Rapports réguliers des revenus

## Support technique

### Documentation officielle
- **API Reference** : [docs.lygosapp.com](https://docs.lygosapp.com/api-reference/introduction)
- **Guide d'intégration** : Disponible en français
- **Exemples de code** : JavaScript, Python, PHP

### Support Lygos
- **Email** : support@lygosapp.com
- **Chat** : Disponible sur le dashboard
- **Téléphone** : Numéros locaux dans chaque pays

### Support Congo Connect
- **Email** : support@congoconnect.com
- **Documentation** : Ce guide d'intégration
- **Github** : Issues et contributions

---

## Résumé

Lygos est maintenant parfaitement intégré à Congo Connect avec :
✅ **3 plans Premium** avec tarification flexible
✅ **Boutons de paiement** sur la page d'upgrade
✅ **Gestion automatique** des confirmations de paiement
✅ **Webhooks** pour les notifications en temps réel
✅ **Support multi-pays** et multi-opérateurs
✅ **Interface sécurisée** et conformes aux standards

L'intégration est **plug-and-play** : il suffit d'ajouter votre clé API Lygos et le système est opérationnel !