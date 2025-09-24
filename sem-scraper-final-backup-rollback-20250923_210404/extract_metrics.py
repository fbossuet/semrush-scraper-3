#!/usr/bin/env python3
import re

log_file = 'logs/smart-partial_20250906_163012.log'

total_metriques_manquantes = 0
total_metriques_trouvees = 0
boutiques_completed = 0
boutiques_partial = 0

with open(log_file, 'r') as f:
    content = f.read()

# Rechercher toutes les métriques manquantes
metriques_manquantes_pattern = r'métriques manquantes: ([^\n]+)'
matches = re.findall(metriques_manquantes_pattern, content)

for match in matches:
    metriques_list = [m.strip() for m in match.split(',')]
    total_metriques_manquantes += len(metriques_list)

# Rechercher les statuts
boutiques_partial = len(re.findall(r'statut: partial', content))
boutiques_completed = len(re.findall(r'statut: completed', content))

# Calcul des métriques récupérées (approximation)
# 7 métriques possibles par boutique - métriques manquantes = métriques récupérées
boutiques_traitees = boutiques_partial + boutiques_completed
if boutiques_traitees > 0:
    metriques_possibles = boutiques_traitees * 7
    total_metriques_trouvees = metriques_possibles - total_metriques_manquantes
else:
    total_metriques_trouvees = 0

print("📊 ANALYSE MÉTRIQUES:")
print(f - Métriques récupérées: {total_metriques_trouvees})  
print(f - Métriques manquantes: {total_metriques_manquantes})
if total_metriques_manquantes + total_metriques_trouvees > 0:
    ratio = (total_metriques_trouvees * 100) // (total_metriques_trouvees + total_metriques_manquantes)
    print(f - Ratio récupération: {ratio}%)
print(f\n📈 STATUTS BOUTIQUES:)
print(f - Boutiques completed: {boutiques_completed})
print(f - Boutiques partial: {boutiques_partial})
print(f - Total traitées: {boutiques_traitees})
