/**
 * JavaScript corrigé pour le dashboard Scraping - Correction analytics et tri
 */

// Variable globale unique pour le dashboard
let dashboard;

// Fonctions globales pour les logs
async function showLogs() {
    if (dashboard) await dashboard.showLogs();
}

function hideLogs() {
    if (dashboard) dashboard.hideLogs();
}

class TrendTrackDashboard {
    constructor() {
        this.currentPage = 1;
        this.currentLimit = 200;
        this.charts = {};
        this.currentShops = [];
        this.filteredShops = [];
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.filters = {};
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation du dashboard...');
        
        // 1. D'abord configurer les filtres (créer les selects)
        this.setupColumnFilters();
        
        // 2. Ensuite charger les données
        await this.loadShops();
        
        // 3. Enfin configurer les événements
        this.setupEventListeners();
    }

    /**
     * Charge les boutiques
     */
    async loadShops() {
        try {
            // Utiliser la route avec analytics pour récupérer toutes les métriques
            const response = await fetch('/api/shops/with-analytics?page=1&limit=1000');
            const data = await response.json();
            
            if (data.success) {
                this.currentShops = data.data;
                this.filteredShops = [...this.currentShops];
                console.log(`📊 ${this.currentShops.length} boutiques chargées`);
                
                // Debug: afficher les status uniques
                const uniqueStatuses = [...new Set(this.currentShops.map(s => s.scraping_status || 'null'))];
                console.log('🔍 Status uniques trouvés:', uniqueStatuses);
                
                // Debug: vérifier les métriques analytics
                const sampleShop = this.currentShops[0];
                if (sampleShop) {
                    console.log('🔍 Exemple de métriques analytics:', {
                        organic_traffic: sampleShop.organic_traffic,
                        bounce_rate: sampleShop.bounce_rate,
                        conversion_rate: sampleShop.conversion_rate,
                        branded_traffic: sampleShop.branded_traffic
                    });
                }
                
                this.displayShops(this.filteredShops);
                this.updateStatusCounters();
                this.updateColumnFilters();
            } else {
                this.showError('Erreur lors du chargement des boutiques');
            }
        } catch (error) {
            console.error('Erreur chargement boutiques:', error);
            this.showError('Erreur de connexion au serveur');
        }
    }

