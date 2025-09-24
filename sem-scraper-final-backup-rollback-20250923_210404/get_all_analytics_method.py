    def get_all_analytics(self):
        """
        Récupère toutes les métriques analytics de la base de données
        """
        try:
            cursor = self.conn.execute("""
                SELECT id, shop_id, metric_type, metric_value, scraping_status, 
                       scraping_date, created_at, updated_at
                FROM analytics 
                ORDER BY shop_id, metric_type, created_at DESC
            """)
            
            analytics = []
            for row in cursor.fetchall():
                analytics.append({
                    'id': row[0],
                    'shop_id': row[1],
                    'metric_type': row[2],
                    'metric_value': row[3],
                    'scraping_status': row[4],
                    'scraping_date': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            self.logger.info(f'✅ {len(analytics)} métriques analytics récupérées')
            return analytics
            
        except Exception as e:
            self.logger.error(f'❌ Erreur lors de la récupération des analytics: {e}')
            return []
