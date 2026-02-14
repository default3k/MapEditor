// static/js/simple_editor.js
class SimpleMapEditor {
    constructor(config) {
        this.config = config;
        this.map = null;
        this.drawnItems = new L.FeatureGroup();
        this.currentColor = '#ff0000';
        this.currentTool = 'marker';
        this.isDrawing = false;
        this.currentPath = null;
        this.tempLine = null;
        
        this.init();
    }
    
    init() {
        // Инициализация Leaflet карты
        this.map = L.map('leaflet-map').setView(
            [this.config.height/2, this.config.width/2], 
            1
        );
        
        // Отключаем стандартные контролы (зум и т.д.)
        this.map.removeControl(this.map.zoomControl);
        this.map.dragging.disable();
        this.map.touchZoom.disable();
        this.map.doubleClickZoom.disable();
        this.map.scrollWheelZoom.disable();
        this.map.boxZoom.disable();
        this.map.keyboard.disable();
        
        // Добавляем изображение карты
        L.imageOverlay(this.config.imageUrl, this.config.bounds).addTo(this.map);
        
        // Устанавливаем границы
        this.map.setMaxBounds(this.config.bounds);
        this.map.setMinZoom(0);
        this.map.setMaxZoom(3);
        
        // Слой для рисования
        this.drawnItems.addTo(this.map);
        
        // Настройка интерфейса
        this.setupUI();
        this.setupTools();
        
        console.log('Редактор готов! Выберите инструмент и рисуйте.');
    }
    
    setupUI() {
        // Кнопки инструментов
        const tools = {
            'marker': { icon: '📍', label: 'Маркер' },
            'polyline': { icon: '📏', label: 'Линия' },
            'polygon': { icon: '🟩', label: 'Область' },
            'rectangle': { icon: '⬜', label: 'Прямоугольник' },
            'circle': { icon: '🔵', label: 'Круг' },
            'text': { icon: '📝', label: 'Текст' },
            'eraser': { icon: '🧹', label: 'Ластик' }
        };
        
        const container = document.getElementById('tools-container');
        container.innerHTML = '';
        
        let toolIndex = 1;
        for (const [tool, data] of Object.entries(tools)) {
            const btn = document.createElement('button');
            btn.className = 'tool-btn';
            btn.innerHTML = `
                <span style="font-size: 1.2em">${data.icon}</span>
                <span>${data.label}</span>
                <small class="ms-auto text-muted">${toolIndex}</small>
            `;
            btn.onclick = () => this.selectTool(tool);
            container.appendChild(btn);
            toolIndex++;
        }
        
        // Палитра цветов
        const colors = [
            '#ff0000', '#00ff00', '#0000ff', '#ffff00',
            '#ff00ff', '#00ffff', '#ffa500', '#800080',
            '#008000', '#000080', '#800000', '#000000'
        ];
        
        const colorContainer = document.getElementById('colors-container');
        colorContainer.innerHTML = '';
        
        colors.forEach(color => {
            const colorBtn = document.createElement('button');
            colorBtn.className = 'color-btn';
            colorBtn.style.backgroundColor = color;
            colorBtn.title = color;
            
            if (color === '#000000') {
                colorBtn.style.border = '3px solid #666';
            }
            
            colorBtn.onclick = () => {
                this.currentColor = color;
                document.querySelectorAll('.color-btn').forEach(b => {
                    b.classList.remove('active');
                });
                colorBtn.classList.add('active');
            };
            
            colorContainer.appendChild(colorBtn);
        });
        
        // Выбираем первый цвет
        colorContainer.firstChild.classList.add('active');
        
        // Кнопка очистки
        document.getElementById('btn-clear').addEventListener('click', () => {
            if (confirm('Очистить весь рисунок?')) {
                this.drawnItems.clearLayers();
            }
        });
        
        // Кнопка отмены
        document.getElementById('btn-undo').addEventListener('click', () => {
            const layers = [];
            this.drawnItems.eachLayer(layer => layers.push(layer));
            if (layers.length > 0) {
                this.drawnItems.removeLayer(layers[layers.length - 1]);
            }
        });
        
        // Кнопка экспорта
        document.getElementById('btn-export').addEventListener('click', () => {
            html2canvas(document.querySelector("#map-container")).then(canvas => {
                const link = document.createElement('a');
                link.download = `map-${this.config.name}-${Date.now()}.png`;
                link.href = canvas.toDataURL();
                link.click();
            });
        });
    }
    
