#!/bin/bash

# Script pour ajouter les nouveaux endpoints au serveur API
# Date: $(date)

echo "🔧 Ajout des nouveaux endpoints à l'API"
echo "======================================"

# Variables
PROJECT_PATH="/home/ubuntu/trendtrack-scraper-final"
SERVER_FILE="$PROJECT_PATH/src/api/server.js"
NEW_ENDPOINTS_FILE="$PROJECT_PATH/new_endpoints.js"
BACKUP_FILE="$PROJECT_PATH/src/api/server_backup_before_new_endpoints_$(date +%Y%m%d_%H%M%S).js"

echo "📋 Étape 1: Sauvegarde du serveur actuel..."
cp "$SERVER_FILE" "$BACKUP_FILE"
echo "✅ Sauvegarde créée: $(basename $BACKUP_FILE)"

echo ""
echo "🔍 Étape 2: Recherche de l'endroit d'insertion..."
# Trouver la ligne où insérer les nouveaux endpoints (après /shops/with-analytics)
INSERT_LINE=$(grep -n "// Top boutiques par Live Ads" "$SERVER_FILE" | cut -d: -f1)

if [ -z "$INSERT_LINE" ]; then
    echo "❌ Impossible de trouver l'endroit d'insertion"
    exit 1
fi

echo "✅ Ligne d'insertion trouvée: $INSERT_LINE"

echo ""
echo "🛠️  Étape 3: Ajout des nouveaux endpoints..."

# Créer un fichier temporaire avec les nouveaux endpoints
cat > /tmp/new_endpoints_content.js << 'EOF'
    // Nouveau endpoint: Liste des shops completed avec analytics
    router.get('/shops/completed', async (req, res) => {
      try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 30;
        const offset = (page - 1) * limit;
        
        // Récupérer les shops avec status 'completed' et leurs analytics
        const shopsStmt = this.dbManager.db.prepare(`
          SELECT s.shop_url, a.organic_traffic, a.bounce_rate, a.avg_visit_duration, 
                 a.branded_traffic, a.conversion_rate
          FROM shops s
          LEFT JOIN analytics a ON s.id = a.shop_id
          WHERE s.scraping_status = 'completed'
          ORDER BY s.id DESC
          LIMIT ? OFFSET ?
        `);
        
        const shops = shopsStmt.all(limit, offset);
        
        // Récupérer le total pour la pagination
        const totalStmt = this.dbManager.db.prepare(`
          SELECT COUNT(*) as total FROM shops WHERE scraping_status = 'completed'
        `);
        const total = totalStmt.get().total;
        
        res.json({
          success: true,
          data: shops,
          pagination: {
            page,
            limit,
            total,
            totalPages: Math.ceil(total / limit)
          }
        });
      } catch (error) {
        console.error('❌ Erreur récupération shops completed:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Nouveau endpoint: Détails d'un shop spécifique
    router.get('/shops/:shop_url', async (req, res) => {
      try {
        const { shop_url } = req.params;
        
        // Récupérer le shop et vérifier son status
        const shopStmt = this.dbManager.db.prepare(`
          SELECT s.shop_url, s.scraping_status, a.organic_traffic, a.bounce_rate, 
                 a.avg_visit_duration, a.branded_traffic, a.conversion_rate
          FROM shops s
          LEFT JOIN analytics a ON s.id = a.shop_id
          WHERE s.shop_url = ?
        `);
        
        const shop = shopStmt.get(shop_url);
        
        if (!shop) {
          return res.status(404).json({ success: false, error: 'Shop non trouvé' });
        }
        
        if (shop.scraping_status !== 'completed') {
          return res.json({
            success: false,
            error: `status = ${shop.scraping_status}`
          });
        }
        
        // Retourner les données sans le scraping_status
        const { scraping_status, ...shopData } = shop;
        res.json({
          success: true,
          data: shopData
        });
      } catch (error) {
        console.error('❌ Erreur récupération shop spécifique:', error.message);
        res.status(500).json({ success: false, error: error.message });
      }
    });

EOF

# Insérer les nouveaux endpoints avant la ligne "Top boutiques par Live Ads"
head -n $((INSERT_LINE - 1)) "$SERVER_FILE" > /tmp/server_part1.js
cat /tmp/new_endpoints_content.js >> /tmp/server_part1.js
tail -n +$INSERT_LINE "$SERVER_FILE" >> /tmp/server_part1.js

# Remplacer le fichier original
mv /tmp/server_part1.js "$SERVER_FILE"

echo ""
echo "✅ Étape 4: Vérification de l'ajout..."
if grep -q "/shops/completed" "$SERVER_FILE" && grep -q "/shops/:shop_url" "$SERVER_FILE"; then
    echo "✅ Nouveaux endpoints ajoutés avec succès!"
else
    echo "❌ Erreur lors de l'ajout des endpoints"
    exit 1
fi

echo ""
echo "🎯 Nouveaux endpoints disponibles:"
echo "   - GET /api/shops/completed?page=1&limit=30"
echo "   - GET /api/shops/{shop_url}"
echo ""
echo "📁 Sauvegarde: $(basename $BACKUP_FILE)"
