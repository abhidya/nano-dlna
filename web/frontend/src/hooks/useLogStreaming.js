/**
 * React Hook for Real-time Log Streaming
 * Provides WebSocket-based log streaming functionality
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import logService from '../services/logService';

export const useLogStreaming = ({
  sources = null,
  levels = null,
  search = null,
  autoConnect = true,
  maxLogs = 1000
} = {}) => {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalLogs: 0,
    newLogsCount: 0,
    connectionTime: null
  });
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 2000;
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  const wsUrl = backendUrl.replace('http://', 'ws://').replace('https://', 'wss://');
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }
    
    try {
      const ws = new WebSocket(`${wsUrl}/api/logs/ws`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        setStats(prev => ({
          ...prev,
          connectionTime: new Date()
        }));
        reconnectAttempts.current = 0;
        
        logService.logInfo('WebSocket log stream connected', {
          component: 'useLogStreaming'
        });
        
        // Send initial filter configuration if needed
        if (sources || levels || search) {
          ws.send(JSON.stringify({
            type: 'filter_update',
            sources,
            levels,
            search
          }));
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const logEntry = JSON.parse(event.data);
          
          if (logEntry.type === 'filter_ack') {
            // Handle filter acknowledgment
            return;
          }
          
          setLogs(prevLogs => {
            const newLogs = [logEntry, ...prevLogs].slice(0, maxLogs);
            return newLogs;
          });
          
          setStats(prev => ({
            ...prev,
            totalLogs: prev.totalLogs + 1,
            newLogsCount: prev.newLogsCount + 1
          }));
          
        } catch (error) {
          console.error('Error parsing log message:', error);
          logService.logError('Error parsing WebSocket log message', {
            component: 'useLogStreaming',
            error: error.message
          });
        }
      };
      
      ws.onclose = (event) => {
        setIsConnected(false);
        
        if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttempts.current);
          
          logService.logWarning(`WebSocket closed, reconnecting in ${delay}ms`, {
            component: 'useLogStreaming',
            attempt: reconnectAttempts.current + 1
          });
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Failed to reconnect after multiple attempts');
          logService.logError('WebSocket reconnection failed', {
            component: 'useLogStreaming',
            attempts: reconnectAttempts.current
          });
        }
      };
      
      ws.onerror = (error) => {
        setError('WebSocket connection error');
        logService.logError('WebSocket error', {
          component: 'useLogStreaming',
          error: error.message || 'Unknown WebSocket error'
        });
      };
      
    } catch (error) {
      setError(`Connection failed: ${error.message}`);
      logService.logError('Failed to create WebSocket connection', {
        component: 'useLogStreaming',
        error: error.message
      });
    }
  }, [wsUrl, sources, levels, search, maxLogs]);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    logService.logInfo('WebSocket log stream disconnected', {
      component: 'useLogStreaming'
    });
  }, []);
  
  const clearLogs = useCallback(() => {
    setLogs([]);
    setStats(prev => ({
      ...prev,
      newLogsCount: 0
    }));
    
    logService.logInfo('Log display cleared', {
      component: 'useLogStreaming'
    });
  }, []);
  
  const updateFilters = useCallback((newFilters) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'filter_update',
        ...newFilters
      }));
      
      logService.logInfo('Log filters updated', {
        component: 'useLogStreaming',
        filters: newFilters
      });
    }
  }, []);
  
  const resetNewLogsCount = useCallback(() => {
    setStats(prev => ({
      ...prev,
      newLogsCount: 0
    }));
  }, []);
  
  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);
  
  return {
    logs,
    isConnected,
    error,
    stats,
    connect,
    disconnect,
    clearLogs,
    updateFilters,
    resetNewLogsCount
  };
};

// Hook for fetching historical logs
export const useLogHistory = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  
  const fetchLogs = useCallback(async ({
    sources = null,
    levels = null,
    sinceMinutes = null,
    limit = 1000,
    search = null
  } = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (sources) {
        sources.forEach(source => params.append('sources', source));
      }
      if (levels) {
        levels.forEach(level => params.append('levels', level));
      }
      if (sinceMinutes) {
        params.append('since_minutes', sinceMinutes);
      }
      if (limit) {
        params.append('limit', limit);
      }
      if (search) {
        params.append('search', search);
      }
      
      const response = await fetch(`${backendUrl}/api/logs?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setLogs(data.logs);
      
      logService.logInfo(`Fetched ${data.logs.length} historical logs`, {
        component: 'useLogHistory',
        filters: { sources, levels, sinceMinutes, limit, search }
      });
      
      return data;
      
    } catch (error) {
      setError(error.message);
      logService.logError('Failed to fetch log history', {
        component: 'useLogHistory',
        error: error.message
      });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);
  
  const exportLogs = useCallback(async (format = 'json', filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.sources) {
        filters.sources.forEach(source => params.append('sources', source));
      }
      if (filters.levels) {
        filters.levels.forEach(level => params.append('levels', level));
      }
      if (filters.sinceMinutes) {
        params.append('since_minutes', filters.sinceMinutes);
      }
      params.append('format', format);
      
      const response = await fetch(`${backendUrl}/api/logs/export?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Trigger download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      logService.logInfo(`Exported logs in ${format} format`, {
        component: 'useLogHistory'
      });
      
    } catch (error) {
      logService.logError('Failed to export logs', {
        component: 'useLogHistory',
        error: error.message
      });
      throw error;
    }
  }, [backendUrl]);
  
  return {
    logs,
    loading,
    error,
    fetchLogs,
    exportLogs
  };
};