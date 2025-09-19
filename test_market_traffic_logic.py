#!/usr/bin/env python3
"""
Test de la logique d'extraction du trafic par pays (sans Playwright)
"""

def test_extraction_logic():
    """Test la logique d'extraction avec des données simulées"""
    
    print("🧪 Test de la logique d'extraction du trafic par pays")
    
    # Simuler les données HTML que vous avez fournies
    simulated_html_data = {
        "US": {"visits": 609094, "percentage": 36},
        "AU": {"visits": 227940, "percentage": 13},
        "GB": {"visits": 161089, "percentage": 10},
        "CA": {"visits": 71044, "percentage": 4},
        "LV": {"visits": 33667, "percentage": 2}
    }
    
    # Logique d'extraction (simulée)
    market_data = {
        "market_us": None,
        "market_uk": None,
        "market_de": None,
        "market_ca": None,
        "market_au": None,
        "market_fr": None
    }
    
    # Mapper les données
    country_mapping = {
        "US": "market_us",
        "GB": "market_uk", 
        "DE": "market_de",
        "CA": "market_ca",
        "AU": "market_au",
        "FR": "market_fr"
    }
    
    for country_code, data in simulated_html_data.items():
        if country_code in country_mapping:
            market_key = country_mapping[country_code]
            # Convertir le pourcentage en décimal
            market_data[market_key] = data["percentage"] / 100
    
    print("📊 Résultats de l'extraction:")
    for key, value in market_data.items():
        if value is not None:
            print(f"  {key}: {value*100:.1f}%")
        else:
            print(f"  {key}: Non trouvé")
    
    # Vérifier les résultats attendus
    expected_results = {
        "market_us": 0.36,  # 36%
        "market_au": 0.13,  # 13%
        "market_uk": 0.10,  # 10% (GB)
        "market_ca": 0.04,  # 4%
        "market_de": None,  # Non présent
        "market_fr": None   # Non présent
    }
    
    print("\n🎯 Vérification des résultats:")
    all_correct = True
    for key, expected in expected_results.items():
        actual = market_data[key]
        if actual == expected:
            print(f"  ✅ {key}: {actual} (attendu: {expected})")
        else:
            print(f"  ❌ {key}: {actual} (attendu: {expected})")
            all_correct = False
    
    if all_correct:
        print("\n🎉 Tous les tests sont passés ! La logique d'extraction est correcte.")
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez la logique d'extraction.")
    
    return all_correct

if __name__ == "__main__":
    test_extraction_logic()