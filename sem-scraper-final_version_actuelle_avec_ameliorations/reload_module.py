#!/usr/bin/env python3
import sys
import importlib

# Recharger le module trendtrack_api_vps_adapted
if trendtrack_api_vps_adapted in sys.modules:
    importlib.reload(sys.modules[trendtrack_api_vps_adapted])
    print("✅ Module rechargé avec succès")
else:
    print("❌ Module non trouvé dans sys.modules")

# Tester la méthode
try:
    from trendtrack_api import api
    result = api.get_shop_analytics(12)
    print(f"🚦 Test après rechargement: {result.get(paid_search_traffic)}")
except Exception as e:
    print(f"❌ Erreur après rechargement: {e}")

