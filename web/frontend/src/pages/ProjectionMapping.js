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
    const [autoLayerCount, setAutoLayerCount] = useState(5);
    const [isProcessingAutoLayers, setIsProcessingAutoLayers] = useState(false);
    const [processingProgress, setProcessingProgress] = useState(0);
    const [processingStep, setProcessingStep] = useState('');
    const [baseTransform, setBaseTransform] = useState({ x: 0, y: 0, scale: 1, rotation: 0 });
    const [edgeProcessing, setEdgeProcessing] = useState(false);
    const [brushMode, setBrushMode] = useState('solid'); // 'solid' or 'spray'
    const [brushShape, setBrushShape] = useState('circle'); // 'circle' or 'square'
    const [magicWandMode, setMagicWandMode] = useState('radius'); // 'radius' or 'point'
    
    const originalCanvasRef = useRef(null);
    const edgeCanvasRef = useRef(null);
    const combinedCanvasRef = useRef(null);
    const currentCanvasRef = useRef(null);
    
    const layerHistoryRef = useRef(new Map());
    const projectionWindowsRef = useRef(new Map());
    const cachedImageDataRef = useRef(null);
    const cachedEdgeDataRef = useRef(null);
    const precomputedEdgesRef = useRef(null); // Store all edge magnitudes
    const edgeUpdateTimerRef = useRef(null);
    
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
    
    // Transform mouse coordinates to layer space accounting for all transformations
    const transformMouseToLayer = useCallback((mouseX, mouseY, layer) => {
        if (!originalImage) return { x: mouseX, y: mouseY };
        
        // Get canvas center
        const centerX = originalImage.width / 2;
        const centerY = originalImage.height / 2;
        
        // Start with mouse coordinates relative to center
        let x = mouseX - centerX;
        let y = mouseY - centerY;
        
        // Apply inverse base transform first (in reverse order: translate, rotate, scale)
        x -= baseTransform.x;
        y -= baseTransform.y;
        
        // Inverse rotation for base transform
        const baseAngle = -baseTransform.rotation * Math.PI / 180;
        const baseCos = Math.cos(baseAngle);
        const baseSin = Math.sin(baseAngle);
        let tempX = x * baseCos - y * baseSin;
        let tempY = x * baseSin + y * baseCos;
        x = tempX;
        y = tempY;
        
        // Inverse scale for base transform
        x = x / baseTransform.scale;
        y = y / baseTransform.scale;
        
        // Apply inverse layer transform (in reverse order: translate, rotate, scale)
        x -= layer.transform.x;
        y -= layer.transform.y;
        
        // Inverse rotation for layer transform
        const layerAngle = -layer.transform.rotation * Math.PI / 180;
        const layerCos = Math.cos(layerAngle);
        const layerSin = Math.sin(layerAngle);
        tempX = x * layerCos - y * layerSin;
        tempY = x * layerSin + y * layerCos;
        x = tempX;
        y = tempY;
        
        // Inverse scale for layer transform
        x = x / layer.transform.scale;
        y = y / layer.transform.scale;
        
        // Convert back to image coordinates
        return {
            x: Math.floor(x + centerX),
            y: Math.floor(y + centerY)
        };
    }, [originalImage, baseTransform]);
    
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
        
        // Precompute edges for the new image
        const imageData = originalCtx.getImageData(0, 0, img.width, img.height);
        cachedImageDataRef.current = imageData;
        
        setEdgeProcessing(true);
        // Use setTimeout to avoid blocking the UI
        setTimeout(() => {
            precomputedEdgesRef.current = precomputeEdges(imageData);
            updateEdgeDetection(img);
            setEdgeProcessing(false);
        }, 10);
        
        if (layers.length === 0) {
            createNewLayer();
        }
    };
    
    const updateEdgeDetection = useCallback((img = originalImage) => {
        if (!img || !edgeCanvasRef.current || !precomputedEdgesRef.current) return;
        
        const edgeCtx = getContext(edgeCanvasRef, 'edge');
        
        if (edgeCtx) {
            // Use precomputed edges for instant update
            const edgeData = applyEdgeThreshold(precomputedEdgesRef.current, edgeSensitivity);
            cachedEdgeDataRef.current = edgeData;
            edgeCtx.putImageData(edgeData, 0, 0);
        }
    }, [originalImage, edgeSensitivity, getContext]);
    
    // Precompute edge magnitudes once when image loads
    const precomputeEdges = (imageData) => {
        const width = imageData.width;
        const height = imageData.height;
        const data = imageData.data;
        const magnitudes = new Float32Array(width * height);
        
        
        // Convert to grayscale first (optimization)
        const grayData = new Uint8Array(width * height);
        for (let i = 0; i < width * height; i++) {
            const idx = i * 4;
            grayData[i] = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
        }
        
        // Compute edge magnitudes
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let pixelX = 0;
                let pixelY = 0;
                
                // Unrolled loop for better performance
                const row0 = (y - 1) * width;
                const row1 = y * width;
                const row2 = (y + 1) * width;
                
                // Apply Sobel operators
                pixelX = -grayData[row0 + x - 1] + grayData[row0 + x + 1]
                       - 2 * grayData[row1 + x - 1] + 2 * grayData[row1 + x + 1]
                       - grayData[row2 + x - 1] + grayData[row2 + x + 1];
                       
                pixelY = -grayData[row0 + x - 1] - 2 * grayData[row0 + x] - grayData[row0 + x + 1]
                       + grayData[row2 + x - 1] + 2 * grayData[row2 + x] + grayData[row2 + x + 1];
                
                magnitudes[y * width + x] = Math.sqrt(pixelX * pixelX + pixelY * pixelY);
            }
        }
        
        return { magnitudes, width, height };
    };
    
    // Fast threshold application using precomputed magnitudes
    const applyEdgeThreshold = (precomputed, threshold) => {
        const { magnitudes, width, height } = precomputed;
        const output = new ImageData(width, height);
        const outputData = output.data;
        
        // Apply threshold in a single pass
        for (let i = 0; i < magnitudes.length; i++) {
            const idx = i * 4;
            if (magnitudes[i] > threshold) {
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
        
        // If we're at -1 (empty state), don't truncate, just start fresh
        if (history.currentIndex === -1) {
            history.states = [];
        } else {
            // Truncate any future history when saving a new state
            history.states = history.states.slice(0, history.currentIndex + 1);
        }
        
        // Use the cached mask if available, as it contains the most recent changes
        const cachedMask = canvasWorkRef.current.maskCache.get(layerId);
        const maskToSave = cachedMask || layer.mask;
        const newState = new ImageData(maskToSave.data.slice(), maskToSave.width, maskToSave.height);
        history.states.push(newState);
        
        if (history.states.length > 50) {
            history.states.shift();
            // Don't increment currentIndex if we removed an item
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
            
            // Apply base transform first, then layer transform
            ctx.save();
            ctx.translate(currentCanvasRef.current.width/2, currentCanvasRef.current.height/2);
            
            // Apply base transform
            ctx.translate(baseTransform.x, baseTransform.y);
            ctx.rotate(baseTransform.rotation * Math.PI / 180);
            ctx.scale(baseTransform.scale, baseTransform.scale);
            
            // Apply layer transform (relative to base)
            ctx.translate(currentLayer.transform.x, currentLayer.transform.y);
            ctx.rotate(currentLayer.transform.rotation * Math.PI / 180);
            ctx.scale(currentLayer.transform.scale, currentLayer.transform.scale);
            
            // Draw centered
            ctx.drawImage(tempCanvas, -tempCanvas.width/2, -tempCanvas.height/2);
            ctx.restore();
        }
    }, [currentLayerIndex, layers, getContext, baseTransform]);
    
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
                
                // Apply transforms with base transform
                ctx.save();
                ctx.translate(combinedCanvasRef.current.width/2, combinedCanvasRef.current.height/2);
                
                // Apply base transform
                ctx.translate(baseTransform.x, baseTransform.y);
                ctx.rotate(baseTransform.rotation * Math.PI / 180);
                ctx.scale(baseTransform.scale, baseTransform.scale);
                
                // Apply layer transform
                ctx.translate(layer.transform.x, layer.transform.y);
                ctx.rotate(layer.transform.rotation * Math.PI / 180);
                ctx.scale(layer.transform.scale, layer.transform.scale);
                
                // Draw centered
                ctx.drawImage(tempCanvas, -tempCanvas.width/2, -tempCanvas.height/2);
                ctx.restore();
            }
        });
    }, [layers, getContext, baseTransform]);
    
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

    useEffect(() => {
        updateCurrentCanvas();
        updateCombinedCanvas();
        // Redraw bezier markers if we have points
        if (bezierPoints.length > 0) {
            drawBezierMarkers(bezierPoints);
        }
    }, [layers, currentLayerIndex, updateCurrentCanvas, updateCombinedCanvas, bezierPoints, drawBezierMarkers]);
    
    useEffect(() => {
        // Debounce edge updates for smoother slider experience
        if (edgeUpdateTimerRef.current) {
            clearTimeout(edgeUpdateTimerRef.current);
        }
        
        edgeUpdateTimerRef.current = setTimeout(() => {
            updateEdgeDetection();
        }, 16); // ~60fps
        
        return () => {
            if (edgeUpdateTimerRef.current) {
                clearTimeout(edgeUpdateTimerRef.current);
            }
        };
    }, [edgeSensitivity, updateEdgeDetection]);
    
    const toggleLayerVisibility = (index) => {
        const newLayers = [...layers];
        newLayers[index].visible = !newLayers[index].visible;
        setLayers(newLayers);
    };
    
    const selectLayer = (index) => {
        setCurrentLayerIndex(index);
        // Ensure mask cache is synchronized when switching layers
        const layer = layers[index];
        if (layer && !canvasWorkRef.current.maskCache.has(layer.id)) {
            canvasWorkRef.current.maskCache.set(layer.id, layer.mask);
        }
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
    
    const downloadLayer = (index, transformMode = 'combined') => {
        // transformMode: 'none', 'layer', 'base', 'combined'
        const layer = layers[index];
        const tempCanvas = document.createElement('canvas');
        
        if (transformMode !== 'none') {
            // Calculate bounds based on transform mode
            const bounds = getTransformedBounds(layer, transformMode);
            tempCanvas.width = bounds.width;
            tempCanvas.height = bounds.height;
            const tempCtx = tempCanvas.getContext('2d');
            
            // Black background
            tempCtx.fillStyle = 'black';
            tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
            
            // Apply transforms from center
            tempCtx.save();
            tempCtx.translate(tempCanvas.width/2, tempCanvas.height/2);
            
            // Apply base transform if needed
            if (transformMode === 'base' || transformMode === 'combined') {
                tempCtx.translate(baseTransform.x, baseTransform.y);
                tempCtx.rotate(baseTransform.rotation * Math.PI / 180);
                tempCtx.scale(baseTransform.scale, baseTransform.scale);
            }
            
            // Apply layer transform if needed
            if (transformMode === 'layer' || transformMode === 'combined') {
                tempCtx.translate(layer.transform.x, layer.transform.y);
                tempCtx.rotate(layer.transform.rotation * Math.PI / 180);
                tempCtx.scale(layer.transform.scale, layer.transform.scale);
            }
            
            // Create white mask
            const maskCanvas = document.createElement('canvas');
            maskCanvas.width = layer.mask.width;
            maskCanvas.height = layer.mask.height;
            const maskCtx = maskCanvas.getContext('2d');
            
            const whiteMask = new ImageData(layer.mask.width, layer.mask.height);
            for (let i = 0; i < layer.mask.data.length; i += 4) {
                if (layer.mask.data[i + 3] > 0) {
                    whiteMask.data[i] = 255;
                    whiteMask.data[i + 1] = 255;
                    whiteMask.data[i + 2] = 255;
                    whiteMask.data[i + 3] = 255;
                }
            }
            maskCtx.putImageData(whiteMask, 0, 0);
            
            // Draw centered
            tempCtx.drawImage(maskCanvas, -maskCanvas.width/2, -maskCanvas.height/2);
            tempCtx.restore();
        } else {
            // Original size without transform
            tempCanvas.width = layer.mask.width;
            tempCanvas.height = layer.mask.height;
            const tempCtx = tempCanvas.getContext('2d');
            
            tempCtx.fillStyle = 'black';
            tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
            
            const whiteMask = new ImageData(layer.mask.width, layer.mask.height);
            for (let i = 0; i < layer.mask.data.length; i += 4) {
                if (layer.mask.data[i + 3] > 0) {
                    whiteMask.data[i] = 255;
                    whiteMask.data[i + 1] = 255;
                    whiteMask.data[i + 2] = 255;
                    whiteMask.data[i + 3] = 255;
                }
            }
            tempCtx.putImageData(whiteMask, 0, 0);
        }
        
        const link = document.createElement('a');
        const suffix = transformMode === 'none' ? '' : '_' + transformMode;
        link.download = layer.name.replace(/[^a-z0-9]/gi, '_') + suffix + '.png';
        link.href = tempCanvas.toDataURL();
        link.click();
        
        setStatus(`Downloaded ${layer.name}`);
    };
    
    const getTransformedBounds = (layer, transformMode = 'combined') => {
        let w = layer.mask.width;
        let h = layer.mask.height;
        let totalRotation = 0;
        
        // Apply base transform if needed
        if (transformMode === 'base' || transformMode === 'combined') {
            w *= baseTransform.scale;
            h *= baseTransform.scale;
            totalRotation += baseTransform.rotation;
        }
        
        // Apply layer transform if needed
        if (transformMode === 'layer' || transformMode === 'combined') {
            w *= layer.transform.scale;
            h *= layer.transform.scale;
            totalRotation += layer.transform.rotation;
        }
        
        const angle = totalRotation * Math.PI / 180;
        
        // Calculate rotated bounds
        const cos = Math.abs(Math.cos(angle));
        const sin = Math.abs(Math.sin(angle));
        const width = Math.ceil(w * cos + h * sin);
        const height = Math.ceil(w * sin + h * cos);
        
        return { width, height };
    };
    
    const downloadAllLayers = () => {
        let downloadIndex = 0;
        
        function downloadNext() {
            if (downloadIndex < layers.length) {
                downloadLayer(downloadIndex, 'combined');
                downloadIndex++;
                setTimeout(downloadNext, 500);
            }
        }
        
        downloadNext();
        setStatus('Downloading all layers...');
    };
    
    const openBaseTransformWindow = () => {
        if (!originalImage) {
            setStatus('Please upload an image first');
            return;
        }
        
        const projWindow = window.open('/backend-static/projection_window.html', 'base_transform', 'width=800,height=600');
        
        projWindow.onload = () => {
            // Get the original image data
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = originalImage.width;
            tempCanvas.height = originalImage.height;
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(originalImage, 0, 0);
            const imageData = tempCtx.getImageData(0, 0, originalImage.width, originalImage.height);
            
            // Create a layer that contains the actual image data
            const imageLayer = {
                id: 'base',
                name: 'Base Transform (Original Image)',
                mask: imageData, // This contains the actual image data, not a mask
                transform: { x: 0, y: 0, scale: 1, rotation: 0 } // Base gets identity layer transform
            };
            
            projWindow.postMessage({
                type: 'init',
                layer: imageLayer,
                layerIndex: -1, // Special index for base transform
                baseTransform: baseTransform,
                isBaseTransformMode: true,
                showAsImage: true // Tell projection window to show as image, not mask
            }, '*');
        };
        
        setStatus('Opened base transform window');
    };
    
    const resetBaseTransform = () => {
        setBaseTransform({ x: 0, y: 0, scale: 1, rotation: 0 });
        setStatus('Reset base transform');
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
                layerIndex: index,
                baseTransform: baseTransform
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
        let x = Math.floor((e.clientX - rect.left) * scaleX);
        let y = Math.floor((e.clientY - rect.top) * scaleY);
        
        // Transform coordinates to layer space if we have transformations
        const currentLayer = layers[currentLayerIndex];
        if (currentLayer && (
            currentLayer.transform.rotation !== 0 || 
            currentLayer.transform.scale !== 1 ||
            currentLayer.transform.x !== 0 ||
            currentLayer.transform.y !== 0 ||
            baseTransform.rotation !== 0 ||
            baseTransform.scale !== 1 ||
            baseTransform.x !== 0 ||
            baseTransform.y !== 0
        )) {
            const transformed = transformMouseToLayer(x, y, currentLayer);
            x = transformed.x;
            y = transformed.y;
        }
        
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
        let x = Math.floor((e.clientX - rect.left) * scaleX);
        let y = Math.floor((e.clientY - rect.top) * scaleY);
        
        // Transform coordinates for drawing operations
        let drawX = x;
        let drawY = y;
        
        if (currentLayerIndex >= 0) {
            const currentLayer = layers[currentLayerIndex];
            if (currentLayer && (
                currentLayer.transform.rotation !== 0 || 
                currentLayer.transform.scale !== 1 ||
                currentLayer.transform.x !== 0 ||
                currentLayer.transform.y !== 0 ||
                baseTransform.rotation !== 0 ||
                baseTransform.scale !== 1 ||
                baseTransform.x !== 0 ||
                baseTransform.y !== 0
            )) {
                const transformed = transformMouseToLayer(x, y, currentLayer);
                drawX = transformed.x;
                drawY = transformed.y;
            }
        }
        
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
            drawBrush(drawX, drawY);
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
        
        // For edge detection, use precomputed magnitudes if available
        let isEdge;
        if (precomputedEdgesRef.current && fromEdgeCanvas) {
            const { magnitudes } = precomputedEdgesRef.current;
            isEdge = (idx) => magnitudes[idx] > edgeSensitivity;
        } else {
            const edgeData = cachedEdgeDataRef.current ? cachedEdgeDataRef.current.data :
                getContext(edgeCanvasRef, 'edge').getImageData(0, 0, width, height).data;
            isEdge = (idx) => edgeData[idx * 4] > 128;
        }
        
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
            
            if (isEdge(idx)) continue;
            
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
        const stack = [];
        
        // Use brush size to define initial selection area in radius mode
        if (magicWandMode === 'radius') {
            // Add all pixels within brush radius to initial stack
            for (let dy = -brushSize; dy <= brushSize; dy++) {
                for (let dx = -brushSize; dx <= brushSize; dx++) {
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist <= brushSize) {
                        const px = startX + dx;
                        const py = startY + dy;
                        if (px >= 0 && px < width && py >= 0 && py < height) {
                            stack.push({x: px, y: py});
                        }
                    }
                }
            }
        } else {
            // Original behavior - single point
            stack.push({x: startX, y: startY});
        }
        
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
                let isInBrush = false;
                let dist = 0;
                
                if (brushShape === 'circle') {
                    dist = Math.sqrt(dx * dx + dy * dy);
                    isInBrush = dist <= brushSize;
                } else {
                    // Square shape - already bounded by the for loop
                    isInBrush = true;
                    // Calculate distance for spray effect on square
                    dist = Math.max(Math.abs(dx), Math.abs(dy));
                }
                
                if (!isInBrush) continue;
                
                const px = x + dx;
                const py = y + dy;
                
                if (px < 0 || px >= width || py < 0 || py >= originalImage.height) continue;
                
                const idx = (py * width + px) * 4;
                
                if (currentTool === 'brush') {
                    maskData[idx] = 255;
                    maskData[idx + 1] = 255;
                    maskData[idx + 2] = 255;
                    
                    if (brushMode === 'solid') {
                        maskData[idx + 3] = 255;
                    } else {
                        // Spray mode - gradient opacity
                        const alpha = 1 - (dist / brushSize);
                        maskData[idx + 3] = Math.max(maskData[idx + 3], alpha * 255);
                    }
                } else {
                    // Eraser
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
        
        if (!history || history.currentIndex < 0 || history.states.length === 0) return;
        
        // Special case: if we're at index 0, we're going back to empty state
        if (history.currentIndex === 0) {
            // Create an empty mask
            const emptyMask = new ImageData(layer.mask.width, layer.mask.height);
            const newLayers = [...layers];
            newLayers[currentLayerIndex].mask = emptyMask;
            newLayers[currentLayerIndex].pixelCount = 0;
            
            // Update the mask cache to empty
            canvasWorkRef.current.maskCache.set(layer.id, emptyMask);
            
            history.currentIndex = -1;
            setLayers(newLayers);
            setStatus('Undo - Cleared');
            return;
        }
        
        history.currentIndex--;
        const newLayers = [...layers];
        const restoredMask = new ImageData(
            history.states[history.currentIndex].data.slice(),
            history.states[history.currentIndex].width,
            history.states[history.currentIndex].height
        );
        newLayers[currentLayerIndex].mask = restoredMask;
        
        // Update the mask cache to match the restored state
        canvasWorkRef.current.maskCache.set(layer.id, restoredMask);
        
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
        
        if (!history) return;
        
        // Check if we can redo
        if (history.currentIndex >= history.states.length - 1) return;
        
        // Special case: if we're at -1, we're redoing from empty state
        if (history.currentIndex === -1 && history.states.length > 0) {
            history.currentIndex = 0;
        } else {
            history.currentIndex++;
        }
        
        const newLayers = [...layers];
        const restoredMask = new ImageData(
            history.states[history.currentIndex].data.slice(),
            history.states[history.currentIndex].width,
            history.states[history.currentIndex].height
        );
        newLayers[currentLayerIndex].mask = restoredMask;
        
        // Update the mask cache to match the restored state
        canvasWorkRef.current.maskCache.set(layer.id, restoredMask);
        
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
            } else if (event.data.type === 'updateBaseTransform') {
                setBaseTransform(event.data.transform);
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
    
    // K-means clustering for auto-layer detection
    const kMeansClustering = (pixels, k, maxIterations = 20) => {
        // Initialize centroids with k-means++ method
        const centroids = [];
        centroids.push(pixels[Math.floor(Math.random() * pixels.length)]);
        
        for (let i = 1; i < k; i++) {
            const distances = pixels.map(pixel => {
                let minDist = Infinity;
                centroids.forEach(centroid => {
                    const dist = Math.sqrt(
                        Math.pow(pixel[0] - centroid[0], 2) +
                        Math.pow(pixel[1] - centroid[1], 2) +
                        Math.pow(pixel[2] - centroid[2], 2)
                    );
                    minDist = Math.min(minDist, dist);
                });
                return minDist;
            });
            
            const sum = distances.reduce((a, b) => a + b, 0);
            let rand = Math.random() * sum;
            for (let j = 0; j < distances.length; j++) {
                rand -= distances[j];
                if (rand <= 0) {
                    centroids.push(pixels[j]);
                    break;
                }
            }
        }
        
        // Assign pixels to clusters
        let assignments = new Array(pixels.length);
        
        for (let iter = 0; iter < maxIterations; iter++) {
            // Assign each pixel to nearest centroid
            let changed = false;
            for (let i = 0; i < pixels.length; i++) {
                let minDist = Infinity;
                let bestCluster = 0;
                
                for (let j = 0; j < k; j++) {
                    const dist = Math.sqrt(
                        Math.pow(pixels[i][0] - centroids[j][0], 2) +
                        Math.pow(pixels[i][1] - centroids[j][1], 2) +
                        Math.pow(pixels[i][2] - centroids[j][2], 2)
                    );
                    
                    if (dist < minDist) {
                        minDist = dist;
                        bestCluster = j;
                    }
                }
                
                if (assignments[i] !== bestCluster) {
                    changed = true;
                    assignments[i] = bestCluster;
                }
            }
            
            if (!changed) break;
            
            // Update centroids
            const sums = Array(k).fill(null).map(() => [0, 0, 0, 0]);
            for (let i = 0; i < pixels.length; i++) {
                const cluster = assignments[i];
                sums[cluster][0] += pixels[i][0];
                sums[cluster][1] += pixels[i][1];
                sums[cluster][2] += pixels[i][2];
                sums[cluster][3]++;
            }
            
            for (let i = 0; i < k; i++) {
                if (sums[i][3] > 0) {
                    centroids[i] = [
                        sums[i][0] / sums[i][3],
                        sums[i][1] / sums[i][3],
                        sums[i][2] / sums[i][3]
                    ];
                }
            }
        }
        
        return { centroids, assignments };
    };
    
    // Find connected components for each cluster
    const findConnectedComponents = (assignments, width, height, minSize = 100) => {
        const visited = new Uint8Array(width * height);
        const components = [];
        
        // Find max cluster number without spreading array
        let maxCluster = 0;
        for (let i = 0; i < assignments.length; i++) {
            if (assignments[i] > maxCluster) maxCluster = assignments[i];
        }
        
        for (let cluster = 0; cluster <= maxCluster; cluster++) {
            for (let i = 0; i < assignments.length; i++) {
                if (assignments[i] === cluster && !visited[i]) {
                    const component = [];
                    const stack = [i];
                    
                    while (stack.length > 0) {
                        const idx = stack.pop();
                        if (visited[idx]) continue;
                        
                        visited[idx] = 1;
                        component.push(idx);
                        
                        const x = idx % width;
                        const y = Math.floor(idx / width);
                        
                        // Check 4-connected neighbors
                        const neighbors = [
                            { x: x - 1, y },
                            { x: x + 1, y },
                            { x, y: y - 1 },
                            { x, y: y + 1 }
                        ];
                        
                        for (const neighbor of neighbors) {
                            if (neighbor.x >= 0 && neighbor.x < width && 
                                neighbor.y >= 0 && neighbor.y < height) {
                                const nIdx = neighbor.y * width + neighbor.x;
                                if (assignments[nIdx] === cluster && !visited[nIdx]) {
                                    stack.push(nIdx);
                                }
                            }
                        }
                    }
                    
                    if (component.length >= minSize) {
                        components.push({ cluster, pixels: component });
                    }
                }
            }
        }
        
        return components;
    };
    
    const autoCreateLayers = async () => {
        if (!originalImage) {
            setStatus('Please upload an image first');
            return;
        }
        
        setIsProcessingAutoLayers(true);
        setProcessingProgress(0);
        setProcessingStep('Starting...');
        
        try {
            const ctx = getContext(originalCanvasRef, 'original');
            const imageData = ctx.getImageData(0, 0, originalImage.width, originalImage.height);
            const data = imageData.data;
            
            // Give UI time to update
            await new Promise(resolve => setTimeout(resolve, 10));
            
            // Sample pixels for k-means (every 4th pixel for speed)
            setProcessingStep('Sampling pixels...');
            setProcessingProgress(10);
            const sampledPixels = [];
            for (let i = 0; i < data.length; i += 16) {
                sampledPixels.push([data[i], data[i + 1], data[i + 2]]);
            }
            
            await new Promise(resolve => setTimeout(resolve, 10));
            
            setProcessingStep('Finding color clusters...');
            setProcessingProgress(20);
            
            // Run k-means clustering
            const { centroids } = kMeansClustering(sampledPixels, autoLayerCount);
            
            await new Promise(resolve => setTimeout(resolve, 10));
            
            // Map all pixels to clusters in chunks to prevent freezing
            setProcessingStep('Assigning pixels to clusters...');
            const fullAssignments = new Array(originalImage.width * originalImage.height);
            const chunkSize = 10000;
            
            for (let chunk = 0; chunk < fullAssignments.length; chunk += chunkSize) {
                const endChunk = Math.min(chunk + chunkSize, fullAssignments.length);
                
                for (let i = chunk; i < endChunk; i++) {
                    const pixelIdx = i * 4;
                    let minDist = Infinity;
                    let bestCluster = 0;
                    
                    for (let j = 0; j < centroids.length; j++) {
                        const dist = Math.sqrt(
                            Math.pow(data[pixelIdx] - centroids[j][0], 2) +
                            Math.pow(data[pixelIdx + 1] - centroids[j][1], 2) +
                            Math.pow(data[pixelIdx + 2] - centroids[j][2], 2)
                        );
                        
                        if (dist < minDist) {
                            minDist = dist;
                            bestCluster = j;
                        }
                    }
                    
                    fullAssignments[i] = bestCluster;
                }
                
                // Update progress
                const progress = 20 + (chunk / fullAssignments.length) * 40;
                setProcessingProgress(Math.round(progress));
                
                // Give UI time to update
                await new Promise(resolve => setTimeout(resolve, 1));
            }
            
            setProcessingStep('Finding connected regions...');
            setProcessingProgress(65);
            await new Promise(resolve => setTimeout(resolve, 10));
            
            // Find connected components
            const components = findConnectedComponents(
                fullAssignments, 
                originalImage.width, 
                originalImage.height,
                (originalImage.width * originalImage.height) / 100 // Min 1% of image
            );
            
            // Sort components by size
            components.sort((a, b) => b.pixels.length - a.pixels.length);
            
            setProcessingStep('Creating layers...');
            setProcessingProgress(70);
            await new Promise(resolve => setTimeout(resolve, 10));
            
            // Clear existing layers
            setLayers([]);
            layerHistoryRef.current.clear();
            canvasWorkRef.current.maskCache.clear();
            
            // Create layers for each significant component
            const newLayers = [];
            const usedColors = new Set();
            
            // Limit to user's requested number of layers
            const maxLayers = Math.min(autoLayerCount, components.length, 10);
            
            for (let index = 0; index < maxLayers; index++) {
                const component = components[index];
                
                const layerId = Date.now() + index;
                
                // Generate unique color
                let color;
                do {
                    color = getRandomColor();
                } while (usedColors.has(color));
                usedColors.add(color);
                
                // Create mask for this component in chunks
                const mask = new ImageData(originalImage.width, originalImage.height);
                const maskData = mask.data;
                
                // Process pixels in chunks to prevent blocking
                const pixelChunkSize = 50000;
                for (let i = 0; i < component.pixels.length; i += pixelChunkSize) {
                    const end = Math.min(i + pixelChunkSize, component.pixels.length);
                    
                    for (let j = i; j < end; j++) {
                        const idx = component.pixels[j];
                        const pixelIdx = idx * 4;
                        maskData[pixelIdx] = 255;
                        maskData[pixelIdx + 1] = 255;
                        maskData[pixelIdx + 2] = 255;
                        maskData[pixelIdx + 3] = 255;
                    }
                    
                    // Update progress more granularly
                    if (i % (pixelChunkSize * 2) === 0) {
                        const componentProgress = i / component.pixels.length;
                        const overallProgress = 70 + (index / maxLayers) * 25 + 
                                              (componentProgress * 25 / maxLayers);
                        setProcessingProgress(Math.round(overallProgress));
                        setProcessingStep(`Creating layer ${index + 1} of ${maxLayers}...`);
                        await new Promise(resolve => setTimeout(resolve, 1));
                    }
                }
                
                // Determine layer name based on position (sample subset for speed)
                const sampleSize = Math.min(1000, component.pixels.length);
                const sampleStep = Math.floor(component.pixels.length / sampleSize);
                let sumX = 0, sumY = 0;
                
                for (let i = 0; i < component.pixels.length; i += sampleStep) {
                    const idx = component.pixels[i];
                    sumX += idx % originalImage.width;
                    sumY += Math.floor(idx / originalImage.width);
                }
                
                const sampledCount = Math.ceil(component.pixels.length / sampleStep);
                const avgX = sumX / sampledCount;
                const avgY = sumY / sampledCount;
                
                let name = 'Region ' + (index + 1);
                if (avgY < originalImage.height * 0.3) name = 'Top ' + name;
                else if (avgY > originalImage.height * 0.7) name = 'Bottom ' + name;
                if (avgX < originalImage.width * 0.3) name = 'Left ' + name;
                else if (avgX > originalImage.width * 0.7) name = 'Right ' + name;
                
                const newLayer = {
                    id: layerId,
                    name,
                    color,
                    mask,
                    visible: true,
                    pixelCount: component.pixels.length,
                    transform: { x: 0, y: 0, scale: 1, rotation: 0 }
                };
                
                newLayers.push(newLayer);
                layerHistoryRef.current.set(layerId, { states: [], currentIndex: -1 });
                canvasWorkRef.current.maskCache.set(layerId, mask);
                
                // Update progress
                const progress = 70 + (index / maxLayers) * 25;
                setProcessingProgress(Math.round(progress));
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            
            setLayers(newLayers);
            setCurrentLayerIndex(0);
            
            setProcessingProgress(100);
            setProcessingStep('Complete!');
            setStatus(`Created ${newLayers.length} layers automatically`);
            
        } catch (error) {
            console.error('Auto-layer error:', error);
            setStatus('Error creating layers');
        } finally {
            setTimeout(() => {
                setIsProcessingAutoLayers(false);
                setProcessingProgress(0);
                setProcessingStep('');
            }, 1000);
        }
    };
    
    return (
        <div className="projection-mapping-container">
            <div className="tools-panel">
                <h3>Image Upload</h3>
                <input type="file" id="imageUpload" accept="image/*" onChange={handleImageUpload} />
                
                <h3>Base Transform (All Layers)</h3>
                <div className="control-group" style={{ backgroundColor: '#2a2a2a', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
                    <label>Position X: <span>{baseTransform.x}</span></label>
                    <input 
                        type="range" 
                        min="-200" 
                        max="200" 
                        value={baseTransform.x}
                        onChange={(e) => setBaseTransform({...baseTransform, x: parseInt(e.target.value)})}
                    />
                    
                    <label>Position Y: <span>{baseTransform.y}</span></label>
                    <input 
                        type="range" 
                        min="-200" 
                        max="200" 
                        value={baseTransform.y}
                        onChange={(e) => setBaseTransform({...baseTransform, y: parseInt(e.target.value)})}
                    />
                    
                    <label>Scale: <span>{baseTransform.scale.toFixed(1)}</span></label>
                    <input 
                        type="range" 
                        min="0.1" 
                        max="3" 
                        step="0.1"
                        value={baseTransform.scale}
                        onChange={(e) => setBaseTransform({...baseTransform, scale: parseFloat(e.target.value)})}
                    />
                    
                    <label>Rotation: <span>{baseTransform.rotation}°</span></label>
                    <input 
                        type="range" 
                        min="-180" 
                        max="180" 
                        value={baseTransform.rotation}
                        onChange={(e) => setBaseTransform({...baseTransform, rotation: parseInt(e.target.value)})}
                    />
                    
                    <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                        <button onClick={openBaseTransformWindow} style={{ flex: 1 }}>📺 Preview</button>
                        <button onClick={resetBaseTransform} style={{ flex: 1 }}>Reset</button>
                    </div>
                </div>
                
                <h3>Edge Detection</h3>
                <div className="control-group">
                    <label>Sensitivity: <span>{edgeSensitivity}</span></label>
                    <input 
                        type="range" 
                        min="5" 
                        max="100" 
                        value={edgeSensitivity}
                        onChange={(e) => setEdgeSensitivity(parseInt(e.target.value))}
                        disabled={edgeProcessing}
                    />
                    {edgeProcessing && <small style={{display: 'block', marginTop: '5px'}}>Processing edges...</small>}
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
                    
                    <label>Brush Mode:</label>
                    <div style={{ display: 'flex', gap: '5px', marginBottom: '10px' }}>
                        <button 
                            className={`tool-button ${brushMode === 'solid' ? 'active' : ''}`}
                            onClick={() => setBrushMode('solid')}
                            style={{ flex: 1 }}
                        >
                            Solid
                        </button>
                        <button 
                            className={`tool-button ${brushMode === 'spray' ? 'active' : ''}`}
                            onClick={() => setBrushMode('spray')}
                            style={{ flex: 1 }}
                        >
                            Spray
                        </button>
                    </div>
                    
                    <label>Brush Shape:</label>
                    <div style={{ display: 'flex', gap: '5px', marginBottom: '10px' }}>
                        <button 
                            className={`tool-button ${brushShape === 'circle' ? 'active' : ''}`}
                            onClick={() => setBrushShape('circle')}
                            style={{ flex: 1 }}
                        >
                            ⭕ Circle
                        </button>
                        <button 
                            className={`tool-button ${brushShape === 'square' ? 'active' : ''}`}
                            onClick={() => setBrushShape('square')}
                            style={{ flex: 1 }}
                        >
                            ⬜ Square
                        </button>
                    </div>
                </div>
                
                <h3>Layers</h3>
                <button onClick={createNewLayer}>+ New Layer</button>
                <button onClick={downloadAllLayers}>⬇ Download All</button>
                
                <div className="control-group">
                    <label>Auto Create Layers: <span>{autoLayerCount}</span></label>
                    <input 
                        type="range" 
                        min="3" 
                        max="10" 
                        value={autoLayerCount}
                        onChange={(e) => setAutoLayerCount(parseInt(e.target.value))}
                        disabled={isProcessingAutoLayers}
                    />
                    <button 
                        onClick={autoCreateLayers}
                        disabled={isProcessingAutoLayers || !originalImage}
                        style={{ width: '100%', marginTop: '10px' }}
                    >
                        {isProcessingAutoLayers ? 'Processing...' : '🎨 Auto Create Layers'}
                    </button>
                    {isProcessingAutoLayers && (
                        <div style={{ marginTop: '10px' }}>
                            <div style={{ 
                                width: '100%', 
                                height: '20px', 
                                backgroundColor: '#2a2a2a', 
                                borderRadius: '10px',
                                overflow: 'hidden'
                            }}>
                                <div style={{ 
                                    width: `${processingProgress}%`, 
                                    height: '100%', 
                                    backgroundColor: '#4CAF50',
                                    transition: 'width 0.3s ease'
                                }} />
                            </div>
                            <small style={{ display: 'block', marginTop: '5px', textAlign: 'center' }}>
                                {processingStep}
                            </small>
                        </div>
                    )}
                </div>
                
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
                                        title="Click to edit layer name"
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
                                    <button onClick={() => downloadLayer(index, 'none')} title="Download original">⬇</button>
                                    <button onClick={() => downloadLayer(index, 'layer')} title="Download with layer transform only">⬇L</button>
                                    <button onClick={() => downloadLayer(index, 'combined')} title="Download with all transforms">⬇📐</button>
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
                                borderRadius: brushShape === 'circle' ? '50%' : '0',
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
                                borderRadius: brushShape === 'circle' ? '50%' : '0',
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