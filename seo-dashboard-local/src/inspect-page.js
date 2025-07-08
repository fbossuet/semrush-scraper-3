import { NoxToolsScraper } from './noxtools-scraper.js';
import { config } from './config.js';

class PageInspector extends NoxToolsScraper {
  
  async inspectAnalyticsPage() {
    console.log('🔍 INSPECTION DÉTAILLÉE DE LA PAGE ANALYTICS');
    console.log('═══════════════════════════════════════════════════');
    
    try {
      // Récupérer tous les éléments textuels de la page
      console.log('\n📄 CONTENU TEXTUEL DE LA PAGE:');
      const allText = await this.page.evaluate(() => {
        return document.body.innerText;
      });
      console.log(allText.slice(0, 500) + '...');
      
      // Identifier les tableaux
      console.log('\n📋 TABLEAUX TROUVÉS:');
      const tables = await this.page.$$('table');
      console.log(`Nombre de tableaux: ${tables.length}`);
      
      for (let i = 0; i < tables.length && i < 3; i++) {
        const tableText = await tables[i].textContent();
        console.log(`Table ${i + 1}: ${tableText.slice(0, 100)}...`);
      }
      
      // Identifier les listes et métriques
      console.log('\n📊 ÉLÉMENTS AVEC CHIFFRES:');
      const numberElements = await this.page.$$eval('*', elements => {
        return elements
          .filter(el => /\d+/.test(el.textContent) && el.children.length === 0)
          .slice(0, 10)
          .map(el => ({
            tag: el.tagName,
            class: el.className,
            text: el.textContent.trim()
          }));
      });
      
      numberElements.forEach((el, i) => {
        console.log(`${i + 1}. <${el.tag}> ${el.class ? `class="${el.class}"` : ''}: "${el.text}"`);
      });
      
      // Identifier les divs principales
      console.log('\n📦 DIVS PRINCIPALES:');
      const mainDivs = await this.page.$$eval('div[class*="container"], div[class*="wrapper"], div[class*="content"], div[id]', divs => {
        return divs.slice(0, 10).map(div => ({
          id: div.id,
          class: div.className,
          text: div.textContent.slice(0, 50).trim()
        }));
      });
      
      mainDivs.forEach((div, i) => {
        console.log(`${i + 1}. ID:"${div.id}" CLASS:"${div.class}" → "${div.text}..."`);
      });
      
      // Identifier les liens
      console.log('\n🔗 LIENS TROUVÉS:');
      const links = await this.page.$$eval('a[href]', links => {
        return links.slice(0, 10).map(link => ({
          href: link.href,
          text: link.textContent.trim()
        }));
      });
      
      links.forEach((link, i) => {
        console.log(`${i + 1}. "${link.text}" → ${link.href}`);
      });
      
      // Structure HTML globale
      console.log('\n🏗️  STRUCTURE HTML:');
      const structure = await this.page.evaluate(() => {
        const getStructure = (element, depth = 0) => {
          if (depth > 3) return '';
          
          let result = '  '.repeat(depth) + `<${element.tagName.toLowerCase()}`;
          if (element.id) result += ` id="${element.id}"`;
          if (element.className) result += ` class="${element.className}"`;
          result += '>\n';
          
          Array.from(element.children).slice(0, 5).forEach(child => {
            result += getStructure(child, depth + 1);
          });
          
          return result;
        };
        
        return getStructure(document.body);
      });
      
      console.log(structure.slice(0, 1000) + '...');
      
    } catch (error) {
      console.error('❌ Erreur inspection:', error.message);
    }
  }
  
  async suggestSelectors() {
    console.log('\n💡 SUGGESTIONS DE SÉLECTEURS:');
    console.log('═══════════════════════════════════════');
    
    // Essayer différents sélecteurs pour les métriques
    const potentialSelectors = [
      // Métriques générales
      '.metric', '.stat', '.number', '.value',
      '[data-metric]', '[data-value]', '[data-stat]',
      
      // Tableaux
      'table tr', 'tbody tr', '.data-row', '.table-row',
      
      // Analytics spécifiques
      '.traffic-metric', '.seo-metric', '.overview-stat',
      '.domain-stat', '.keyword-stat', '.backlink-stat',
      
      // Conteneurs
      '.analytics-data', '.overview-data', '.dashboard-widget',
      '.widget', '.panel', '.card',
      
      // Textes et titres
      'h1, h2, h3', '.title', '.heading', '.label'
    ];
    
    for (const selector of potentialSelectors) {
      try {
        const elements = await this.page.$$(selector);
        if (elements.length > 0) {
          console.log(`✅ "${selector}" → ${elements.length} élément(s)`);
          
          // Afficher aperçu du premier élément
          const firstText = await elements[0].textContent();
          if (firstText.trim()) {
            console.log(`   📝 Exemple: "${firstText.trim().slice(0, 50)}..."`);
          }
        }
      } catch (e) {
        // Sélecteur invalide, continuer
      }
    }
  }
}

async function runInspection() {
  const inspector = new PageInspector();
  
  try {
    await inspector.init();
    
    // Workflow standard pour arriver sur analytics
    const loginSuccess = await inspector.connectToNoxTools();
    if (!loginSuccess) throw new Error('Connexion échouée');
    
    const navSuccess = await inspector.navigateToFinalSite();
    if (!navSuccess) throw new Error('Navigation échouée');
    
    await inspector.waitForFinalSiteLoading();
    
    // Inspection détaillée
    await inspector.inspectAnalyticsPage();
    await inspector.suggestSelectors();
    
    console.log('\n🎯 INSPECTION TERMINÉE !');
    console.log('Utilise ces informations pour améliorer les sélecteurs dans config.js');
    
  } catch (error) {
    console.error('💥 Erreur inspection:', error.message);
  } finally {
    await inspector.close();
  }
}

export { PageInspector, runInspection };

if (import.meta.url === `file://${process.argv[1]}`) {
  runInspection();
}