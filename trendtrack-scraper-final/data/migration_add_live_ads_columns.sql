-- Migration: Ajout des colonnes live_ads_7d et live_ads_30d
-- Date: 2025-09-19
-- Description: Ajouter les colonnes pour capturer les variations de progression des Live Ads

-- Vérifier si les colonnes existent déjà
SELECT name FROM sqlite_master WHERE type='table' AND name='shops';

-- Ajouter les colonnes live_ads_7d et live_ads_30d
ALTER TABLE shops ADD COLUMN live_ads_7d INTEGER DEFAULT 0;
ALTER TABLE shops ADD COLUMN live_ads_30d INTEGER DEFAULT 0;

-- Vérifier la structure mise à jour
.schema shops

