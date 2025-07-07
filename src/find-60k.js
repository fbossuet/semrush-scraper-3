import fs from 'fs';

function findSpecificValue(filePath, searchValue = '60.1k') {
  console.log(`🔍 Recherche de "${searchValue}" dans ${filePath}...`);
  console.log('═══════════════════════════════════════════════════');
  
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const results = [];
    
    // Fonction récursive pour chercher dans toute la structure
    function searchInObject(obj, path = '') {
      if (typeof obj === 'string') {
        // Chercher la valeur exacte
        if (obj.includes(searchValue)) {
          results.push({
            path: path,
            content: obj.substring(Math.max(0, obj.indexOf(searchValue) - 50), obj.indexOf(searchValue) + 100),
            fullContent: obj
          });
        }
        
        // Chercher aussi des variations
        const variations = [
          '60.1K', '60.1k', '60,1k', '60,1K', 
          '60.1 K', '60.1 k', '60,1 k', '60,1 K',
          'traffic 60.1', 'traffic: 60.1', 'organic 60.1'
        ];
        
        variations.forEach(variation => {
          if (obj.includes(variation)) {
            results.push({
              path: path,
              variation: variation,
              content: obj.substring(Math.max(0, obj.indexOf(variation) - 50), obj.indexOf(variation) + 100),
              fullContent: obj
            });
          }
        });
        
      } else if (Array.isArray(obj)) {
        obj.forEach((item, index) => {
          searchInObject(item, `${path}[${index}]`);
        });
      } else if (obj && typeof obj === 'object') {
        Object.entries(obj).forEach(([key, value]) => {
          searchInObject(value, path ? `${path}.${key}` : key);
        });
      }
    }
    
    searchInObject(data);
    
    console.log(`\n📊 RÉSULTATS POUR "${searchValue}":`);
    
    if (results.length > 0) {
      results.forEach((result, index) => {
        console.log(`\n🎯 CORRESPONDANCE ${index + 1}:`);
        console.log(`   📂 Chemin: ${result.path}`);
        if (result.variation) {
          console.log(`   🔸 Variation trouvée: ${result.variation}`);
        }
        console.log(`   📝 Contexte: ...${result.content}...`);
        console.log(`   📄 Longueur contenu complet: ${result.fullContent.length} caractères`);
      });
    } else {
      console.log('❌ Valeur non trouvée');
      
      // Recherche élargie de tous les nombres proches
      console.log('\n🔍 RECHERCHE ÉLARGIE DE NOMBRES SIMILAIRES:');
      const allText = JSON.stringify(data);
      
      // Chercher d'autres nombres avec K
      const numberPattern = /\b(\d+\.?\d*)\s*[Kk]\b/g;
      const matches = [...allText.matchAll(numberPattern)];
      
      if (matches.length > 0) {
        console.log('   📊 Nombres avec K trouvés:');
        matches.forEach(match => {
          console.log(`      • ${match[0]}`);
        });
      }
      
      // Chercher spécifiquement autour de 60
      const sixtyPattern = /\b6\d+\.?\d*[Kk]?\b/g;
      const sixtyMatches = [...allText.matchAll(sixtyPattern)];
      
      if (sixtyMatches.length > 0) {
        console.log('   🎯 Nombres commençant par 6:');
        sixtyMatches.forEach(match => {
          console.log(`      • ${match[0]}`);
        });
      }
    }
    
    return results;
    
  } catch (error) {
    console.error('❌ Erreur:', error.message);
    return [];
  }
}

// Recherche dans le fichier le plus récent
function searchInLatestFile(searchValue = '60.1k') {
  console.log('🔍 Recherche dans le fichier le plus récent...\n');
  
  const files = fs.readdirSync('.')
    .filter(file => file.startsWith('analytics-') && file.endsWith('.json'))
    .sort((a, b) => {
      const timeA = fs.statSync(a).mtime;
      const timeB = fs.statSync(b).mtime;
      return timeB - timeA;
    });
  
  if (files.length === 0) {
    console.log('❌ Aucun fichier analytics trouvé');
    return;
  }
  
  const latestFile = files[0];
  console.log(`📂 Fichier: ${latestFile}\n`);
  
  return findSpecificValue(latestFile, searchValue);
}

// Recherche de tout ce qui contient "organic" et un nombre
function findOrganicTraffic(filePath) {
  console.log(`🌱 Recherche de métriques organiques dans ${filePath}...`);
  console.log('═══════════════════════════════════════════════════');
  
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const allText = JSON.stringify(data, null, 2);
    
    // Patterns pour organic traffic
    const organicPatterns = [
      /organic[^0-9]*(\d+\.?\d*\s*[KMkm]?)/gi,
      /organic\s+traffic[^0-9]*(\d+\.?\d*\s*[KMkm]?)/gi,
      /organic\s+search[^0-9]*(\d+\.?\d*\s*[KMkm]?)/gi,
      /traffic[^0-9]*(\d+\.?\d*\s*[KMkm]?)/gi
    ];
    
    console.log('\n🎯 RECHERCHE ORGANIC TRAFFIC:');
    
    organicPatterns.forEach((pattern, index) => {
      const matches = [...allText.matchAll(pattern)];
      if (matches.length > 0) {
        console.log(`\n   Pattern ${index + 1}: ${pattern.source}`);
        matches.forEach(match => {
          console.log(`      🔸 ${match[0]} → Valeur: ${match[1]}`);
        });
      }
    });
    
  } catch (error) {
    console.error('❌ Erreur:', error.message);
  }
}

// Script principal
if (import.meta.url === `file://${process.argv[1]}`) {
  const filePath = process.argv[2];
  const searchValue = process.argv[3] || '60.1k';
  
  if (filePath) {
    findSpecificValue(filePath, searchValue);
    console.log('\n' + '='.repeat(60));
    findOrganicTraffic(filePath);
  } else {
    searchInLatestFile(searchValue);
  }
}

export { findSpecificValue, searchInLatestFile, findOrganicTraffic };