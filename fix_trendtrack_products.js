// 🆕 Extraction directe du nombre de produits (colonne 2)
      try {
        const productsCell = cells[2]; // 3ème colonne (index 2)
        const productsP = productsCell.locator('p:has(> span:has-text("products"))');
        const productsText = await productsP.textContent();
        if (productsText) {
          const match = productsText.match(/\d[\d\s.,]*/);
          shopData.totalProducts = match ? Number(match[0].replace(/[^\d]/g, "")) : null;
          console.log(`📦 Produits extraits pour ${shopData.shopName}: ${shopData.totalProducts}`);
        } else {
          shopData.totalProducts = null;
        }
      } catch (error) {
        console.error(`⚠️ Erreur extraction produits pour ${shopData.shopName}:`, error.message);
        shopData.totalProducts = null;
      }

      // Ajouter les données de trafic par pays si demandé