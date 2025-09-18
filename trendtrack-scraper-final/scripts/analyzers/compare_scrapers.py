#!/usr/bin/env python3
import os

def compare_scrapers():
    """Compare le scraper principal et le scraper intelligent"""
    
    print("🔍 COMPARAISON SCRAPER PRINCIPAL vs SCRAPER INTELLIGENT")
    print("=" * 60)
    
    # Chemins des fichiers
    main_scraper = "/home/ubuntu/sem-scraper-final/production_scraper.py"
    smart_scraper = "/home/ubuntu/trendtrack-scraper-final/scrape_smart_all.py"
    
    if not os.path.exists(main_scraper):
        print(f"❌ Scraper principal non trouvé: {main_scraper}")
        return
    
    if not os.path.exists(smart_scraper):
        print(f"❌ Scraper intelligent non trouvé: {smart_scraper}")
        return
    
    print("📊 ANALYSE DES DIFFÉRENCES...")
    print("-" * 40)
    
    # 1. COMPARAISON DES IMPORTS
    print("\n1️⃣ IMPORTS:")
    print("-" * 20)
    
    with open(main_scraper, 'r') as f:
        main_content = f.read()
    
    with open(smart_scraper, 'r') as f:
        smart_content = f.read()
    
    # Imports du scraper principal
    main_imports = [line.strip() for line in main_content.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
    print("📦 Scraper principal - Imports:")
    for imp in main_imports[:10]:
        print(f"   {imp}")
    
    # Imports du scraper intelligent
    smart_imports = [line.strip() for line in smart_content.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
    print("\n📦 Scraper intelligent - Imports:")
    for imp in smart_imports[:10]:
        print(f"   {imp}")
    
    # 2. COMPARAISON DES URLS
    print("\n2️⃣ URLS ET DOMAINES:")
    print("-" * 20)
    
    # URLs dans le scraper principal
    main_urls = [line.strip() for line in main_content.split('\n') if 'mytoolsplan' in line and 'http' in line]
    print("🌐 Scraper principal - URLs:")
    for url in main_urls[:5]:
        print(f"   {url}")
    
    # URLs dans le scraper intelligent
    smart_urls = [line.strip() for line in smart_content.split('\n') if 'mytoolsplan' in line and 'http' in line]
    print("\n🌐 Scraper intelligent - URLs:")
    for url in smart_urls[:5]:
        print(f"   {url}")
    
    # 3. COMPARAISON DES SÉLECTEURS
    print("\n3️⃣ SÉLECTEURS:")
    print("-" * 20)
    
    # Sélecteurs dans le scraper principal
    main_selectors = [line.strip() for line in main_content.split('\n') if 'wait_for_selector' in line or 'query_selector' in line or 'fill(' in line]
    print("🎯 Scraper principal - Sélecteurs:")
    for sel in main_selectors[:8]:
        print(f"   {sel}")
    
    # Sélecteurs dans le scraper intelligent
    smart_selectors = [line.strip() for line in smart_content.split('\n') if 'wait_for_selector' in line or 'query_selector' in line or 'fill(' in line]
    print("\n🎯 Scraper intelligent - Sélecteurs:")
    for sel in smart_selectors[:8]:
        print(f"   {sel}")
    
    # 4. COMPARAISON DES MÉTRIQUES
    print("\n4️⃣ MÉTRIQUES ET LOGIQUE:")
    print("-" * 20)
    
    # Métriques dans le scraper principal
    main_metrics = [line.strip() for line in main_content.split('\n') if 'organic_traffic' in line or 'bounce_rate' in line or 'paid_search_traffic' in line]
    print("📊 Scraper principal - Métriques:")
    for met in main_metrics[:5]:
        print(f"   {met}")
    
    # Métriques dans le scraper intelligent
    smart_metrics = [line.strip() for line in smart_content.split('\n') if 'organic_traffic' in line or 'bounce_rate' in line or 'paid_search_traffic' in line]
    print("\n📊 Scraper intelligent - Métriques:")
    for met in smart_metrics[:5]:
        print(f"   {met}")
    
    # 5. COMPARAISON DES FONCTIONS
    print("\n5️⃣ FONCTIONS:")
    print("-" * 20)
    
    # Fonctions dans le scraper principal
    main_functions = [line.strip() for line in main_content.split('\n') if line.strip().startswith('def ')]
    print("🔧 Scraper principal - Fonctions:")
    for func in main_functions[:8]:
        print(f"   {func}")
    
    # Fonctions dans le scraper intelligent
    smart_functions = [line.strip() for line in smart_content.split('\n') if line.strip().startswith('def ')]
    print("\n🔧 Scraper intelligent - Fonctions:")
    for func in smart_functions[:8]:
        print(f"   {func}")
    
    # 6. COMPARAISON DES CONFIGURATIONS
    print("\n6️⃣ CONFIGURATIONS:")
    print("-" * 20)
    
    # Configurations dans le scraper principal
    main_config = [line.strip() for line in main_content.split('\n') if 'timeout' in line or 'headless' in line or 'args=' in line]
    print("⚙️ Scraper principal - Configurations:")
    for config in main_config[:5]:
        print(f"   {config}")
    
    # Configurations dans le scraper intelligent
    smart_config = [line.strip() for line in smart_content.split('\n') if 'timeout' in line or 'headless' in line or 'args=' in line]
    print("\n⚙️ Scraper intelligent - Configurations:")
    for config in smart_config[:5]:
        print(f"   {config}")
    
    print(f"\n🎯 COMPARAISON TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    compare_scrapers()
