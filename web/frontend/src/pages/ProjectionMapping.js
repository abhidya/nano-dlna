import React, { useState, useRef, useEffect, useCallback } from 'react';
import './ProjectionMapping.css';

function ProjectionMapping() {
    const [originalImage, setOriginalImage] = useState(null);
    const [layers, setLayers] = useState([]);
    const [currentLayerIndex, setCurrentLayerIndex] = useState(-1);
    const [currentTool, setCurrentTool] = useState('floodFill');
    const [edgeSensitivity, setEdgeSensitivity] = useState(50);
    const [tolerance, setTolerance] = useState(20);
    const [brushSize, setBrushSize] = useState(10);
    const [isDrawing, setIsDrawing] = useState(false);
    const [status, setStatus] = useState('');
    const [bezierPoints, setBezierPoints] = useState([]);
    const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0, canvasX: 0, canvasY: 0, visible: false, activeCanvas: null });
    
    const originalCanvasRef = useRef(null);
    const edgeCanvasRef = useRef(null);
    const combinedCanvasRef = useRef(null);
    const currentCanvasRef = useRef(null);
    
    const layerHistoryRef = useRef(new Map());
    const projectionWindowsRef = useRef(new Map());
    const cachedImageDataRef = useRef(null);
    const cachedEdgeDataRef = useRef(null);
    
    // Cache canvas contexts
    const contextsRef = useRef({
        original: null,
        edge: null,
        combined: null,
        current: null
    });
    
    // Canvas work ref for direct manipulation
    const canvasWorkRef = useRef({
        isProcessing: false,
        pendingUpdates: [],
        maskCache: new Map(), // Cache mask data for direct manipulation
        updateTimer: null
    });
    
    // Helper function to get cached context
    const getContext = useCallback((canvasRef, contextKey) => {
        if (!contextsRef.current[contextKey] && canvasRef.current) {
            contextsRef.current[contextKey] = canvasRef.current.getContext('2d', { willReadFrequently: true });
        }
        return contextsRef.current[contextKey];
    }, []);
    
    // Get the appropriate cursor style based on the current tool
    const getCursorStyle = useCallback(() => {
        switch (currentTool) {
            case 'brush':
            case 'eraser':
                return 'none'; // Hide cursor for brush/eraser (we show custom preview)
            case 'floodFill':
                return 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'32\' height=\'32\' viewBox=\'0 0 32 32\'><path d=\'M16 2 L12 10 L20 10 Z\' fill=\'white\' stroke=\'black\'/><rect x=\'14\' y=\'10\' width=\'4\' height=\'20\' fill=\'white\' stroke=\'black\'/></svg>") 16 2, auto';
            case 'magicWand':
                return 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'32\' height=\'32\' viewBox=\'0 0 32 32\'><circle cx=\'16\' cy=\'16\' r=\'8\' fill=\'none\' stroke=\'white\' stroke-width=\'2\'/><circle cx=\'16\' cy=\'16\' r=\'8\' fill=\'none\' stroke=\'black\' stroke-width=\'1\'/><line x1=\'16\' y1=\'4\' x2=\'16\' y2=\'8\' stroke=\'white\' stroke-width=\'2\'/><line x1=\'16\' y1=\'24\' x2=\'16\' y2=\'28\' stroke=\'white\' stroke-width=\'2\'/><line x1=\'4\' y1=\'16\' x2=\'8\' y2=\'16\' stroke=\'white\' stroke-width=\'2\'/><line x1=\'24\' y1=\'16\' x2=\'28\' y2=\'16\' stroke=\'white\' stroke-width=\'2\'/></svg>") 16 16, auto';
            case 'bezier':
                return 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'32\' height=\'32\' viewBox=\'0 0 32 32\'><circle cx=\'16\' cy=\'16\' r=\'4\' fill=\'white\' stroke=\'black\'/><path d=\'M8 24 Q 16 8, 24 24\' fill=\'none\' stroke=\'white\' stroke-width=\'2\'/><path d=\'M8 24 Q 16 8, 24 24\' fill=\'none\' stroke=\'black\' stroke-width=\'1\'/></svg>") 16 16, auto';
            default:
                return 'crosshair';
        }
    }, [currentTool]);
    
    // Batch update system
    const flushPendingUpdates = useCallback(() => {
        if (canvasWorkRef.current.pendingUpdates.length === 0) return;
        
        const updates = [...canvasWorkRef.current.pendingUpdates];
        canvasWorkRef.current.pendingUpdates = [];
        
        // Apply all updates at once
        setLayers(currentLayers => {
            const newLayers = [...currentLayers];
            updates.forEach(update => {
                const layerIndex = newLayers.findIndex(l => l.id === update.layerId);
                if (layerIndex >= 0) {
                    newLayers[layerIndex] = {
                        ...newLayers[layerIndex],
                        ...update.changes
                    };
                }
            });
            return newLayers;
        });
    }, []);
    
    useEffect(() => {
        if (status) {
            const timer = setTimeout(() => setStatus(''), 3000);
            return () => clearTimeout(timer);
        }
    }, [status]);

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                setOriginalImage(img);
                initializeCanvases(img);
                updateEdgeDetection(img);
                setStatus('Image loaded successfully');
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    };
    
    const initializeCanvases = (img) => {
        const canvases = [
            originalCanvasRef.current,
            edgeCanvasRef.current,
            combinedCanvasRef.current,
            currentCanvasRef.current
        ];
        
        canvases.forEach(canvas => {
            if (canvas) {
                canvas.width = img.width;
                canvas.height = img.height;
            }
        });
        
        // Clear context cache when canvas sizes change
        contextsRef.current = {
            original: null,
            edge: null,
            combined: null,
            current: null
        };
        
        const originalCtx = getContext(originalCanvasRef, 'original');
        if (originalCtx) {
            originalCtx.drawImage(img, 0, 0);
        }
        
        if (layers.length === 0) {
            createNewLayer();
        }
    };
    
    const updateEdgeDetection = useCallback((img = originalImage) => {
        if (!img || !edgeCanvasRef.current) return;
        
        const originalCtx = getContext(originalCanvasRef, 'original');
        const edgeCtx = getContext(edgeCanvasRef, 'edge');
        
        if (originalCtx && edgeCtx) {
            const imageData = originalCtx.getImageData(0, 0, img.width, img.height);
            cachedImageDataRef.current = imageData;
            const edgeData = detectEdges(imageData, edgeSensitivity);
            cachedEdgeDataRef.current = edgeData;
            edgeCtx.putImageData(edgeData, 0, 0);
        }
    }, [originalImage, edgeSensitivity, getContext]);
    
    const detectEdges = (imageData, threshold) => {
        const width = imageData.width;
        const height = imageData.height;
        const data = imageData.data;
        const output = new ImageData(width, height);
        const outputData = output.data;
        
        const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1];
        const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let pixelX = 0;
                let pixelY = 0;
                
                for (let j = -1; j <= 1; j++) {
                    for (let i = -1; i <= 1; i++) {
                        const idx = ((y + j) * width + (x + i)) * 4;
                        const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                        const kernelIdx = (j + 1) * 3 + (i + 1);
                        pixelX += gray * sobelX[kernelIdx];
                        pixelY += gray * sobelY[kernelIdx];
                    }
                }
                
                const magnitude = Math.sqrt(pixelX * pixelX + pixelY * pixelY);
                const idx = (y * width + x) * 4;
                
                if (magnitude > threshold) {
                    outputData[idx] = 255;
                    outputData[idx + 1] = 255;
                    outputData[idx + 2] = 255;
                    outputData[idx + 3] = 255;
                } else {
                    outputData[idx] = 0;
                    outputData[idx + 1] = 0;
                    outputData[idx + 2] = 0;
                    outputData[idx + 3] = 255;
                }
            }
        }
        
        return output;
    };
    
    const getRandomColor = () => {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#FFD93D', '#6BCB77'];
        return colors[Math.floor(Math.random() * colors.length)];
    };
    
    const createNewLayer = () => {
        if (!originalImage) {
            setStatus('Please upload an image first');
            return;
        }
        
        const layerId = Date.now();
        const layerIndex = layers.length;
        const newLayer = {
            id: layerId,
            name: `Layer ${layerIndex + 1}`,
            color: getRandomColor(),
            mask: new ImageData(originalImage.width, originalImage.height),
            visible: true,
            pixelCount: 0,
            transform: { x: 0, y: 0, scale: 1, rotation: 0 }
        };
        
        // Cache the mask for direct manipulation
        canvasWorkRef.current.maskCache.set(layerId, newLayer.mask);
        
        setLayers([...layers, newLayer]);
        layerHistoryRef.current.set(layerId, { states: [], currentIndex: -1 });
        setCurrentLayerIndex(layerIndex);
        saveLayerState(layerId);
        setStatus(`Created ${newLayer.name}`);
    };
    
    const saveLayerState = (layerId) => {
        const layer = layers.find(l => l.id === layerId);
        if (!layer) return;
        
        const history = layerHistoryRef.current.get(layerId);
        if (!history) return;
        
        history.states = history.states.slice(0, history.currentIndex + 1);
        const newState = new ImageData(layer.mask.data.slice(), layer.mask.width, layer.mask.height);
        history.states.push(newState);
        
        if (history.states.length > 20) {
            history.states.shift();
        } else {
            history.currentIndex++;
        }
    };
    
    const updateCurrentCanvas = useCallback(() => {
        if (!currentCanvasRef.current || currentLayerIndex < 0) return;
        
        const ctx = getContext(currentCanvasRef, 'current');
        if (!ctx) return;
        ctx.clearRect(0, 0, currentCanvasRef.current.width, currentCanvasRef.current.height);
        
        if (originalCanvasRef.current) {
            ctx.globalAlpha = 0.3;
            ctx.drawImage(originalCanvasRef.current, 0, 0);
        }
        
        const currentLayer = layers[currentLayerIndex];
        if (currentLayer) {
            ctx.globalAlpha = 1;
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = currentLayer.mask.width;
            tempCanvas.height = currentLayer.mask.height;
            const tempCtx = tempCanvas.getContext('2d');
            
            const coloredMask = new ImageData(currentLayer.mask.width, currentLayer.mask.height);
            const maskData = currentLayer.mask.data;
            const coloredData = coloredMask.data;
            
            const r = parseInt(currentLayer.color.substr(1, 2), 16);
            const g = parseInt(currentLayer.color.substr(3, 2), 16);
            const b = parseInt(currentLayer.color.substr(5, 2), 16);
            
            for (let i = 0; i < maskData.length; i += 4) {
                if (maskData[i + 3] > 0) {
                    coloredData[i] = r;
                    coloredData[i + 1] = g;
                    coloredData[i + 2] = b;
                    coloredData[i + 3] = maskData[i + 3];
                }
            }
            
            tempCtx.putImageData(coloredMask, 0, 0);
            ctx.drawImage(tempCanvas, 0, 0);
        }
    }, [currentLayerIndex, layers, getContext]);
    
    const updateCombinedCanvas = useCallback(() => {
        if (!combinedCanvasRef.current) return;
        
        const ctx = getContext(combinedCanvasRef, 'combined');
        if (!ctx) return;
        ctx.clearRect(0, 0, combinedCanvasRef.current.width, combinedCanvasRef.current.height);
        
        if (originalCanvasRef.current) {
            ctx.globalAlpha = 0.5;
            ctx.drawImage(originalCanvasRef.current, 0, 0);
        }
        
        ctx.globalAlpha = 0.7;
        layers.forEach(layer => {
            if (layer.visible) {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = layer.mask.width;
                tempCanvas.height = layer.mask.height;
                const tempCtx = tempCanvas.getContext('2d');
                
                const coloredMask = new ImageData(layer.mask.width, layer.mask.height);
                const maskData = layer.mask.data;
                const coloredData = coloredMask.data;
                
                const r = parseInt(layer.color.substr(1, 2), 16);
                const g = parseInt(layer.color.substr(3, 2), 16);
                const b = parseInt(layer.color.substr(5, 2), 16);
                
                for (let i = 0; i < maskData.length; i += 4) {
                    if (maskData[i + 3] > 0) {
                        coloredData[i] = r;
                        coloredData[i + 1] = g;
                        coloredData[i + 2] = b;
                        coloredData[i + 3] = maskData[i + 3];
                    }
                }
                
                tempCtx.putImageData(coloredMask, 0, 0);
                ctx.drawImage(tempCanvas, 0, 0);
            }
        });
    }, [layers, getContext]);
    
    useEffect(() => {
        updateCurrentCanvas();
        updateCombinedCanvas();
        // Redraw bezier markers if we have points
        if (bezierPoints.length > 0) {
            drawBezierMarkers(bezierPoints);
        }
    }, [layers, currentLayerIndex, updateCurrentCanvas, updateCombinedCanvas, bezierPoints]);
    
    useEffect(() => {
        updateEdgeDetection();
    }, [edgeSensitivity, updateEdgeDetection]);
    
    const toggleLayerVisibility = (index) => {
        const newLayers = [...layers];
        newLayers[index].visible = !newLayers[index].visible;
        setLayers(newLayers);
    };
    
    const selectLayer = (index) => {
        setCurrentLayerIndex(index);
    };
    
    const deleteLayer = (index) => {
        if (layers.length === 1) {
            setStatus('Cannot delete last layer');
            return;
        }
        
        const layer = layers[index];
        const newLayers = layers.filter((_, i) => i !== index);
        setLayers(newLayers);
        layerHistoryRef.current.delete(layer.id);
        canvasWorkRef.current.maskCache.delete(layer.id);
        
        if (currentLayerIndex >= newLayers.length) {
            setCurrentLayerIndex(newLayers.length - 1);
        }
        
        setStatus(`Deleted ${layer.name}`);
    };
    
    const downloadLayer = (index) => {
        const layer = layers[index];
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = layer.mask.width;
        tempCanvas.height = layer.mask.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCtx.save();
        tempCtx.translate(tempCanvas.width/2, tempCanvas.height/2);
        tempCtx.rotate(layer.transform.rotation * Math.PI / 180);
        tempCtx.scale(layer.transform.scale, layer.transform.scale);
        tempCtx.translate(-tempCanvas.width/2 + layer.transform.x, -tempCanvas.height/2 + layer.transform.y);
        
        tempCtx.fillStyle = 'black';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        const maskData = layer.mask;
        for (let i = 0; i < maskData.data.length; i += 4) {
            if (maskData.data[i + 3] > 0) {
                maskData.data[i] = 255;
                maskData.data[i + 1] = 255;
                maskData.data[i + 2] = 255;
            }
        }
        
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = layer.mask.width;
        maskCanvas.height = layer.mask.height;
        maskCanvas.getContext('2d').putImageData(maskData, 0, 0);
        
        tempCtx.drawImage(maskCanvas, 0, 0);
        tempCtx.restore();
        
        const link = document.createElement('a');
        link.download = layer.name.replace(/[^a-z0-9]/gi, '_') + '.png';
        link.href = tempCanvas.toDataURL();
        link.click();
        
        setStatus(`Downloaded ${layer.name}`);
    };
    
    const downloadAllLayers = () => {
        let downloadIndex = 0;
        
        function downloadNext() {
            if (downloadIndex < layers.length) {
                downloadLayer(downloadIndex);
                downloadIndex++;
                setTimeout(downloadNext, 500);
            }
        }
        
        downloadNext();
        setStatus('Downloading all layers...');
    };
    
    const openProjectionWindow = (index) => {
        const layer = layers[index];
        
        if (projectionWindowsRef.current.has(index)) {
            projectionWindowsRef.current.get(index).close();
        }
        
        const projWindow = window.open('/backend-static/projection_window.html', `projection_${index}`, 'width=800,height=600');
        projectionWindowsRef.current.set(index, projWindow);
        
        projWindow.onload = () => {
            projWindow.postMessage({
                type: 'init',
                layer: layer,
                layerIndex: index
            }, '*');
        };
        
        setStatus(`Opened projection window for ${layer.name}`);
    };
    
    const handleCanvasMouseDown = (e) => {
        if (currentLayerIndex < 0) return;
        
        // Get the actual canvas that was clicked
        const canvas = e.currentTarget;
        const rect = canvas.getBoundingClientRect();
        
        // Calculate scale factors between displayed size and internal resolution
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        // Apply scaling to get correct canvas coordinates
        const x = Math.floor((e.clientX - rect.left) * scaleX);
        const y = Math.floor((e.clientY - rect.top) * scaleY);
        
        // For edge detection canvas, we need to apply the selection to the current layer
        const isEdgeCanvas = canvas === edgeCanvasRef.current;
        
        if (currentTool === 'floodFill') {
            smartFloodFill(x, y, isEdgeCanvas);
        } else if (currentTool === 'magicWand') {
            magicWandFloodFill(x, y, isEdgeCanvas);
        } else if (currentTool === 'brush' || currentTool === 'eraser') {
            setIsDrawing(true);
            drawBrush(x, y);
        } else if (currentTool === 'bezier') {
            const newPoints = [...bezierPoints, {x, y}];
            setBezierPoints(newPoints);
            
            // Draw temporary markers for bezier points
            drawBezierMarkers(newPoints);
            
            if (newPoints.length === 4) {
                drawBezier(newPoints);
                setBezierPoints([]);
            }
        }
    };
    
    const handleCanvasMouseMove = (e) => {
        const canvas = e.currentTarget;
        const rect = canvas.getBoundingClientRect();
        
        // Calculate scale factors between displayed size and internal resolution
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        // Apply scaling to get correct canvas coordinates
        const x = Math.floor((e.clientX - rect.left) * scaleX);
        const y = Math.floor((e.clientY - rect.top) * scaleY);
        
        // Update cursor position for preview (both screen and canvas coordinates)
        setCursorPosition({ 
            x: e.clientX - rect.left, 
            y: e.clientY - rect.top,
            canvasX: x,
            canvasY: y,
            visible: true,
            activeCanvas: canvas
        });
        
        if (!isDrawing || currentLayerIndex < 0) return;
        
        if (currentTool === 'brush' || currentTool === 'eraser') {
            drawBrush(x, y);
        }
    };
    
    const handleCanvasMouseUp = () => {
        if (isDrawing) {
            setIsDrawing(false);
            saveLayerState(layers[currentLayerIndex].id);
        }
    };
    
    const handleCanvasMouseLeave = () => {
        setCursorPosition({ x: 0, y: 0, canvasX: 0, canvasY: 0, visible: false, activeCanvas: null });
        if (isDrawing) {
            setIsDrawing(false);
            saveLayerState(layers[currentLayerIndex].id);
        }
    };
    
    const smartFloodFill = (startX, startY, fromEdgeCanvas = false) => {
        const layer = layers[currentLayerIndex];
        const width = originalImage.width;
        const height = originalImage.height;
        
        // Mark as processing
        canvasWorkRef.current.isProcessing = true;
        
        const visited = new Uint8Array(width * height);
        const stack = [{x: startX, y: startY}];
        // Use cached data if available, otherwise get fresh data
        const originalData = cachedImageDataRef.current ? cachedImageDataRef.current.data : 
            getContext(originalCanvasRef, 'original').getImageData(0, 0, width, height).data;
        const edgeData = cachedEdgeDataRef.current ? cachedEdgeDataRef.current.data :
            getContext(edgeCanvasRef, 'edge').getImageData(0, 0, width, height).data;
        
        // Work directly on cached mask if available, otherwise clone
        let maskData;
        const cachedMask = canvasWorkRef.current.maskCache.get(layer.id);
        if (cachedMask) {
            maskData = cachedMask.data;
        } else {
            const newMask = new ImageData(layer.mask.data.slice(), width, height);
            maskData = newMask.data;
            canvasWorkRef.current.maskCache.set(layer.id, newMask);
        }
        
        const startIdx = (startY * width + startX) * 4;
        const startColor = [originalData[startIdx], originalData[startIdx + 1], originalData[startIdx + 2]];
        
        let pixelCount = 0;
        const toleranceValue = tolerance * 3;
        
        // Use a more efficient stack-based approach with batch processing
        const batchSize = 100;
        let batch = 0;
        
        while (stack.length > 0) {
            const {x, y} = stack.pop();
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            
            const idx = y * width + x;
            if (visited[idx]) continue;
            visited[idx] = 1;
            
            const edgeIdx = idx * 4;
            if (edgeData[edgeIdx] > 128) continue;
            
            const pixelIdx = idx * 4;
            const colorDiff = Math.abs(originalData[pixelIdx] - startColor[0]) +
                             Math.abs(originalData[pixelIdx + 1] - startColor[1]) +
                             Math.abs(originalData[pixelIdx + 2] - startColor[2]);
            
            if (colorDiff > toleranceValue) continue;
            
            maskData[pixelIdx] = 255;
            maskData[pixelIdx + 1] = 255;
            maskData[pixelIdx + 2] = 255;
            maskData[pixelIdx + 3] = 255;
            pixelCount++;
            
            // Add neighbors
            if (x + 1 < width) stack.push({x: x + 1, y});
            if (x - 1 >= 0) stack.push({x: x - 1, y});
            if (y + 1 < height) stack.push({x, y: y + 1});
            if (y - 1 >= 0) stack.push({x, y: y - 1});
            
            // Update UI in batches to improve performance
            batch++;
            if (batch >= batchSize) {
                batch = 0;
                // Allow the UI to update
                requestAnimationFrame(() => {});
            }
        }
        
        // Update the canvas immediately for visual feedback
        const currentCtx = getContext(currentCanvasRef, 'current');
        if (currentCtx && cachedMask) {
            // Draw the updated mask directly
            requestAnimationFrame(() => {
                currentCtx.clearRect(0, 0, width, height);
                
                // Draw faded background
                if (originalCanvasRef.current) {
                    currentCtx.globalAlpha = 0.3;
                    currentCtx.drawImage(originalCanvasRef.current, 0, 0);
                    currentCtx.globalAlpha = 1;
                }
                
                // Draw the mask with layer color
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = width;
                tempCanvas.height = height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(cachedMask, 0, 0);
                
                currentCtx.globalCompositeOperation = 'source-over';
                currentCtx.fillStyle = layer.color;
                currentCtx.globalAlpha = 0.7;
                
                // Create colored version
                for (let i = 0; i < maskData.length; i += 4) {
                    if (maskData[i + 3] > 0) {
                        const pixelIndex = i / 4;
                        const x = pixelIndex % width;
                        const y = Math.floor(pixelIndex / width);
                        currentCtx.fillRect(x, y, 1, 1);
                    }
                }
            });
        }
        
        // Queue the state update
        canvasWorkRef.current.pendingUpdates.push({
            layerId: layer.id,
            changes: {
                mask: cachedMask || new ImageData(maskData, width, height),
                pixelCount: layer.pixelCount + pixelCount
            }
        });
        
        // Defer the React state update
        if (canvasWorkRef.current.updateTimer) {
            clearTimeout(canvasWorkRef.current.updateTimer);
        }
        
        canvasWorkRef.current.updateTimer = setTimeout(() => {
            canvasWorkRef.current.isProcessing = false;
            flushPendingUpdates();
            saveLayerState(layer.id);
        }, 16); // ~60fps
    };
    
    const magicWandFloodFill = (startX, startY, fromEdgeCanvas = false) => {
        const layer = layers[currentLayerIndex];
        const width = originalImage.width;
        const height = originalImage.height;
        
        // Mark as processing
        canvasWorkRef.current.isProcessing = true;
        
        const visited = new Uint8Array(width * height);
        const stack = [{x: startX, y: startY}];
        // Use cached data if available
        const originalData = cachedImageDataRef.current ? cachedImageDataRef.current.data :
            getContext(originalCanvasRef, 'original').getImageData(0, 0, width, height).data;
        
        // Work directly on cached mask
        let maskData;
        const cachedMask = canvasWorkRef.current.maskCache.get(layer.id);
        if (cachedMask) {
            maskData = cachedMask.data;
        } else {
            const newMask = new ImageData(layer.mask.data.slice(), width, height);
            maskData = newMask.data;
            canvasWorkRef.current.maskCache.set(layer.id, newMask);
        }
        
        const startIdx = (startY * width + startX) * 4;
        const startColor = [originalData[startIdx], originalData[startIdx + 1], originalData[startIdx + 2]];
        const startBrightness = (startColor[0] + startColor[1] + startColor[2]) / 3;
        
        let pixelCount = 0;
        
        while (stack.length > 0) {
            const {x, y} = stack.pop();
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            
            const idx = y * width + x;
            if (visited[idx]) continue;
            visited[idx] = 1;
            
            const pixelIdx = idx * 4;
            const pixelColor = [originalData[pixelIdx], originalData[pixelIdx + 1], originalData[pixelIdx + 2]];
            const pixelBrightness = (pixelColor[0] + pixelColor[1] + pixelColor[2]) / 3;
            
            const colorDiff = Math.abs(pixelColor[0] - startColor[0]) +
                             Math.abs(pixelColor[1] - startColor[1]) +
                             Math.abs(pixelColor[2] - startColor[2]);
            const brightnessDiff = Math.abs(pixelBrightness - startBrightness);
            
            if (colorDiff + brightnessDiff > tolerance * 4) continue;
            
            maskData[pixelIdx] = 255;
            maskData[pixelIdx + 1] = 255;
            maskData[pixelIdx + 2] = 255;
            maskData[pixelIdx + 3] = 255;
            pixelCount++;
            
            for (let dy = -1; dy <= 1; dy++) {
                for (let dx = -1; dx <= 1; dx++) {
                    if (dx === 0 && dy === 0) continue;
                    stack.push({x: x + dx, y: y + dy});
                }
            }
        }
        
        // Queue the update instead of immediate state change
        canvasWorkRef.current.pendingUpdates.push({
            layerId: layer.id,
            changes: {
                mask: cachedMask || new ImageData(maskData, width, height),
                pixelCount: layer.pixelCount + pixelCount
            }
        });
        
        // Update canvas immediately for feedback
        requestAnimationFrame(() => {
            updateCurrentCanvas();
        });
        
        // Defer state update
        if (canvasWorkRef.current.updateTimer) {
            clearTimeout(canvasWorkRef.current.updateTimer);
        }
        
        canvasWorkRef.current.updateTimer = setTimeout(() => {
            canvasWorkRef.current.isProcessing = false;
            flushPendingUpdates();
            saveLayerState(layer.id);
        }, 16);
    };
    
    const drawBrush = (x, y) => {
        if (currentLayerIndex < 0) return;
        
        const layer = layers[currentLayerIndex];
        const width = originalImage.width;
        const height = originalImage.height;
        
        // Ensure coordinates are within bounds
        if (x < 0 || x >= width || y < 0 || y >= height) return;
        
        // Work directly on cached mask
        let maskData;
        const cachedMask = canvasWorkRef.current.maskCache.get(layer.id);
        if (cachedMask) {
            maskData = cachedMask.data;
        } else {
            const newMask = new ImageData(layer.mask.data.slice(), width, height);
            maskData = newMask.data;
            canvasWorkRef.current.maskCache.set(layer.id, newMask);
        }
        
        for (let dy = -brushSize; dy <= brushSize; dy++) {
            for (let dx = -brushSize; dx <= brushSize; dx++) {
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist > brushSize) continue;
                
                const px = x + dx;
                const py = y + dy;
                
                if (px < 0 || px >= width || py < 0 || py >= originalImage.height) continue;
                
                const idx = (py * width + px) * 4;
                const alpha = 1 - (dist / brushSize);
                
                if (currentTool === 'brush') {
                    maskData[idx] = 255;
                    maskData[idx + 1] = 255;
                    maskData[idx + 2] = 255;
                    maskData[idx + 3] = Math.max(maskData[idx + 3], alpha * 255);
                } else {
                    maskData[idx] = 0;
                    maskData[idx + 1] = 0;
                    maskData[idx + 2] = 0;
                    maskData[idx + 3] = 0;
                }
            }
        }
        
        // Update canvas immediately for visual feedback
        const currentCtx = getContext(currentCanvasRef, 'current');
        if (currentCtx && cachedMask) {
            requestAnimationFrame(() => {
                // Just update the affected area for better performance
                const updateX = Math.max(0, x - brushSize - 1);
                const updateY = Math.max(0, y - brushSize - 1);
                const updateWidth = Math.min(width - updateX, brushSize * 2 + 2);
                const updateHeight = Math.min(originalImage.height - updateY, brushSize * 2 + 2);
                
                // Create partial image data for the updated region
                const partialData = currentCtx.getImageData(updateX, updateY, updateWidth, updateHeight);
                currentCtx.putImageData(partialData, updateX, updateY);
                
                updateCurrentCanvas();
            });
        }
    };
    
    const drawBezierMarkers = (points) => {
        const ctx = getContext(currentCanvasRef, 'current');
        if (!ctx) return;
        
        // Redraw current canvas first
        updateCurrentCanvas();
        
        // Draw markers and preview line
        ctx.save();
        points.forEach((point, index) => {
            // Draw point marker
            ctx.beginPath();
            ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
            ctx.fillStyle = index === 0 || index === 3 ? '#ff4444' : '#4444ff'; // Red for endpoints, blue for control points
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Draw point number
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.fillText(index + 1, point.x + 8, point.y - 8);
        });
        
        // Draw preview lines connecting points
        if (points.length > 1) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            ctx.strokeStyle = '#ffff00';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        
        // If we have 3 points, show preview of the curve
        if (points.length === 3) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            ctx.quadraticCurveTo(points[1].x, points[1].y, points[2].x, points[2].y);
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 2;
            ctx.stroke();
        }
        
        ctx.restore();
    };
    
    const drawBezier = (points) => {
        const layer = layers[currentLayerIndex];
        const width = originalImage.width;
        const height = originalImage.height;
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = width;
        tempCanvas.height = height;
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCtx.strokeStyle = 'white';
        tempCtx.lineWidth = brushSize;
        tempCtx.lineCap = 'round';
        
        tempCtx.beginPath();
        tempCtx.moveTo(points[0].x, points[0].y);
        tempCtx.bezierCurveTo(
            points[1].x, points[1].y,
            points[2].x, points[2].y,
            points[3].x, points[3].y
        );
        tempCtx.stroke();
        
        const tempData = tempCtx.getImageData(0, 0, width, height).data;
        const newMask = new ImageData(layer.mask.data.slice(), width, height);
        const maskData = newMask.data;
        
        let pixelCount = 0;
        for (let i = 0; i < tempData.length; i += 4) {
            if (tempData[i + 3] > 0) {
                maskData[i] = 255;
                maskData[i + 1] = 255;
                maskData[i + 2] = 255;
                maskData[i + 3] = 255;
                pixelCount++;
            }
        }
        
        const newLayers = [...layers];
        newLayers[currentLayerIndex].mask = newMask;
        newLayers[currentLayerIndex].pixelCount += pixelCount;
        setLayers(newLayers);
        saveLayerState(layer.id);
    };
    
    const undo = useCallback(() => {
        if (currentLayerIndex < 0) return;
        
        const layer = layers[currentLayerIndex];
        const history = layerHistoryRef.current.get(layer.id);
        
        if (!history || history.currentIndex <= 0) return;
        
        history.currentIndex--;
        const newLayers = [...layers];
        newLayers[currentLayerIndex].mask = new ImageData(
            history.states[history.currentIndex].data.slice(),
            history.states[history.currentIndex].width,
            history.states[history.currentIndex].height
        );
        
        let pixelCount = 0;
        for (let i = 3; i < newLayers[currentLayerIndex].mask.data.length; i += 4) {
            if (newLayers[currentLayerIndex].mask.data[i] > 128) pixelCount++;
        }
        newLayers[currentLayerIndex].pixelCount = pixelCount;
        
        setLayers(newLayers);
        setStatus('Undo');
    }, [currentLayerIndex, layers]);
    
    const redo = useCallback(() => {
        if (currentLayerIndex < 0) return;
        
        const layer = layers[currentLayerIndex];
        const history = layerHistoryRef.current.get(layer.id);
        
        if (!history || history.currentIndex >= history.states.length - 1) return;
        
        history.currentIndex++;
        const newLayers = [...layers];
        newLayers[currentLayerIndex].mask = new ImageData(
            history.states[history.currentIndex].data.slice(),
            history.states[history.currentIndex].width,
            history.states[history.currentIndex].height
        );
        
        let pixelCount = 0;
        for (let i = 3; i < newLayers[currentLayerIndex].mask.data.length; i += 4) {
            if (newLayers[currentLayerIndex].mask.data[i] > 128) pixelCount++;
        }
        newLayers[currentLayerIndex].pixelCount = pixelCount;
        
        setLayers(newLayers);
        setStatus('Redo');
    }, [currentLayerIndex, layers]);
    
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                undo();
            } else if (e.ctrlKey && e.key === 'y') {
                e.preventDefault();
                redo();
            }
        };
        
        const handleMessage = (event) => {
            if (event.data.type === 'updateTransform') {
                const newLayers = [...layers];
                if (newLayers[event.data.layerIndex]) {
                    newLayers[event.data.layerIndex].transform = event.data.transform;
                    setLayers(newLayers);
                }
            }
        };
        
        document.addEventListener('keydown', handleKeyDown);
        window.addEventListener('message', handleMessage);
        
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('message', handleMessage);
        };
    }, [layers, undo, redo]);
    
    const renameLayer = (index, newName) => {
        const newLayers = [...layers];
        newLayers[index].name = newName || `Layer ${index + 1}`;
        setLayers(newLayers);
    };
    
    const copyLayer = (index) => {
        const original = layers[index];
        const copy = {
            id: Date.now(),
            name: original.name + ' copy',
            color: original.color,
            mask: new ImageData(original.mask.data.slice(), original.mask.width, original.mask.height),
            visible: true,
            pixelCount: original.pixelCount,
            transform: { ...original.transform }
        };
        
        setLayers([...layers, copy]);
        layerHistoryRef.current.set(copy.id, { states: [], currentIndex: -1 });
        
        setStatus(`Copied ${original.name}`);
    };
    
    return (
        <div className="projection-mapping-container">
            <div className="tools-panel">
                <h3>Image Upload</h3>
                <input type="file" id="imageUpload" accept="image/*" onChange={handleImageUpload} />
                
                <h3>Edge Detection</h3>
                <div className="control-group">
                    <label>Sensitivity: <span>{edgeSensitivity}</span></label>
                    <input 
                        type="range" 
                        min="5" 
                        max="100" 
                        value={edgeSensitivity}
                        onChange={(e) => setEdgeSensitivity(parseInt(e.target.value))}
                    />
                </div>
                
                <h3>Tools</h3>
                <div className="tool-buttons">
                    <button 
                        className={`tool-button ${currentTool === 'floodFill' ? 'active' : ''}`}
                        onClick={() => { setCurrentTool('floodFill'); setBezierPoints([]); }}
                    >
                        🪣 Fill
                    </button>
                    <button 
                        className={`tool-button ${currentTool === 'magicWand' ? 'active' : ''}`}
                        onClick={() => { setCurrentTool('magicWand'); setBezierPoints([]); }}
                    >
                        ✨ Magic
                    </button>
                    <button 
                        className={`tool-button ${currentTool === 'brush' ? 'active' : ''}`}
                        onClick={() => { setCurrentTool('brush'); setBezierPoints([]); }}
                    >
                        🖌️ Brush
                    </button>
                    <button 
                        className={`tool-button ${currentTool === 'eraser' ? 'active' : ''}`}
                        onClick={() => { setCurrentTool('eraser'); setBezierPoints([]); }}
                    >
                        🗑️ Eraser
                    </button>
                    <button 
                        className={`tool-button ${currentTool === 'bezier' ? 'active' : ''}`}
                        onClick={() => { setCurrentTool('bezier'); setBezierPoints([]); }}
                    >
                        📐 Bezier
                    </button>
                </div>
                
                <div className="control-group">
                    <label>Tolerance: <span>{tolerance}</span></label>
                    <input 
                        type="range" 
                        min="5" 
                        max="100" 
                        value={tolerance}
                        onChange={(e) => setTolerance(parseInt(e.target.value))}
                    />
                    
                    <label>Brush Size: <span>{brushSize}</span></label>
                    <input 
                        type="range" 
                        min="1" 
                        max="50" 
                        value={brushSize}
                        onChange={(e) => setBrushSize(parseInt(e.target.value))}
                    />
                </div>
                
                <h3>Layers</h3>
                <button onClick={createNewLayer}>+ New Layer</button>
                <button onClick={downloadAllLayers}>⬇ Download All</button>
                
                <div className="layers-list">
                    {layers.map((layer, index) => {
                        const coverage = ((layer.pixelCount / (originalImage?.width * originalImage?.height || 1)) * 100).toFixed(1);
                        
                        return (
                            <div 
                                key={layer.id} 
                                className={`layer-item ${index === currentLayerIndex ? 'active' : ''}`}
                            >
                                <div>
                                    <span 
                                        className="color-square" 
                                        style={{ backgroundColor: layer.color }}
                                        onClick={() => toggleLayerVisibility(index)}
                                    ></span>
                                    <span 
                                        contentEditable
                                        suppressContentEditableWarning
                                        onBlur={(e) => renameLayer(index, e.target.textContent)}
                                    >
                                        {layer.name}
                                    </span>
                                    <small style={{ float: 'right' }}>
                                        {layer.pixelCount} px ({coverage}%)
                                    </small>
                                </div>
                                <div className="layer-controls">
                                    <button onClick={() => selectLayer(index)}>Edit</button>
                                    <button onClick={() => copyLayer(index)}>Copy</button>
                                    <button onClick={() => deleteLayer(index)}>Delete</button>
                                    <button onClick={() => downloadLayer(index)}>⬇</button>
                                    <button onClick={() => openProjectionWindow(index)}>📺</button>
                                </div>
                            </div>
                        );
                    })}
                </div>
                
                <div className="shortcut-info">
                    <h4>Keyboard Shortcuts:</h4>
                    Ctrl+Z: Undo<br />
                    Ctrl+Y: Redo<br />
                    <br />
                    <h4>Projection Window:</h4>
                    Arrow Keys: Move<br />
                    Shift+Arrow: Move fast<br />
                    +/-: Scale<br />
                    [/]: Rotate<br />
                    R: Reset<br />
                    C: Center<br />
                    H: Hide controls<br />
                    F11: Fullscreen
                </div>
            </div>
            
            <div className="canvas-area">
                <div className="canvas-container">
                    <div className="canvas-label">Original</div>
                    <canvas ref={originalCanvasRef}></canvas>
                </div>
                <div className="canvas-container">
                    <div className="canvas-label">Edge Detection</div>
                    <canvas 
                        ref={edgeCanvasRef}
                        style={{ cursor: getCursorStyle() }}
                        onMouseDown={handleCanvasMouseDown}
                        onMouseMove={handleCanvasMouseMove}
                        onMouseUp={handleCanvasMouseUp}
                        onMouseLeave={handleCanvasMouseLeave}
                    ></canvas>
                    {cursorPosition.visible && (currentTool === 'brush' || currentTool === 'eraser') && cursorPosition.activeCanvas === edgeCanvasRef.current && (
                        <div 
                            className="cursor-preview"
                            style={{
                                left: cursorPosition.x - brushSize,
                                top: cursorPosition.y - brushSize,
                                width: brushSize * 2,
                                height: brushSize * 2,
                                borderColor: currentTool === 'eraser' ? '#ff4444' : layers[currentLayerIndex]?.color || '#fff'
                            }}
                        />
                    )}
                </div>
                <div className="canvas-container">
                    <div className="canvas-label">All Layers Combined</div>
                    <canvas ref={combinedCanvasRef}></canvas>
                </div>
                <div className="canvas-container">
                    <div className="canvas-label">
                        Current Layer: <span>{layers[currentLayerIndex]?.name || 'None'}</span>
                    </div>
                    <canvas 
                        ref={currentCanvasRef}
                        style={{ cursor: getCursorStyle() }}
                        onMouseDown={handleCanvasMouseDown}
                        onMouseMove={handleCanvasMouseMove}
                        onMouseUp={handleCanvasMouseUp}
                        onMouseLeave={handleCanvasMouseLeave}
                    ></canvas>
                    {cursorPosition.visible && (currentTool === 'brush' || currentTool === 'eraser') && cursorPosition.activeCanvas === currentCanvasRef.current && (
                        <div 
                            className="cursor-preview"
                            style={{
                                left: cursorPosition.x - brushSize,
                                top: cursorPosition.y - brushSize,
                                width: brushSize * 2,
                                height: brushSize * 2,
                                borderColor: currentTool === 'eraser' ? '#ff4444' : layers[currentLayerIndex]?.color || '#fff'
                            }}
                        />
                    )}
                </div>
            </div>
            
            {status && <div className="status show">{status}</div>}
        </div>
    );
}

export default ProjectionMapping;