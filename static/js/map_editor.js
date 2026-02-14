// static/js/map_editor.js

class MapEditor {
    constructor(config) {
        this.config = config;
        this.map = null;
        this.layers = [];
        this.objects = [];
        this.currentLayer = null;
        this.currentTool = 'select';
        this.drawnItems = new L.FeatureGroup();
        
        this.init();
    }
    
    async init() {
        // Инициализация карты
        this.map = L.map('leaflet-map').setView(
            [this.config.height/2, this.config.width/2], 
            1
        );
        
        // Добавляем изображение карты
        L.imageOverlay(this.config.imageUrl, this.config.bounds).addTo(this.map);
        this.map.setMaxBounds(this.config.bounds);
        
        // Добавляем слой для рисования
        this.drawnItems.addTo(this.map);
        
        // Загружаем данные карты
        await this.loadMapData();
        
        // Настройка инструментов
        this.setupTools();
        
        // Обработчики событий
        this.setupEvents();
    }
    
    async loadMapData() {
        try {
            const response = await fetch(`/api/map/${this.config.id}/`);
            const data = await response.json();
            
            this.layers = data.layers;
            this.renderLayers();
            
            // Отображаем объекты
            this.renderObjects();
            
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
        }
    }
    
    renderLayers() {
        const container = document.getElementById('layers-list');
        container.innerHTML = '';
        
        this.layers.forEach(layer => {
            const div = document.createElement('div');
            div.className = 'layer-item';
            div.innerHTML = `
                <div style="display: flex; align-items: center;">
                    <span class="color-badge" style="background: ${layer.color}"></span>
                    <span>${layer.name}</span>
                    <span style="margin-left: auto; font-size: 12px;">
                        ${layer.objects.length} об.
                    </span>
                </div>
            `;
            
            div.onclick = () => this.selectLayer(layer);
            container.appendChild(div);
        });
        
        // Выбираем первый слой
        if (this.layers.length > 0 && !this.currentLayer) {
            this.selectLayer(this.layers[0]);
        }
    }
    
    selectLayer(layer) {
        this.currentLayer = layer;
        
        // Обновляем UI
        document.querySelectorAll('.layer-item').forEach(el => {
            el.classList.remove('active');
        });
        event.target.closest('.layer-item').classList.add('active');
        
        // Показываем объекты слоя
        this.renderObjects();
    }
    
    renderObjects() {
        const container = document.getElementById('objects-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!this.currentLayer) {
            container.innerHTML = '<p class="text-muted">Выберите слой</p>';
            return;
        }
        
        this.currentLayer.objects.forEach(obj => {
            const div = document.createElement('div');
            div.className = 'object-item';
            div.innerHTML = `
                <strong>${obj.label || obj.type}</strong>
                <small class="text-muted d-block">${obj.type}</small>
            `;
            
            div.onclick = () => this.editObject(obj);
            container.appendChild(div);
        });
    }
    
    setupTools() {
        // Маркер
        document.getElementById('tool-marker')?.addEventListener('click', () => {
            this.currentTool = 'marker';
            alert('Кликните на карту, чтобы поставить маркер');
            this.map.on('click', this.addMarker.bind(this));
        });
        
        // Линия
        document.getElementById('tool-polyline')?.addEventListener('click', () => {
            this.currentTool = 'polyline';
            alert('Кликайте на карту для создания линии (Enter - завершить)');
            this.startDrawing('polyline');
        });
        
        // Область
        document.getElementById('tool-polygon')?.addEventListener('click', () => {
            this.currentTool = 'polygon';
            alert('Кликайте на карту для создания области (Enter - завершить)');
            this.startDrawing('polygon');
        });
        
        // Выбор
        document.getElementById('tool-select')?.addEventListener('click', () => {
            this.currentTool = 'select';
        });
        
        // Удаление
        document.getElementById('tool-delete')?.addEventListener('click', () => {
            if (confirm('Удалить все объекты?')) {
                this.drawnItems.clearLayers();
                this.saveAll();
            }
        });
    }
    
    addMarker(e) {
        if (this.currentTool !== 'marker' || !this.currentLayer) return;
        
        const marker = L.marker(e.latlng).addTo(this.drawnItems);
        
        // Сохраняем в БД
        this.saveObject({
            type: 'marker',
            coordinates: [e.latlng.lat, e.latlng.lng],
            layer_id: this.currentLayer.id,
            properties: {color: this.currentLayer.color}
        }).then(objId => {
            marker._objectId = objId;
            marker.bindPopup(`<b>Маркер</b><br>ID: ${objId}`).openPopup();
        });
        
        // Убираем обработчик
        this.map.off('click', this.addMarker);
    }
    
    startDrawing(type) {
        const points = [];
        let polyline = null;
        
        const clickHandler = (e) => {
            points.push([e.latlng.lat, e.latlng.lng]);
            
            if (!polyline) {
                polyline = L.polyline(points, {color: this.currentLayer?.color || 'red'})
                    .addTo(this.drawnItems);
            } else {
                polyline.setLatLngs(points);
            }
        };
        
        const keyHandler = (e) => {
            if (e.key === 'Enter' && points.length >= 2) {
                // Сохраняем
                this.saveObject({
                    type: type,
                    coordinates: points,
                    layer_id: this.currentLayer?.id,
                    properties: {color: this.currentLayer?.color || 'red'}
                });
                
                // Очищаем
                this.map.off('click', clickHandler);
                document.removeEventListener('keydown', keyHandler);
                
                if (type === 'polygon') {
                    polyline.setStyle({fill: true, fillOpacity: 0.3});
                }
            }
        };
        
        this.map.on('click', clickHandler);
        document.addEventListener('keydown', keyHandler);
    }
    
    async saveObject(data) {
        try {
            const response = await fetch('/api/object/save/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Объект сохранен!');
                return result.object_id;
            }
        } catch (error) {
            console.error('Ошибка сохранения:', error);
        }
    }
    
    async saveAll() {
        // Сохраняем все нарисованные объекты
        alert('Функция сохранения всех объектов');
    }
    
    setupEvents() {
        // Сохранение по Ctrl+S
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveAll();
            }
        });
    }
}