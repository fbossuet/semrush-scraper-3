#!/usr/bin/env python3
"""
Script d'import SEM - Import de fichiers CSV dans la base de données TrendTrack
"""

import os
import csv
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SEMImporter:
    def __init__(self):
        self.db_path = "/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db"
        self.imports_dir = "/home/ubuntu/sem-scraper-final/imports"
        
    def create_imports_directory(self):
        """Créer le répertoire imports s'il n'existe pas"""
        Path(self.imports_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Répertoire imports: {self.imports_dir}")
    
    def list_csv_files(self):
        """Lister les fichiers CSV disponibles dans le répertoire imports"""
        self.create_imports_directory()
        
        csv_files = []
        for file in os.listdir(self.imports_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(self.imports_dir, file)
                file_size = os.path.getsize(file_path)
                csv_files.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size
                })
        
        return csv_files
    
    def validate_csv_format(self, file_path):
        """Valider le format du fichier CSV"""
        logger.info(f"🔍 Validation du fichier: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Lire les premières lignes pour analyser le format
                sample_lines = []
                for i, line in enumerate(file):
                    if i >= 5:  # Analyser les 5 premières lignes
                        break
                    sample_lines.append(line.strip())
            
            if not sample_lines:
                return False, "Fichier vide"
            
            # Analyser la première ligne (en-têtes)
            headers = sample_lines[0].split(',')
            logger.info(f"📋 En-têtes détectés: {headers}")
            
            # Chercher une colonne qui pourrait contenir les domaines
            domain_column = None
            possible_domain_columns = ['domain', 'domaine', 'url', 'site', 'website', 'shop_name']
            
            for i, header in enumerate(headers):
                header_lower = header.lower().strip()
                if header_lower in possible_domain_columns:
                    domain_column = i
                    logger.info(f"✅ Colonne domaine trouvée: '{header}' (index {i})")
                    break
            
            if domain_column is None:
                return False, f"Aucune colonne domaine trouvée. Colonnes disponibles: {headers}"
            
            # Valider quelques lignes de données
            valid_domains = 0
            invalid_domains = 0
            
            for i, line in enumerate(sample_lines[1:], 1):
                if not line.strip():
                    continue
                    
                columns = line.split(',')
                if len(columns) <= domain_column:
                    invalid_domains += 1
                    continue
                
                domain = columns[domain_column].strip()
                if self.is_valid_domain(domain):
                    valid_domains += 1
                else:
                    invalid_domains += 1
                    logger.warning(f"⚠️ Domaine invalide ligne {i+1}: '{domain}'")
            
            if valid_domains == 0:
                return False, "Aucun domaine valide trouvé"
            
            logger.info(f"✅ Validation réussie: {valid_domains} domaines valides, {invalid_domains} invalides")
            return True, f"Format valide. Colonne domaine: '{headers[domain_column]}' (index {domain_column})"
            
        except Exception as e:
            return False, f"Erreur de validation: {str(e)}"
    
    def is_valid_domain(self, domain):
        """Vérifier si un domaine est valide"""
        if not domain or len(domain) < 3:
            return False
        
        # Enlever les extensions communes si présentes
        domain_clean = domain.lower().strip()
        extensions = ['.com', '.fr', '.net', '.org', '.co.uk', '.de', '.es', '.it']
        
        for ext in extensions:
            if domain_clean.endswith(ext):
                domain_clean = domain_clean[:-len(ext)]
                break
        
        # Vérifier que le domaine nettoyé est valide
        if len(domain_clean) < 2:
            return False
        
        # Vérifier qu'il ne contient que des caractères valides
        valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
        if not all(c in valid_chars for c in domain_clean):
            return False
        
        return True
    
    def clean_domain(self, domain):
        """Nettoyer un domaine (enlever l'extension)"""
        domain_clean = domain.lower().strip()
        extensions = ['.com', '.fr', '.net', '.org', '.co.uk', '.de', '.es', '.it']
        
        for ext in extensions:
            if domain_clean.endswith(ext):
                domain_clean = domain_clean[:-len(ext)]
                break
        
        return domain_clean
    
    def find_domain_column(self, headers):
        """Trouver la colonne qui contient les domaines"""
        possible_domain_columns = ['domain', 'domaine', 'url', 'site', 'website', 'shop_name']
        
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            if header_lower in possible_domain_columns:
                return i
        
        # Si aucune colonne nommée trouvée, prendre la première colonne
        return 0
    
    def import_csv_to_database(self, file_path):
        """Importer le fichier CSV dans la base de données"""
        logger.info(f"📥 Import du fichier: {file_path}")
        
        try:
            # Connexion à la base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lire le fichier CSV
            imported_count = 0
            skipped_count = 0
            error_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)  # Lire les en-têtes
                
                domain_column = self.find_domain_column(headers)
                logger.info(f"🎯 Utilisation de la colonne: '{headers[domain_column]}' (index {domain_column})")
                
                for row_num, row in enumerate(csv_reader, 2):
                    if not row or len(row) <= domain_column:
                        skipped_count += 1
                        continue
                    
                    domain_raw = row[domain_column].strip()
                    if not domain_raw:
                        skipped_count += 1
                        continue
                    
                    # Nettoyer le domaine
                    domain_clean = self.clean_domain(domain_raw)
                    if not self.is_valid_domain(domain_raw):
                        logger.warning(f"⚠️ Ligne {row_num}: Domaine invalide '{domain_raw}'")
                        error_count += 1
                        continue
                    
                    # Construire l'URL complète
                    shop_url = f"https://{domain_clean}.com"
                    shop_name = domain_clean
                    
                    try:
                        # Vérifier si le shop existe déjà
                        cursor.execute("SELECT id FROM shops WHERE shop_url = ?", (shop_url,))
                        existing = cursor.fetchone()
                        
                        if existing:
                            logger.info(f"⏭️ Shop déjà existant: {shop_url}")
                            skipped_count += 1
                            continue
                        
                        # Insérer le nouveau shop
                        cursor.execute("""
                            INSERT INTO shops (shop_name, shop_url, scraping_status, scraping_last_update, updated_at, creation_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            shop_name,
                            shop_url,
                            '',  # Status vide comme demandé
                            None,
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat()
                        ))
                        
                        imported_count += 1
                        logger.info(f"✅ Importé: {shop_name} -> {shop_url}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur ligne {row_num}: {str(e)}")
                        error_count += 1
                        continue
            
            # Valider les changements
            conn.commit()
            conn.close()
            
            logger.info(f"🎉 Import terminé!")
            logger.info(f"   ✅ Importés: {imported_count}")
            logger.info(f"   ⏭️ Ignorés: {skipped_count}")
            logger.info(f"   ❌ Erreurs: {error_count}")
            
            return {
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count,
                'errors': error_count
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'import: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_interactive_import(self):
        """Interface interactive pour l'import"""
        print("=" * 80)
        print("📥 IMPORT SEM - TRENDTRACK")
        print("=" * 80)
        
        # Lister les fichiers disponibles
        csv_files = self.list_csv_files()
        
        if not csv_files:
            print(f"❌ Aucun fichier CSV trouvé dans {self.imports_dir}")
            print(f"💡 Placez vos fichiers CSV dans ce répertoire et relancez le script")
            return
        
        print(f"\n📁 Fichiers CSV disponibles dans {self.imports_dir}:")
        for i, file_info in enumerate(csv_files, 1):
            size_mb = file_info['size'] / 1024 / 1024
            print(f"   {i}. {file_info['name']} ({size_mb:.2f} MB)")
        
        # Sélection du fichier
        while True:
            try:
                choice = input(f"\n🎯 Choisissez un fichier (1-{len(csv_files)}) ou 'q' pour quitter: ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Au revoir!")
                    return
                
                file_index = int(choice) - 1
                if 0 <= file_index < len(csv_files):
                    selected_file = csv_files[file_index]
                    break
                else:
                    print(f"❌ Choix invalide. Entrez un nombre entre 1 et {len(csv_files)}")
            except ValueError:
                print("❌ Entrez un nombre valide")
        
        print(f"\n📋 Fichier sélectionné: {selected_file['name']}")
        
        # Validation du format
        is_valid, message = self.validate_csv_format(selected_file['path'])
        
        if not is_valid:
            print(f"❌ Format invalide: {message}")
            return
        
        print(f"✅ {message}")
        
        # Confirmation d'import
        confirm = input(f"\n🚀 Voulez-vous importer ce fichier? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Import annulé")
            return
        
        # Import
        print(f"\n🔄 Import en cours...")
        result = self.import_csv_to_database(selected_file['path'])
        
        if result['success']:
            print(f"\n🎉 Import réussi!")
            print(f"   ✅ Shops importés: {result['imported']}")
            print(f"   ⏭️ Shops ignorés: {result['skipped']}")
            print(f"   ❌ Erreurs: {result['errors']}")
        else:
            print(f"\n❌ Import échoué: {result['error']}")

def main():
    """Fonction principale"""
    importer = SEMImporter()
    importer.run_interactive_import()

if __name__ == "__main__":
    main()
