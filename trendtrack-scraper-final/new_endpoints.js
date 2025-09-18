// Nouveaux endpoints pour l'API TrendTrack

// Endpoint 1: Liste des shops completed avec analytics
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

// Endpoint 2: Détails d'un shop spécifique
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
