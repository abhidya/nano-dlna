#!/usr/bin/env python3

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

from log_aggregation_service import get_log_aggregation_service, log_frontend_event

try:
    from logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])

# Get the log aggregation service
log_service = get_log_aggregation_service()

@router.get("/")
async def get_logs(
    sources: Optional[List[str]] = Query(None, description="Filter by log sources"),
    levels: Optional[List[str]] = Query(None, description="Filter by log levels"), 
    since_minutes: Optional[int] = Query(None, description="Get logs from last N minutes"),
    limit: int = Query(1000, description="Maximum number of logs to return"),
    search: Optional[str] = Query(None, description="Search term for filtering logs")
):
    """Get filtered logs from all sources"""
    
    since = None
    if since_minutes:
        since = datetime.now() - timedelta(minutes=since_minutes)
    
    logs = log_service.get_logs(
        sources=sources,
        levels=levels,
        since=since,
        limit=limit,
        search=search
    )
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "sources": sources,
            "levels": levels,
            "since_minutes": since_minutes,
            "search": search
        }
    }

@router.get("/sources")
async def get_log_sources():
    """Get available log sources"""
    sources = list(log_service.collectors.keys())
    return {"sources": sources}

@router.get("/levels")
async def get_log_levels():
    """Get available log levels"""
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    return {"levels": levels}

@router.get("/stats")
async def get_log_stats():
    """Get logging statistics"""
    total_logs = len(log_service.log_buffer)
    
    # Count by source
    source_counts = {}
    level_counts = {}
    
    for log in log_service.log_buffer:
        source_counts[log.source] = source_counts.get(log.source, 0) + 1
        level_counts[log.level] = level_counts.get(log.level, 0) + 1
    
    # Recent activity (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_logs = [log for log in log_service.log_buffer if log.timestamp >= one_hour_ago]
    
    return {
        "total_logs": total_logs,
        "recent_logs_1h": len(recent_logs),
        "sources": source_counts,
        "levels": level_counts,
        "collectors": len(log_service.collectors),
        "active_websockets": len(log_service.websocket_clients)
    }

@router.get("/stream")
async def stream_logs(
    sources: Optional[List[str]] = Query(None),
    levels: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None)
):
    """Stream logs via Server-Sent Events"""
    return await log_service.stream_logs_sse(sources=sources, levels=levels, search=search)

@router.websocket("/ws")
async def websocket_log_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()
    log_service.add_websocket_client(websocket)
    
    try:
        # Send initial batch of recent logs
        recent_logs = log_service.get_logs(limit=50)
        for log in reversed(recent_logs):  # Send oldest first
            await websocket.send_text(json.dumps(log))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client message (for potential filtering updates)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                
                # Handle filter updates from client
                try:
                    filter_data = json.loads(message)
                    if filter_data.get('type') == 'filter_update':
                        # Client can send filter updates, but for now we just acknowledge
                        await websocket.send_text(json.dumps({
                            "type": "filter_ack",
                            "message": "Filter update received"
                        }))
                except json.JSONDecodeError:
                    pass  # Ignore invalid JSON
                    
            except asyncio.TimeoutError:
                # No message received, continue
                pass
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        log_service.remove_websocket_client(websocket)

@router.post("/frontend")
async def submit_frontend_log(request_data: Dict[str, Any]):
    """Endpoint for frontend to submit console logs"""
    try:
        # Handle both single log and batch of logs
        if 'logs' in request_data:
            # Batch of logs
            logs = request_data['logs']
            if not isinstance(logs, list):
                raise HTTPException(status_code=400, detail="Logs must be a list")
            
            processed_count = 0
            for log_data in logs:
                if 'message' in log_data:
                    # Add timestamp if not provided
                    if 'timestamp' not in log_data:
                        log_data['timestamp'] = datetime.now().timestamp()
                    
                    # Process the frontend log
                    log_frontend_event(log_data)
                    processed_count += 1
            
            return {"status": "success", "message": f"Processed {processed_count} logs"}
        else:
            # Single log
            if 'message' not in request_data:
                raise HTTPException(status_code=400, detail="Message field is required")
            
            # Add timestamp if not provided
            if 'timestamp' not in request_data:
                request_data['timestamp'] = datetime.now().timestamp()
            
            # Process the frontend log
            log_frontend_event(request_data)
            
            return {"status": "success", "message": "Log received"}
        
    except Exception as e:
        logger.error(f"Error processing frontend log: {e}")
        raise HTTPException(status_code=500, detail="Error processing log")

@router.get("/export")
async def export_logs(
    sources: Optional[List[str]] = Query(None),
    levels: Optional[List[str]] = Query(None),
    since_minutes: Optional[int] = Query(60, description="Export logs from last N minutes"),
    format: str = Query("json", description="Export format: json, csv, txt")
):
    """Export logs in various formats"""
    
    since = datetime.now() - timedelta(minutes=since_minutes)
    logs = log_service.get_logs(
        sources=sources,
        levels=levels,
        since=since,
        limit=10000  # Allow larger export
    )
    
    if format == "json":
        def generate():
            yield json.dumps({"logs": logs, "exported_at": datetime.now().isoformat()}, indent=2)
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )
    
    elif format == "csv":
        import csv
        import io
        
        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["timestamp", "level", "source", "logger", "message", "filename", "line"])
            
            # Write logs
            for log in logs:
                writer.writerow([
                    log["timestamp"],
                    log["level"],
                    log["source"],
                    log["logger_name"],
                    log["message"],
                    log["filename"],
                    log["line_number"]
                ])
            
            output.seek(0)
            yield output.getvalue()
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    
    elif format == "txt":
        def generate():
            for log in logs:
                timestamp = log["timestamp"]
                level = log["level"]
                source = log["source"]
                logger_name = log["logger_name"]
                message = log["message"]
                yield f"[{timestamp}] {level} [{source}] {logger_name}: {message}\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use: json, csv, txt")

@router.get("/tail/{source}")
async def tail_log_source(
    source: str,
    lines: int = Query(100, description="Number of lines to tail")
):
    """Tail logs from a specific source"""
    if source not in log_service.collectors:
        raise HTTPException(status_code=404, detail=f"Log source '{source}' not found")
    
    # Get recent logs from this source
    logs = log_service.get_logs(sources=[source], limit=lines)
    
    return {
        "source": source,
        "lines": lines,
        "logs": logs
    }

@router.post("/clear")
async def clear_log_buffer():
    """Clear the log buffer (admin function)"""
    log_service.log_buffer.clear()
    return {"status": "success", "message": "Log buffer cleared"}

# Health check for the logging system
@router.get("/health")
async def logging_health_check():
    """Health check for the logging system"""
    health_info = {
        "status": "healthy",
        "collectors": len(log_service.collectors),
        "buffer_size": len(log_service.log_buffer),
        "websocket_clients": len(log_service.websocket_clients),
        "collectors_status": {}
    }
    
    # Check each collector
    for name, collector in log_service.collectors.items():
        health_info["collectors_status"][name] = {
            "running": collector.is_running,
            "type": type(collector).__name__
        }
    
    return health_info