    /**
     * Met à jour les compteurs par status
     */
    updateStatusCounters() {
        const statusCounts = {};
        
        this.filteredShops.forEach(shop => {
            const status = shop.scraping_status || 'null';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        const countersContainer = document.getElementById('statusCounters');
        let countersHTML = '';

        Object.entries(statusCounts).forEach(([status, count]) => {
            const statusClass = this.getStatusClass(status);
            const displayStatus = status === '' || status === 'null' ? 'Vide' : status;
            
            countersHTML += `
                <div class="status-counter ${statusClass}">
                    <i class="fas fa-circle"></i> ${displayStatus}: ${count}
                </div>
            `;
        });

        countersContainer.innerHTML = countersHTML;
    }

    /**
     * Obtient la classe CSS pour un status
     */
    getStatusClass(status) {
        if (!status || status === '' || status === 'null') return 'unknown';
        
        const statusStr = status.toString().toLowerCase();
        
        // Classes basées sur les vrais status
        if (statusStr.includes('success') || statusStr.includes('completed')) return 'success';
        if (statusStr.includes('error') || statusStr.includes('failed')) return 'error';
        if (statusStr.includes('pending') || statusStr.includes('running')) return 'pending';
        if (statusStr.includes('processing')) return 'pending';
        if (statusStr.includes('waiting')) return 'pending';
        if (statusStr.includes('partial')) return 'pending';
        if (statusStr.includes('na')) return 'unknown';
        
        return 'unknown';
    }

    /**
     * Configure les filtres par colonne
     */
    setupColumnFilters() {
        const filterableColumns = [
            { key: 'scraping_status', label: 'Status' },
            { key: 'category', label: 'Catégorie' },
            { key: 'project_source', label: 'Projet' }
        ];

        const filtersContainer = document.getElementById('columnFilters');
        let filtersHTML = '<span style="font-weight: 600; margin-right: 10px;">Filtres:</span>';

        filterableColumns.forEach(column => {
            filtersHTML += `
                <div class="filter-group">
                    <label>${column.label}:</label>
                    <select class="filter-select" data-column="${column.key}" onchange="dashboard.applyColumnFilter('${column.key}', this.value)">
                        <option value="">Tous</option>
                    </select>
                </div>
            `;
        });

        filtersContainer.innerHTML = filtersHTML;
        console.log('✅ Filtres configurés');
    }

    /**
     * Met à jour les options des filtres par colonne
     */
    updateColumnFilters() {
        const filterableColumns = ['scraping_status', 'category', 'project_source'];
        
        filterableColumns.forEach(columnKey => {
            const select = document.querySelector(`select[data-column="${columnKey}"]`);
            if (!select) {
                console.error(`❌ Select non trouvé pour ${columnKey}`);
                return;
            }

            // Récupérer les valeurs uniques
            const values = this.currentShops.map(shop => shop[columnKey]).filter(val => val !== null && val !== undefined);
            const uniqueValues = [...new Set(values)];
            
            console.log(`🔍 ${columnKey} unique values:`, uniqueValues);
            
            // Sauvegarder la valeur actuelle
            const currentValue = select.value;
            
            // Vider et remplir les options
            select.innerHTML = '<option value="">Tous</option>';
            uniqueValues.forEach(value => {
                const option = document.createElement('option');
                option.value = value === "" ? "Vide" : value;
                option.textContent = value === '' ? 'Vide' : value;
                select.appendChild(option);
            });
            
            // Restaurer la valeur
            select.value = currentValue;
            
            console.log(`✅ ${columnKey} dropdown mis à jour avec ${uniqueValues.length} options`);
        });
    }

    /**
     * Applique un filtre par colonne
     */
    applyColumnFilter(columnKey, value) {
        console.log(`🔍 Filtre appliqué: ${columnKey} = ${value}`);
        
        if (value) {
            this.filters[columnKey] = value;
        } else {
            delete this.filters[columnKey];
        }
        
        this.applyFilters();
    }

    /**
     * Applique tous les filtres
     */
    applyFilters() {
        this.filteredShops = this.currentShops.filter(shop => {
            return Object.entries(this.filters).every(([key, filterValue]) => {
                const shopValue = shop[key];
                
                // Gestion spéciale pour les valeurs vides
                if (filterValue === 'Vide') {
                    return !shopValue || shopValue === '' || shopValue === null;
                }
                
                if (!shopValue) return false;
                
                // Comparaison exacte
                return shopValue.toString().toLowerCase() === filterValue.toLowerCase();
            });
        });
        
        console.log(`🔍 Filtrage: ${this.currentShops.length} -> ${this.filteredShops.length} boutiques`);
        
        this.displayShops(this.filteredShops);
        this.updateStatusCounters();
    }

    /**
     * Formate une valeur pour l'affichage
     */
    formatValue(value, type = 'text') {
        if (value === null || value === undefined || value === '') {
            return 'N/A';
        }
        
        if (type === 'number') {
            return typeof value === 'number' ? value.toLocaleString() : value;
        }
        
        if (type === 'percentage') {
            if (typeof value === 'number') {
                return `${value.toFixed(1)}%`;
            }
            return value;
        }
        
        return value;
    }

    /**
     * Affiche les boutiques dans le tableau
     */
    displayShops(shops) {
        const tbody = document.getElementById('shopsTableBody');
        
        if (shops.length === 0) {
            tbody.innerHTML = '<tr><td colspan="22" style="text-align: center; padding: 20px;">Aucune boutique trouvée</td></tr>';
            return;
        }

        let html = '';
        shops.forEach(shop => {
            const statusClass = this.getStatusClass(shop.scraping_status);
            const statusValue = shop.scraping_status || 'Vide';
            
            html += `
                <tr>
                    <td>
                        <button class="btn btn-secondary" onclick="viewShopDetails(${shop.id})" style="padding: 4px 8px; font-size: 0.8rem;">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                    <td>${this.formatValue(shop.shop_url)}</td>
                    <td>${this.formatValue(shop.shop_domain)}</td>
                    <td>${this.formatValue(shop.creation_date)}</td>
                    <td>${this.formatValue(shop.category)}</td>
                    <td>${this.formatValue(shop.monthly_visits, 'number')}</td>
                    <td>${this.formatValue(shop.monthly_revenue, 'number')}</td>
                    <td>${this.formatValue(shop.live_ads, 'number')}</td>
                    <td>${this.formatValue(shop.page_number)}</td>
                    <td>${this.formatValue(shop.scraped_at)}</td>
                    <td>${this.formatValue(shop.updated_at)}</td>
                    <td>${this.formatValue(shop.project_source)}</td>
                    <td>${this.formatValue(shop.external_id)}</td>
                    <td>${this.formatValue(shop.organic_traffic, 'number')}</td>
                    <td>${this.formatValue(shop.branded_traffic, 'number')}</td>
                    <td>${this.formatValue(shop.bounce_rate, 'percentage')}</td>
                    <td>${this.formatValue(shop.average_visit_duration)}</td>
                    <td>${this.formatValue(shop.conversion_rate, 'percentage')}</td>
                    <td><span class="status-badge status-${statusClass}">${statusValue}</span></td>
                    <td>${this.formatValue(shop.scraping_last_update)}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        this.restoreSortState();
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Recherche avec Enter
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchShops();
            }
        });

        // Ajouter les écouteurs de tri pour les en-têtes de colonnes
        this.setupSortListeners();
    }

    /**
     * Configure les écouteurs de tri pour les colonnes
     */
    setupSortListeners() {
        const headers = document.querySelectorAll('#shopsTable th:not(:first-child)');

        headers.forEach((header, index) => {
            header.classList.add('sortable');
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                console.log(`🔍 Tri cliqué sur colonne ${index}`);
                this.sortTable(index);
            });
            this.updateSortIndicator(header, null);
        });
    }

    /**
     * Met à jour l'indicateur de tri sur l'en-tête
     */
    updateSortIndicator(header, direction) {
        header.classList.remove('sort-asc', 'sort-desc');
        
        if (direction === 'asc') {
            header.classList.add('sort-asc');
        } else if (direction === 'desc') {
            header.classList.add('sort-desc');
        }
    }

    /**
     * Trie le tableau selon la colonne sélectionnée
     */
    sortTable(columnIndex) {
        console.log(`🔍 Tri de la colonne ${columnIndex}`);
        
        const headers = document.querySelectorAll('#shopsTable th:not(:first-child)');
        const header = headers[columnIndex];
        
        if (!header) {
            console.error(`❌ En-tête non trouvé pour l'index ${columnIndex}`);
            return;
        }
        
        if (this.sortColumn === columnIndex) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = columnIndex;
            this.sortDirection = 'asc';
        }

        console.log(`🔍 Tri: colonne ${columnIndex}, direction ${this.sortDirection}`);

        headers.forEach(h => this.updateSortIndicator(h, null));
        this.updateSortIndicator(header, this.sortDirection);

        this.filteredShops.sort((a, b) => {
            const aValue = this.getColumnValue(a, columnIndex);
            const bValue = this.getColumnValue(b, columnIndex);
            
            return this.compareValues(aValue, bValue, this.sortDirection);
        });

        this.displayShops(this.filteredShops);
    }

    /**
     * Récupère la valeur d'une colonne pour une boutique donnée
     */
    getColumnValue(shop, columnIndex) {
        const columnMap = [
            'shop_name', 'id', 'shop_url', 'shop_domain', 'creation_date', 
            'category', 'monthly_visits', 'monthly_revenue', 'live_ads', 
            'page_number', 'scraped_at', 'updated_at', 'project_source', 
            'external_id', 'organic_traffic', 'branded_traffic', 
            'bounce_rate', 'average_visit_duration', 'conversion_rate', 
            'scraping_status', 'scraping_last_update'
        ];

        const columnName = columnMap[columnIndex];
        if (!columnName) return '';

        const value = shop[columnName];
        if (value === null || value === undefined || value === '') return '';

        // Traitement spécial pour les nombres
        if (typeof value === 'number') {
            return value;
        }

        // Traitement spécial pour les chaînes numériques
        if (typeof value === 'string') {
            // Essayer de convertir en nombre si c'est possible
            const numValue = parseFloat(value.replace(/[^\d.-]/g, ''));
            if (!isNaN(numValue)) {
                return numValue;
            }
        }

        // Traitement spécial pour les dates
        if (columnName.includes('date') || columnName.includes('at')) {
            const dateValue = new Date(value);
            if (!isNaN(dateValue.getTime())) {
                return dateValue.getTime();
            }
        }

        return value.toString().toLowerCase();
    }

    /**
     * Compare deux valeurs pour le tri
     */
    compareValues(a, b, direction) {
        // Gestion des valeurs vides
        if (a === '' && b === '') return 0;
        if (a === '') return direction === 'asc' ? -1 : 1;
        if (b === '') return direction === 'asc' ? 1 : -1;
        
        if (a === b) return 0;
        
        const aIsNumber = typeof a === 'number' && !isNaN(a);
        const bIsNumber = typeof b === 'number' && !isNaN(b);
        
        if (aIsNumber && bIsNumber) {
            return direction === 'asc' ? a - b : b - a;
        }
        
        // Si l'un est un nombre et l'autre non, traiter comme des chaînes
        const aStr = a.toString();
        const bStr = b.toString();
        
        if (direction === 'asc') {
            return aStr.localeCompare(bStr);
        } else {
            return bStr.localeCompare(aStr);
        }
    }

    /**
     * Restaure l'état de tri après mise à jour du tableau
     */
    restoreSortState() {
        if (this.sortColumn !== null) {
            const headers = document.querySelectorAll('#shopsTable th:not(:first-child)');
            const header = headers[this.sortColumn];
            if (header) {
                this.updateSortIndicator(header, this.sortDirection);
            }
        }
    }

    /**
     * Recherche de boutiques
     */
    async searchShops() {
        const query = document.getElementById('searchInput').value.trim();
        
        if (!query) {
            this.filters = {};
            this.filteredShops = [...this.currentShops];
            this.displayShops(this.filteredShops);
            this.updateStatusCounters();
            this.updateColumnFilters();
            return;
        }
        
        try {
            const response = await fetch(`/api/shops/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                this.filteredShops = data.data;
                this.displayShops(this.filteredShops);
                this.updateStatusCounters();
                document.getElementById('pagination').innerHTML = '';
            } else {
                this.showError('Erreur lors de la recherche');
            }
        } catch (error) {
            console.error('Erreur recherche:', error);
            this.showError('Erreur de connexion au serveur');
        }
    }

    /**
     * Actualise les données
     */
    async refreshData() {
        await this.loadShops();
    }

    /**
     * Déclenche la mise à jour du scraper
     */
    async triggerUpdate() {
        try {
            const response = await fetch('/api/trigger-update', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                alert('Mise à jour déclenchée avec succès !');
            } else {
                this.showError('Erreur lors du déclenchement de la mise à jour');
            }
        } catch (error) {
            console.error('Erreur trigger update:', error);
            this.showError('Erreur de connexion au serveur');
        }
    }

    /**
     * Affiche une erreur
     */
    showError(message) {
        alert(message);
    }

    /**
     * Affiche les logs
     */
    async showLogs() {
        try {
            const response = await fetch('/api/logs');
            const data = await response.json();
            
            if (data.success) {
                const logs = data.data.join('\n');
                const modal = document.createElement('div');
                modal.className = 'modal-overlay';
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>Logs TrendTrack</h3>
                            <button onclick="this.closest('.modal-overlay').remove()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <pre style="max-height: 400px; overflow-y: auto;">${logs}</pre>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            } else {
                this.showError('Erreur lors du chargement des logs');
            }
        } catch (error) {
            console.error('Erreur logs:', error);
            this.showError('Erreur de connexion au serveur');
        }
    }

    /**
     * Cache les logs
     */
    hideLogs() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
    }
}

// Fonctions globales
function searchShops() {
    dashboard.searchShops();
}

function refreshData() {
    dashboard.refreshData();
}

function triggerSEMScraper() {
    alert('Fonctionnalité SEM Scraper à implémenter');
}

function showSEMLogs() {
    alert('Fonctionnalité SEM Logs à implémenter');
}

function viewShopDetails(shopId) {
    const shop = dashboard.filteredShops?.find(s => s.id === shopId);
    if (!shop) {
        alert('Boutique non trouvée');
        return;
    }
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Détails de la boutique</h3>
                <button onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="detail-row">
                    <strong>Nom:</strong> ${shop.shop_name || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>URL:</strong> ${shop.shop_url || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Domaine:</strong> ${shop.shop_domain || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Catégorie:</strong> ${shop.category || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Visites/Mois:</strong> ${shop.monthly_visits || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Revenus/Mois:</strong> ${shop.monthly_revenue || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Live Ads:</strong> ${shop.live_ads || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Status:</strong> ${shop.scraping_status || 'Vide'}
                </div>
                <div class="detail-row">
                    <strong>Organic Traffic:</strong> ${shop.organic_traffic || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Bounce Rate:</strong> ${shop.bounce_rate || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Conversion Rate:</strong> ${shop.conversion_rate || 'N/A'}
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Initialisation du dashboard quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new TrendTrackDashboard();
});
