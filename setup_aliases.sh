#!/bin/bash
# Script pour configurer des alias utiles

echo "🔧 Configuration des alias pour le workspace test..."

# Ajouter les alias au fichier .bashrc
cat >> ~/.bashrc << 'EOF'

# Aliases pour le workspace test
alias test-workspace="cd /home/ubuntu/projects/shopshopshops/test"
alias test-cursor="cd /home/ubuntu/projects/shopshopshops/test && cursor ."
alias test-check="./check_workspace.sh"
alias test-api="cd /home/ubuntu/projects/shopshopshops/test/sem-scraper-final && python3 api_server.py"

EOF

echo "✅ Aliases ajoutés au .bashrc"
echo ""
echo "📋 Nouveaux alias disponibles:"
echo "   test-workspace  - Aller dans le répertoire test"
echo "   test-cursor     - Ouvrir Cursor dans le répertoire test"
echo "   test-check      - Vérifier le workspace"
echo "   test-api        - Démarrer l'API"
echo ""
echo "💡 Redémarrez votre terminal ou exécutez: source ~/.bashrc"
