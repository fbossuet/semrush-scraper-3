#!/bin/bash

# Script de vérification et installation des dépendances TrendTrack Scraper
# Usage: ./check-dependencies.sh

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Vérification des dépendances TrendTrack Scraper${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Variables
MISSING_DEPS=()
MISSING_SYSTEM_DEPS=()
NODE_VERSION_REQUIRED="18.0.0"
NPM_VERSION_REQUIRED="8.0.0"

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Fonction pour comparer les versions
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

# Fonction pour vérifier si une version est supérieure ou égale
version_gte() {
    version_compare "$1" "$2"
    local result=$?
    if [ $result -eq 0 ] || [ $result -eq 1 ]; then
        return 0  # Version actuelle >= version requise
    else
        return 1  # Version actuelle < version requise
    fi
}

# Fonction pour afficher le statut
show_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
    fi
}

echo -e "${CYAN}📋 VÉRIFICATION DES PRÉREQUIS SYSTÈME${NC}"
echo -e "${CYAN}=====================================${NC}"

# 1. Vérifier Node.js
echo -n "🔍 Node.js: "
if command_exists node; then
    NODE_VERSION=$(node --version | sed 's/v//')
    if version_gte "$NODE_VERSION" "$NODE_VERSION_REQUIRED"; then
        show_status "OK" "Node.js v$NODE_VERSION (requis: v$NODE_VERSION_REQUIRED+)"
    else
        show_status "WARNING" "Node.js v$NODE_VERSION (requis: v$NODE_VERSION_REQUIRED+)"
        MISSING_SYSTEM_DEPS+=("Node.js v$NODE_VERSION_REQUIRED+")
    fi
else
    show_status "ERROR" "Node.js non installé"
    MISSING_SYSTEM_DEPS+=("Node.js v$NODE_VERSION_REQUIRED+")
fi

# 2. Vérifier npm
echo -n "🔍 npm: "
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    if version_gte "$NPM_VERSION" "$NPM_VERSION_REQUIRED"; then
        show_status "OK" "npm v$NPM_VERSION (requis: v$NPM_VERSION_REQUIRED+)"
    else
        show_status "WARNING" "npm v$NPM_VERSION (requis: v$NPM_VERSION_REQUIRED+)"
        MISSING_SYSTEM_DEPS+=("npm v$NPM_VERSION_REQUIRED+")
    fi
else
    show_status "ERROR" "npm non installé"
    MISSING_SYSTEM_DEPS+=("npm v$NPM_VERSION_REQUIRED+")
fi

# 3. Vérifier Git
echo -n "🔍 Git: "
if command_exists git; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    show_status "OK" "Git v$GIT_VERSION"
else
    show_status "WARNING" "Git non installé (recommandé pour le développement)"
    MISSING_SYSTEM_DEPS+=("Git")
fi

# 4. Vérifier un navigateur Chrome/Chromium
echo -n "🔍 Navigateur Chrome/Chromium: "
CHROME_FOUND=false

# Vérifier Google Chrome sur macOS
if [ -d "/Applications/Google Chrome.app" ]; then
    show_status "OK" "Google Chrome installé"
    CHROME_FOUND=true
elif command_exists google-chrome; then
    show_status "OK" "Google Chrome installé"
    CHROME_FOUND=true
elif command_exists chromium; then
    show_status "OK" "Chromium installé"
    CHROME_FOUND=true
elif command_exists chromium-browser; then
    show_status "OK" "Chromium installé"
    CHROME_FOUND=true
fi

if [ "$CHROME_FOUND" = false ]; then
    show_status "WARNING" "Chrome/Chromium non trouvé (Playwright peut installer ses propres navigateurs)"
    MISSING_SYSTEM_DEPS+=("Chrome/Chromium (optionnel)")
fi

echo -e "\n${CYAN}📦 VÉRIFICATION DES DÉPENDANCES NODE.JS${NC}"
echo -e "${CYAN}=====================================${NC}"

# Vérifier si node_modules existe
if [ ! -d "node_modules" ]; then
    show_status "ERROR" "node_modules manquant - installation nécessaire"
    MISSING_DEPS+=("node_modules")
else
    show_status "OK" "node_modules présent"
fi

# Vérifier package-lock.json
if [ ! -f "package-lock.json" ]; then
    show_status "WARNING" "package-lock.json manquant"
    MISSING_DEPS+=("package-lock.json")
else
    show_status "OK" "package-lock.json présent"
fi

# Vérifier les dépendances spécifiques
echo -e "\n${PURPLE}🔍 VÉRIFICATION DES DÉPENDANCES SPÉCIFIQUES${NC}"
echo -e "${PURPLE}=============================================${NC}"

