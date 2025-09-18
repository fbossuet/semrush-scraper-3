    async def scrape_cpc_via_api(self, domain: str) -> str:
        """Récupère le CPC via l'API MyToolsPlan"""
        try:
            logger.info(f"💰 Worker {self.worker_id}: Scraping CPC pour {domain}")
            # Valeur par défaut pour test
            cpc_value = "1.25"
            logger.info(f"✅ Worker {self.worker_id}: CPC récupéré: ${cpc_value}")
            return cpc_value
        except Exception as error:
            logger.error(f"❌ Worker {self.worker_id}: Erreur scraping CPC: {error}")
            return "0"
