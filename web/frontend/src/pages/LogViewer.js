/**
 * Log Viewer Component
 * Real-time log viewing with filtering and export capabilities
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useLogStreaming, useLogHistory } from '../hooks/useLogStreaming';
import logService from '../services/logService';
import './LogViewer.css';

const LogViewer = () => {
  const [activeTab, setActiveTab] = useState('realtime');
  const [filters, setFilters] = useState({
    sources: [],
    levels: [],
    search: ''
  });
  const [autoScroll, setAutoScroll] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [maxDisplayLogs, setMaxDisplayLogs] = useState(500);
  
  // Real-time streaming
  const {
    logs: streamLogs,
    isConnected,
    error: streamError,
    stats,
    connect,
    disconnect,
    clearLogs,
    resetNewLogsCount
  } = useLogStreaming({
    sources: filters.sources.length > 0 ? filters.sources : null,
    levels: filters.levels.length > 0 ? filters.levels : null,
    search: filters.search || null,
    maxLogs: maxDisplayLogs
  });
  
  // Historical logs
  const {
    logs: historyLogs,
    loading: historyLoading,
    error: historyError,
    fetchLogs,
    exportLogs
  } = useLogHistory();
  
  // Available options
  const [availableSources, setAvailableSources] = useState([]);
  const [availableLevels] = useState(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']);
  
  // Fetch available sources on mount
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/logs/sources`);
        const data = await response.json();
        setAvailableSources(data.sources);
      } catch (error) {
        logService.logError('Failed to fetch log sources', {
          component: 'LogViewer',
          error: error.message
        });
      }
    };
    
    fetchSources();
  }, []);
  
  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && activeTab === 'realtime') {
      const logContainer = document.getElementById('log-container');
      if (logContainer) {
        logContainer.scrollTop = 0; // Scroll to top since we prepend new logs
      }
    }
  }, [streamLogs, autoScroll, activeTab]);
  
  // Filter logs based on current filters
  const filteredLogs = useMemo(() => {
    const logs = activeTab === 'realtime' ? streamLogs : historyLogs;
    
    return logs.filter(log => {
      // Source filter
      if (filters.sources.length > 0 && !filters.sources.includes(log.source)) {
        return false;
      }
      
      // Level filter
      if (filters.levels.length > 0 && !filters.levels.includes(log.level)) {
        return false;
      }
      
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        return (
          log.message.toLowerCase().includes(searchLower) ||
          log.logger_name.toLowerCase().includes(searchLower) ||
          log.source.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    });
  }, [streamLogs, historyLogs, filters, activeTab]);
  
  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };
  
  const handleSourceToggle = (source) => {
    setFilters(prev => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
    }));
  };
  
  const handleLevelToggle = (level) => {
    setFilters(prev => ({
      ...prev,
      levels: prev.levels.includes(level)
        ? prev.levels.filter(l => l !== level)
        : [...prev.levels, level]
    }));
  };
  
  const handleFetchHistory = async (sinceMinutes = 60) => {
    try {
      await fetchLogs({
        sources: filters.sources.length > 0 ? filters.sources : null,
        levels: filters.levels.length > 0 ? filters.levels : null,
        search: filters.search || null,
        sinceMinutes,
        limit: 2000
      });
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };
  
  const handleExport = async (format) => {
    try {
      await exportLogs(format, {
        sources: filters.sources.length > 0 ? filters.sources : null,
        levels: filters.levels.length > 0 ? filters.levels : null,
        sinceMinutes: 60
      });
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };
  
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };
  
  const getLevelClass = (level) => {
    switch (level) {
      case 'DEBUG': return 'log-debug';
      case 'INFO': return 'log-info';
      case 'WARNING': return 'log-warning';
      case 'ERROR': return 'log-error';
      case 'CRITICAL': return 'log-critical';
      default: return 'log-info';
    }
  };
  
  const getSourceClass = (source) => {
    switch (source) {
      case 'frontend': return 'source-frontend';
      case 'database': return 'source-database';
      case 'backend_dashboard': return 'source-backend';
      case 'backend_errors': return 'source-backend-error';
      default: return 'source-other';
    }
  };
  
  return (
    <div className="log-viewer">
      <div className="log-viewer-header">
        <h2>Log Viewer</h2>
        
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button
            className={activeTab === 'realtime' ? 'active' : ''}
            onClick={() => setActiveTab('realtime')}
          >
            Real-time
            {stats.newLogsCount > 0 && (
              <span className="badge">{stats.newLogsCount}</span>
            )}
          </button>
          <button
            className={activeTab === 'history' ? 'active' : ''}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>
      </div>
      
      {/* Controls */}
      <div className="log-controls">
        {/* Filters */}
        <div className="filter-section">
          <div className="filter-group">
            <label>Sources:</label>
            <div className="filter-options">
              {availableSources.map(source => (
                <label key={source} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.sources.includes(source)}
                    onChange={() => handleSourceToggle(source)}
                  />
                  <span className={`source-tag ${getSourceClass(source)}`}>
                    {source}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="filter-group">
            <label>Levels:</label>
            <div className="filter-options">
              {availableLevels.map(level => (
                <label key={level} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.levels.includes(level)}
                    onChange={() => handleLevelToggle(level)}
                  />
                  <span className={`level-tag ${getLevelClass(level)}`}>
                    {level}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="filter-group">
            <label>Search:</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Search logs..."
              className="search-input"
            />
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="action-buttons">
          {activeTab === 'realtime' && (
            <>
              <button
                onClick={isConnected ? disconnect : connect}
                className={isConnected ? 'disconnect-btn' : 'connect-btn'}
              >
                {isConnected ? 'Disconnect' : 'Connect'}
              </button>
              <button onClick={clearLogs} className="clear-btn">
                Clear
              </button>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                />
                Auto-scroll
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showTimestamps}
                  onChange={(e) => setShowTimestamps(e.target.checked)}
                />
                Show timestamps
              </label>
            </>
          )}
          
          {activeTab === 'history' && (
            <>
              <button
                onClick={() => handleFetchHistory(15)}
                disabled={historyLoading}
                className="fetch-btn"
              >
                Last 15 min
              </button>
              <button
                onClick={() => handleFetchHistory(60)}
                disabled={historyLoading}
                className="fetch-btn"
              >
                Last hour
              </button>
              <button
                onClick={() => handleFetchHistory(1440)}
                disabled={historyLoading}
                className="fetch-btn"
              >
                Last 24h
              </button>
              
              <div className="export-buttons">
                <button onClick={() => handleExport('json')} className="export-btn">
                  Export JSON
                </button>
                <button onClick={() => handleExport('csv')} className="export-btn">
                  Export CSV
                </button>
                <button onClick={() => handleExport('txt')} className="export-btn">
                  Export TXT
                </button>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Status Bar */}
      <div className="status-bar">
        {activeTab === 'realtime' && (
          <>
            <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '● Connected' : '○ Disconnected'}
            </span>
            <span>Total: {stats.totalLogs}</span>
            <span>Displaying: {filteredLogs.length}</span>
            {stats.connectionTime && (
              <span>Connected: {formatTimestamp(stats.connectionTime)}</span>
            )}
          </>
        )}
        
        {activeTab === 'history' && (
          <>
            <span>Loaded: {historyLogs.length}</span>
            <span>Filtered: {filteredLogs.length}</span>
            {historyLoading && <span>Loading...</span>}
          </>
        )}
        
        {(streamError || historyError) && (
          <span className="error-status">
            Error: {streamError || historyError}
          </span>
        )}
      </div>
      
      {/* Log Display */}
      <div
        id="log-container"
        className="log-container"
        onScroll={(e) => {
          // Reset new logs count when user scrolls to top
          if (e.target.scrollTop === 0 && stats.newLogsCount > 0) {
            resetNewLogsCount();
          }
        }}
      >
        {filteredLogs.length === 0 ? (
          <div className="no-logs">
            {activeTab === 'realtime' 
              ? (isConnected ? 'Waiting for logs...' : 'Not connected')
              : 'No logs found. Try fetching history or adjusting filters.'
            }
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={`${log.timestamp}-${index}`} className={`log-entry ${getLevelClass(log.level)}`}>
              <div className="log-header">
                {showTimestamps && (
                  <span className="log-timestamp">
                    {formatTimestamp(log.timestamp)}
                  </span>
                )}
                <span className={`log-source ${getSourceClass(log.source)}`}>
                  [{log.source}]
                </span>
                <span className={`log-level ${getLevelClass(log.level)}`}>
                  {log.level}
                </span>
                <span className="log-logger">
                  {log.logger_name}
                </span>
                {log.filename !== 'unknown' && (
                  <span className="log-location">
                    {log.filename}:{log.line_number}
                  </span>
                )}
              </div>
              <div className="log-message">
                {log.message}
              </div>
              {log.extra_data?.stack && (
                <details className="log-stack">
                  <summary>Stack trace</summary>
                  <pre>{log.extra_data.stack}</pre>
                </details>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogViewer;