#!/usr/bin/env python3
"""
Dashboard HTML pour visualiser les métriques de la base de données
Interface avec tableau fixe et colonne URL à gauche
"""

import sqlite3
import json
from datetime import datetime, timezone
import os

def create_dashboard_html():
    """Créer l'interface HTML avec toutes les métriques"""
    
    # Connexion à la base de données
    db_path = '/home/ubuntu/trendtrack-scraper-final/data/trendtrack.db'
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer toutes les données avec les analytics
    cursor.execute("""
        SELECT 
            s.shop_url,
            s.shop_name,
            s.scraping_status,
            s.scraping_last_update,
            s.monthly_visits,
            s.monthly_revenue,
            s.live_ads,
            s.category,
            s.creation_date,
            s.updated_at,
            a.organic_traffic,
            a.visits,
            a.branded_traffic,
            a.paid_search_traffic,
            a.avg_visit_duration,
            a.bounce_rate,
            a.conversion_rate,
            a.updated_at as analytics_updated
        FROM shops s
        LEFT JOIN analytics a ON s.id = a.shop_id
        ORDER BY s.scraping_status DESC, s.shop_url ASC
    """)
    
    shops = cursor.fetchall()
    conn.close()
    
    # Statistiques
    total_shops = len(shops)
    completed = len([s for s in shops if s[2] == 'completed'])
    partial = len([s for s in shops if s[2] == 'partial'])
    na = len([s for s in shops if s[2] == 'na'])
    no_status = len([s for s in shops if s[2] is None or s[2] == ''])
    
    # Statistiques des métriques analytics
    shops_with_analytics = len([s for s in shops if s[10] is not None])  # organic_traffic
    shops_with_organic = len([s for s in shops if s[10] is not None and s[10] != 'N/A'])
    shops_with_paid = len([s for s in shops if s[13] is not None and s[13] != 'N/A'])
    shops_with_branded = len([s for s in shops if s[12] is not None and s[12] != 'N/A'])
    
    # Générer le HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Dashboard Métriques TrendTrack</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .header h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 15px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card.completed {{
            background: linear-gradient(135deg, #00b894, #00a085);
        }}
        
        .stat-card.partial {{
            background: linear-gradient(135deg, #fdcb6e, #e17055);
        }}
        
        .stat-card.na {{
            background: linear-gradient(135deg, #6c5ce7, #5f3dc4);
        }}
        
        .stat-card.no-status {{
            background: linear-gradient(135deg, #a29bfe, #6c5ce7);
        }}
        
        .stat-card.analytics {{
            background: linear-gradient(135deg, #00cec9, #00b894);
        }}
        
        .stat-card.organic {{
            background: linear-gradient(135deg, #55a3ff, #3742fa);
        }}
        
        .stat-card.paid {{
            background: linear-gradient(135deg, #ff7675, #d63031);
        }}
        
        .stat-card.branded {{
            background: linear-gradient(135deg, #fdcb6e, #e17055);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .table-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            overflow: hidden;
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            max-height: 70vh;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            min-width: 1400px;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        th:first-child {{
            position: sticky;
            left: 0;
            z-index: 11;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-width: 300px;
        }}
        
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        
        td:first-child {{
            position: sticky;
            left: 0;
            background: white;
            z-index: 5;
            min-width: 300px;
            font-weight: 500;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr:hover td:first-child {{
            background: #f8f9fa;
        }}
        
        .status {{
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .status.completed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status.partial {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status.na {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .status.null {{
            background: #e2e3e5;
            color: #383d41;
        }}
        
        .url {{
            color: #007bff;
            text-decoration: none;
            word-break: break-all;
        }}
        
        .url:hover {{
            text-decoration: underline;
        }}
        
        .timestamp {{
            font-size: 0.8em;
            color: #6c757d;
        }}
        
        .metric-value {{
            font-weight: 600;
            text-align: center;
        }}
        
        .metric-value.valid {{
            color: #28a745;
        }}
        
        .metric-value.invalid {{
            color: #dc3545;
        }}
        
        .metric-value.na {{
            color: #6c757d;
            font-style: italic;
        }}
        
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1.1em;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .last-update {{
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 15px;
        }}
        
        .filter-container {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            background: #e9ecef;
            color: #495057;
        }}
        
        .filter-btn.active {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .filter-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        
        .filter-btn.completed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .filter-btn.partial {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .filter-btn.na {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .filter-btn.null {{
            background: #e2e3e5;
            color: #383d41;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Dashboard Métriques TrendTrack</h1>
        <div class="stats">
            <div class="stat-card completed">
                <div class="stat-number">{completed}</div>
                <div class="stat-label">✅ Completed</div>
            </div>
            <div class="stat-card partial">
                <div class="stat-number">{partial}</div>
                <div class="stat-label">⚠️ Partial</div>
            </div>
            <div class="stat-card na">
                <div class="stat-number">{na}</div>
                <div class="stat-label">🚫 NA</div>
            </div>
            <div class="stat-card no-status">
                <div class="stat-number">{no_status}</div>
                <div class="stat-label">❓ Sans Statut</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card analytics">
                <div class="stat-number">{shops_with_analytics}</div>
                <div class="stat-label">📊 Avec Analytics</div>
            </div>
            <div class="stat-card organic">
                <div class="stat-number">{shops_with_organic}</div>
                <div class="stat-label">🌿 Organic Traffic</div>
            </div>
            <div class="stat-card paid">
                <div class="stat-number">{shops_with_paid}</div>
                <div class="stat-label">🔍 Paid Search</div>
            </div>
            <div class="stat-card branded">
                <div class="stat-number">{shops_with_branded}</div>
                <div class="stat-label">📈 Branded Traffic</div>
            </div>
        </div>
    </div>
    
    <div class="filter-container">
        <h3 style="text-align: center; margin-bottom: 15px; color: #2c3e50;">🔍 Filtres par Statut</h3>
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterByStatus('all')">📊 Tous ({total_shops})</button>
            <button class="filter-btn completed" onclick="filterByStatus('completed')">✅ Completed ({completed})</button>
            <button class="filter-btn partial" onclick="filterByStatus('partial')">⚠️ Partial ({partial})</button>
            <button class="filter-btn na" onclick="filterByStatus('na')">🚫 NA ({na})</button>
            <button class="filter-btn null" onclick="filterByStatus('null')">❓ Sans Statut ({no_status})</button>
        </div>
    </div>
    
    <div class="table-container">
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>🌐 URL</th>
                        <th>🏪 Nom</th>
                        <th>📊 Statut</th>
                        <th>👥 Visites/Mois</th>
                        <th>💰 Revenus/Mois</th>
                        <th>📢 Pub Active</th>
                        <th>🌿 Organic Traffic</th>
                        <th>🔍 Paid Search</th>
                        <th>📈 Branded Traffic</th>
                        <th>⏱️ Avg Duration</th>
                        <th>📊 Bounce Rate</th>
                        <th>💹 Conversion</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Ajouter les lignes de données
    for shop in shops:
        url, name, status, last_update, visits, revenue, ads, category, creation, updated, organic_traffic, visits_analytics, branded_traffic, paid_search, avg_duration, bounce_rate, conversion_rate, analytics_updated = shop
        
        # Nettoyer les données
        url = url or 'N/A'
        name = name or 'N/A'
        status = status or 'null'
        last_update = last_update or 'N/A'
        visits = visits or 'N/A'
        revenue = revenue or 'N/A'
        ads = ads or 'N/A'
        category = category or 'N/A'
        creation = creation or 'N/A'
        updated = updated or 'N/A'
        
        # Nettoyer les métriques analytics
        organic_traffic = organic_traffic or 'N/A'
        visits_analytics = visits_analytics or 'N/A'
        branded_traffic = branded_traffic or 'N/A'
        paid_search = paid_search or 'N/A'
        avg_duration = avg_duration or 'N/A'
        bounce_rate = bounce_rate or 'N/A'
        conversion_rate = conversion_rate or 'N/A'
        analytics_updated = analytics_updated or 'N/A'
        
        # Fonction pour déterminer la classe CSS des métriques
        def get_metric_class(value):
            if value == 'N/A':
                return 'na'
            elif isinstance(value, str) and (value.endswith('K') or value.endswith('M') or value.endswith('B')):
                return 'valid'
            elif isinstance(value, (int, float)) and value > 0:
                return 'valid'
            else:
                return 'invalid'
        
        # Appliquer les classes aux métriques
        organic_class = get_metric_class(organic_traffic)
        paid_class = get_metric_class(paid_search)
        branded_class = get_metric_class(branded_traffic)
        duration_class = get_metric_class(avg_duration)
        bounce_class = get_metric_class(bounce_rate)
        conversion_class = get_metric_class(conversion_rate)
        
        # Formater les timestamps
        if last_update != 'N/A':
            try:
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
            except:
                pass
        
        if creation != 'N/A':
            try:
                creation = datetime.fromisoformat(creation.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            except:
                pass
        
        if updated != 'N/A':
            try:
                updated = datetime.fromisoformat(updated.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
            except:
                pass
        
        html_content += f"""
                    <tr class="status-row {status}">
                        <td><a href="{url}" target="_blank" class="url">{url}</a></td>
                        <td>{name}</td>
                        <td><span class="status {status}">{status}</span></td>
                        <td>{visits}</td>
                        <td>{revenue}</td>
                        <td>{ads}</td>
                        <td><span class="metric-value {organic_class}">{organic_traffic}</span></td>
                        <td><span class="metric-value {paid_class}">{paid_search}</span></td>
                        <td><span class="metric-value {branded_class}">{branded_traffic}</span></td>
                        <td><span class="metric-value {duration_class}">{avg_duration}</span></td>
                        <td><span class="metric-value {bounce_class}">{bounce_rate}</span></td>
                        <td><span class="metric-value {conversion_class}">{conversion_rate}</span></td>
                    </tr>
"""
    
    html_content += f"""
                </tbody>
            </table>
        </div>
        <div class="last-update">
            📊 Total: {total_shops} domaines | Dernière mise à jour: {datetime.now(timezone.utc).isoformat()}
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">🔄 Actualiser</button>
    
    <script>
        // Fonction de filtrage par statut
        function filterByStatus(status) {{
            const rows = document.querySelectorAll('.status-row');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Mettre à jour les boutons actifs
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Filtrer les lignes
            rows.forEach(row => {{
                if (status === 'all' || row.classList.contains(status)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}
        
        // Auto-refresh toutes les 5 minutes
        setTimeout(() => {{
            location.reload();
        }}, 300000);
        
        // Ajouter des effets visuels
        document.addEventListener('DOMContentLoaded', function() {{
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {{
                row.style.animationDelay = `${{index * 0.05}}s`;
                row.style.animation = 'fadeInUp 0.5s ease forwards';
            }});
        }});
        
        // CSS pour l'animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""
    
    # Sauvegarder le fichier HTML
    output_path = '/home/ubuntu/sem-scraper-final/dashboard_metrics.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard HTML créé: {output_path}")
    print(f"📊 {total_shops} domaines affichés")
    print(f"🌐 Accès: http://37.59.102.7:8000/dashboard_metrics.html")

if __name__ == "__main__":
    create_dashboard_html()