    selectTool(tool) {
        this.currentTool = tool;
        
        // Убираем все обработчики
        this.map.off('click');
        this.map.off('mousedown');
        this.map.off('mousemove');
        this.map.off('mouseup');
        
        // Очищаем текущий путь
        this.currentPath = null;
        this.isDrawing = false;
        if (this.tempLine) {
            this.drawnItems.removeLayer(this.tempLine);
            this.tempLine = null;
        }
        
        // Устанавливаем курсор
        const cursor = {
            'marker': 'crosshair',
            'polyline': 'crosshair',
            'polygon': 'crosshair',
            'rectangle': 'crosshair',
            'circle': 'crosshair',
            'text': 'text',
            'eraser': 'not-allowed'
        }[tool] || 'default';
        
        document.getElementById('leaflet-map').style.cursor = cursor;
        
        // Обновляем активные кнопки
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        // Настраиваем обработчики для инструмента
        switch(tool) {
            case 'marker':
                this.map.on('click', (e) => this.addMarker(e));
                break;
                
            case 'polyline':
                this.map.on('click', (e) => this.addPoint(e));
                break;
                
            case 'polygon':
                this.map.on('click', (e) => this.addPoint(e));
                break;
                
            case 'rectangle':
                this.map.on('mousedown', (e) => this.startRectangle(e));
                break;
                
            case 'circle':
                this.map.on('click', (e) => this.addCircle(e));
                break;
                
            case 'text':
                this.map.on('click', (e) => this.addText(e));
                break;
                
            case 'eraser':
                this.map.on('click', (e) => this.removeAtPoint(e));
                break;
        }
        
        console.log(`Выбран инструмент: ${tool}`);
    }
    
    // ====================
    // ИНСТРУМЕНТЫ РИСОВАНИЯ
    // ====================
    
    addMarker(e) {
        const marker = L.circleMarker(e.latlng, {
            radius: 8,
            color: this.currentColor,
            fillColor: this.currentColor,
            fillOpacity: 0.8,
            weight: 2
        }).addTo(this.drawnItems);
        
        marker.bindPopup(`<div style="color: ${this.currentColor}">📍 Маркер</div>`);
    }
    
    addPoint(e) {
        if (!this.currentPath) {
            this.currentPath = [e.latlng];
            this.tempLine = L.polyline([e.latlng], {
                color: this.currentColor,
                weight: 3,
                dashArray: '5, 5'
            }).addTo(this.drawnItems);
        } else {
            this.currentPath.push(e.latlng);
            this.tempLine.setLatLngs(this.currentPath);
        }
    }
    
    finishDrawing() {
        if (!this.currentPath || this.currentPath.length < 2) {
            return;
        }
        
        if (this.currentTool === 'polyline') {
            const polyline = L.polyline(this.currentPath, {
                color: this.currentColor,
                weight: 3
            }).addTo(this.drawnItems);
            
            this.drawnItems.removeLayer(this.tempLine);
            
        } else if (this.currentTool === 'polygon') {
            const polygon = L.polygon(this.currentPath, {
                color: this.currentColor,
                weight: 2,
                fillColor: this.currentColor,
                fillOpacity: 0.3
            }).addTo(this.drawnItems);
            
            this.drawnItems.removeLayer(this.tempLine);
        }
        
        this.currentPath = null;
        this.tempLine = null;
    }
    
    startRectangle(e) {
        const startPoint = e.latlng;
        let rectangle = null;
        
        const onMove = (e) => {
            const endPoint = e.latlng;
            
            const bounds = L.latLngBounds(startPoint, endPoint);
            
            if (!rectangle) {
                rectangle = L.rectangle(bounds, {
                    color: this.currentColor,
                    weight: 2,
                    fillColor: this.currentColor,
                    fillOpacity: 0.3,
                    dashArray: '5, 5'
                }).addTo(this.drawnItems);
            } else {
                rectangle.setBounds(bounds);
            }
        };
        
        const onUp = (e) => {
            const endPoint = e.latlng;
            const bounds = L.latLngBounds(startPoint, endPoint);
            
            this.drawnItems.removeLayer(rectangle);
            
            const finalRect = L.rectangle(bounds, {
                color: this.currentColor,
                weight: 2,
                fillColor: this.currentColor,
                fillOpacity: 0.3
            }).addTo(this.drawnItems);
            
            this.map.off('mousemove', onMove);
            this.map.off('mouseup', onUp);
        };
        
        this.map.on('mousemove', onMove);
        this.map.on('mouseup', onUp);
    }
    
    addCircle(e) {
        const circle = L.circle(e.latlng, {
            radius: 50,
            color: this.currentColor,
            weight: 2,
            fillColor: this.currentColor,
            fillOpacity: 0.3
        }).addTo(this.drawnItems);
    }
    
    addText(e) {
        const text = prompt('Введите текст:', 'Текст');
        if (text) {
            L.marker(e.latlng, {
                icon: L.divIcon({
                    className: 'text-label',
                    html: `<div style="color: ${this.currentColor}; font-weight: bold; background: white; padding: 5px 10px; border-radius: 5px; border: 2px solid ${this.currentColor}">${text}</div>`,
                    iconSize: [text.length * 10 + 30, 30]
                })
            }).addTo(this.drawnItems);
        }
    }
    
    removeAtPoint(e) {
        this.drawnItems.eachLayer((layer) => {
            if (layer.getBounds) {
                if (layer.getBounds().contains(e.latlng)) {
                    this.drawnItems.removeLayer(layer);
                }
            } else if (layer.getLatLng) {
                const distance = e.latlng.distanceTo(layer.getLatLng());
                if (distance < 20) {
                    this.drawnItems.removeLayer(layer);
                }
            }
        });
    }
    
    setupTools() {
        // Добавляем обработчик ESC для завершения рисования
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.finishDrawing();
            }
        });
    }
}

// Проверка загрузки библиотек
if (typeof L === 'undefined') {
    console.error('Leaflet не загружен!');
}