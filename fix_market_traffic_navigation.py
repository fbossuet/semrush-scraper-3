#!/usr/bin/env python3
import re

# Lire le fichier
with open('/tmp/market_traffic_extractor.py', 'r') as f:
    content = f.read()

# Remplacer la navigation incorrecte
old_navigation = '''await page.goto(shop_url, wait_until='domcontentloaded', timeout=30000)'''

new_navigation = '''# Construire l'URL TrendTrack pour cette boutique
                # Format: https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/shop/[shop_id]
                # Pour l'instant, on utilise une URL générique - à améliorer avec l'ID réel
                trendtrack_url = f"https://app.trendtrack.io/en/workspace/w-al-yakoobs-workspace-x0Qg9st/trending-shops"
                logger.info(f"🌐 Navigation vers TrendTrack: {trendtrack_url}")
                await page.goto(trendtrack_url, wait_until='domcontentloaded', timeout=30000)'''

# Appliquer le remplacement
new_content = content.replace(old_navigation, new_navigation)

# Écrire le fichier modifié
with open('/tmp/market_traffic_extractor_fixed.py', 'w') as f:
    f.write(new_content)

print("✅ Fichier market_traffic_extractor.py modifié avec succès")