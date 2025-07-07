import { NoxToolsScraper } from './noxtools-scraper.js';
import fs from 'fs';

class TrafficPageInspector extends NoxToolsScraper {
  
  async inspectTrafficOverview() {
    console.log('🔍 INSPECTION DÉTAILLÉE DE TRAFFIC OVERVIEW');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      await this.init();
      
      // Connexion
      const loginSuccess = await this.connectToNoxTools();
      if (!loginSuccess) throw new Error('Connexion échouée');
      
      // Navigation vers Traffic Overview
      console.log('🚗 Navigation vers Traffic Overview...');
      const trafficUrl = 'https://server1.noxtools.com/analytics/traffic/traffic-overview/';
      
      await this.page.goto(trafficUrl, { 
        waitUntil: 'domcontentloaded',
        timeout: 60000 
      });
      
      console.log('✅ Page chargée ! Analyse en cours...');
      
      // Attendre le chargement complet
      await this.page.waitForTimeout(8000);
      
      // 1. Tous les boutons de la page
      console.log('\n🔘 TOUS LES BOUTONS:');
      const buttons = await this.page.evaluate(() => {
        const allButtons = Array.from(document.querySelectorAll('button'));
        return allButtons.map(btn => ({
          text: btn.textContent?.trim(),
          className: btn.className,
          id: btn.id,
          title: btn.title,
          type: btn.type,
          innerHTML: btn.innerHTML?.substring(0, 100),
          style: btn.getAttribute('style')
        })).filter(btn => btn.text || btn.className || btn.innerHTML);
      });
      
      buttons.forEach((btn, index) => {
        console.log(`\n   Bouton ${index + 1}:`);
        console.log(`     📝 Texte: "${btn.text}"`);
        console.log(`     🎨 Classe: "${btn.className}"`);
        console.log(`     🆔 ID: "${btn.id}"`);
        console.log(`     📄 HTML: ${btn.innerHTML}`);
        if (btn.title) console.log(`     📋 Title: "${btn.title}"`);
      });
      
      // 2. Tous les inputs
      console.log('\n📝 TOUS LES INPUTS:');
      const inputs = await this.page.evaluate(() => {
        const allInputs = Array.from(document.querySelectorAll('input'));
        return allInputs.map(input => ({
          type: input.type,
          placeholder: input.placeholder,
          name: input.name,
          id: input.id,
          className: input.className,
          value: input.value
        }));
      });
      
      inputs.forEach((input, index) => {
        console.log(`\n   Input ${index + 1}:`);
        console.log(`     📝 Type: ${input.type}`);
        console.log(`     💭 Placeholder: "${input.placeholder}"`);
        console.log(`     🏷️ Name: "${input.name}"`);
        console.log(`     🎨 Classe: "${input.className}"`);
      });
      
      // 3. Structure générale de la page
      console.log('\n🏗️ STRUCTURE DE LA PAGE:');
      const pageStructure = await this.page.evaluate(() => {
        const body = document.body;
        const mainContainers = body.querySelectorAll('div[class*="container"], .main, .content, [id*="app"], [class*="traffic"]');
        
        return Array.from(mainContainers).map(container => ({
          tagName: container.tagName,
          className: container.className,
          id: container.id,
          textPreview: container.textContent?.substring(0, 200)
        }));
      });
      
      pageStructure.forEach((container, index) => {
        console.log(`\n   Container ${index + 1}:`);
        console.log(`     🏷️ Tag: ${container.tagName}`);
        console.log(`     🎨 Classe: "${container.className}"`);
        console.log(`     🆔 ID: "${container.id}"`);
        console.log(`     📝 Aperçu: ${container.textPreview}...`);
      });
      
      // 4. Chercher des éléments contenant "+" ou "add"
      console.log('\n➕ ÉLÉMENTS AVEC "+" OU "ADD":');
      const addElements = await this.page.evaluate(() => {
        const allElements = Array.from(document.querySelectorAll('*'));
        const addRelated = allElements.filter(el => {
          const text = el.textContent?.toLowerCase() || '';
          const className = el.className?.toLowerCase() || '';
          const id = el.id?.toLowerCase() || '';
          
          return text.includes('+') || text.includes('add') || 
                 className.includes('add') || className.includes('plus') ||
                 id.includes('add') || id.includes('plus');
        });
        
        return addRelated.map(el => ({
          tagName: el.tagName,
          text: el.textContent?.trim().substring(0, 100),
          className: el.className,
          id: el.id,
          innerHTML: el.innerHTML?.substring(0, 150)
        }));
      });
      
      addElements.forEach((el, index) => {
        console.log(`\n   Élément + ${index + 1}:`);
        console.log(`     🏷️ Tag: ${el.tagName}`);
        console.log(`     📝 Texte: "${el.text}"`);
        console.log(`     🎨 Classe: "${el.className}"`);
        console.log(`     📄 HTML: ${el.innerHTML}`);
      });
      
      // 5. Contenu textuel général
      console.log('\n📄 CONTENU TEXTUEL DE LA PAGE:');
      const pageText = await this.page.evaluate(() => {
        return document.body.textContent?.substring(0, 1000);
      });
      console.log(pageText);
      
      // 6. Sauvegarder l'HTML complet
      const htmlContent = await this.page.content();
      
      const inspection = {
        timestamp: new Date().toISOString(),
        url: trafficUrl,
        buttons,
        inputs,
        pageStructure,
        addElements,
        pageText,
        htmlContent
      };
      
      const filename = `traffic-page-inspection-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(inspection, null, 2));
      console.log(`\n💾 Inspection sauvegardée: ${filename}`);
      
      // Prendre une capture d'écran
      try {
        await this.page.screenshot({ 
          path: `traffic-overview-${Date.now()}.png`,
          fullPage: true 
        });
        console.log('📸 Capture d\'écran prise !');
      } catch (e) {
        console.log('⚠️ Impossible de prendre la capture');
      }
      
      return inspection;
      
    } catch (error) {
      console.error('💥 Erreur inspection:', error.message);
    } finally {
      await this.close();
    }
  }
}

async function inspectTrafficPage() {
  const inspector = new TrafficPageInspector();
  await inspector.inspectTrafficOverview();
}

export { TrafficPageInspector, inspectTrafficPage };

if (import.meta.url === `file://${process.argv[1]}`) {
  inspectTrafficPage();
}