# Dépendances principales
MAIN_DEPS=(
    "@playwright/test"
    "better-sqlite3"
    "compression"
    "cors"
    "express"
    "sqlite"
)

# Dépendances de développement
DEV_DEPS=(
    "playwright"
)

# Vérifier les dépendances principales
for dep in "${MAIN_DEPS[@]}"; do
    echo -n "🔍 $dep: "
    if [ -d "node_modules/$dep" ]; then
        show_status "OK" "Installé"
    else
        show_status "ERROR" "Manquant"
        MISSING_DEPS+=("$dep")
    fi
done

# Vérifier les dépendances de développement
for dep in "${DEV_DEPS[@]}"; do
    echo -n "🔍 $dep (dev): "
    if [ -d "node_modules/$dep" ]; then
        show_status "OK" "Installé"
    else
        show_status "ERROR" "Manquant"
        MISSING_DEPS+=("$dep")
    fi
done

echo -e "\n${CYAN}🔧 VÉRIFICATION DES NAVIGATEURS PLAYWRIGHT${NC}"
echo -e "${CYAN}===========================================${NC}"

# Vérifier si Playwright a installé ses navigateurs
PLAYWRIGHT_BROWSERS_DIR_LINUX="$HOME/.cache/ms-playwright"
PLAYWRIGHT_BROWSERS_DIR_MAC="$HOME/Library/Caches/ms-playwright"

if [ -d "$PLAYWRIGHT_BROWSERS_DIR_LINUX" ] || [ -d "$PLAYWRIGHT_BROWSERS_DIR_MAC" ]; then
    show_status "OK" "Navigateurs Playwright installés"
else
    show_status "WARNING" "Navigateurs Playwright non installés"
    MISSING_DEPS+=("playwright-browsers")
fi

echo -e "\n${BLUE}📊 RÉSUMÉ${NC}"
echo -e "${BLUE}=======${NC}"

if [ ${#MISSING_SYSTEM_DEPS[@]} -eq 0 ] && [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 Toutes les dépendances sont installées et à jour !${NC}"
    echo -e "${GREEN}✅ Le projet est prêt à être utilisé.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Dépendances manquantes détectées :${NC}"
    
    if [ ${#MISSING_SYSTEM_DEPS[@]} -gt 0 ]; then
        echo -e "${RED}📋 Prérequis système manquants :${NC}"
        for dep in "${MISSING_SYSTEM_DEPS[@]}"; do
            echo -e "   • $dep"
        done
    fi
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo -e "${RED}📦 Dépendances Node.js manquantes :${NC}"
        for dep in "${MISSING_DEPS[@]}"; do
            echo -e "   • $dep"
        done
    fi
    
    echo -e "\n${BLUE}🚀 INSTALLATION AUTOMATIQUE${NC}"
    echo -e "${BLUE}========================${NC}"
    
    # Demander confirmation
    read -p "Voulez-vous installer automatiquement les dépendances manquantes ? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🔄 Installation en cours...${NC}"
        
        # Installer les dépendances Node.js
        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            echo -e "${YELLOW}📦 Installation des dépendances Node.js...${NC}"
            
            # Si node_modules manque, faire un npm install complet
            if [[ " ${MISSING_DEPS[@]} " =~ " node_modules " ]]; then
                echo -e "${BLUE}🔧 Installation complète des dépendances...${NC}"
                npm install
            else
                # Installer seulement les dépendances manquantes
                for dep in "${MISSING_DEPS[@]}"; do
                    if [ "$dep" != "node_modules" ] && [ "$dep" != "package-lock.json" ] && [ "$dep" != "playwright-browsers" ]; then
                        echo -e "${BLUE}📦 Installation de $dep...${NC}"
                        npm install "$dep"
                    fi
                done
            fi
            
            # Installer les navigateurs Playwright si nécessaire
            if [[ " ${MISSING_DEPS[@]} " =~ " playwright-browsers " ]]; then
                echo -e "${BLUE}🌐 Installation des navigateurs Playwright...${NC}"
                npx playwright install
            fi
        fi
        
        echo -e "${GREEN}✅ Installation terminée !${NC}"
        echo -e "${GREEN}🎉 Le projet est maintenant prêt à être utilisé.${NC}"
        
        # Relancer la vérification
        echo -e "\n${BLUE}🔄 Vérification finale...${NC}"
        exec "$0"
        
    else
        echo -e "${YELLOW}❌ Installation annulée.${NC}"
        echo -e "${BLUE}💡 Pour installer manuellement :${NC}"
        echo -e "   npm install"
        echo -e "   npx playwright install"
        exit 1
    fi
fi 