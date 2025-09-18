#!/usr/bin/env python3
import re

# Lire le fichier
with open('/tmp/trendtrack-extractor.js', 'r') as f:
    content = f.read()

# Code à ajouter
products_extraction_code = '''
      // 🆕 Extraction directe du nombre de produits (colonne 2)
      try {
        const productsCell = cells[2]; // 3ème colonne (index 2)
        const productsP = productsCell.locator('p:has(> span:has-text("products"))');
        const productsText = await productsP.textContent();
        if (productsText) {
          const match = productsText.match(/\\d[\\d\\s.,]*/);
          shopData.totalProducts = match ? Number(match[0].replace(/[^\\d]/g, "")) : null;
          console.log(`📦 Produits extraits pour ${shopData.shopName}: ${shopData.totalProducts}`);
        } else {
          shopData.totalProducts = null;
        }
      } catch (error) {
        console.error(`⚠️ Erreur extraction produits pour ${shopData.shopName}:`, error.message);
        shopData.totalProducts = null;
      }

'''

# Trouver la ligne à remplacer
pattern = r"(shopData\.liveAds = liveAdsP \? \(await liveAdsP\.textContent\(\)\)\.trim\(\) : '';)\s*"
replacement = r"\1" + products_extraction_code

# Appliquer le remplacement
new_content = re.sub(pattern, replacement, content)

# Écrire le fichier modifié
with open('/tmp/trendtrack-extractor-fixed.js', 'w') as f:
    f.write(new_content)

print("✅ Fichier modifié avec succès")