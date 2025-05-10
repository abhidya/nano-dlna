#!/bin/bash

# Script to view and monitor dashboard logs
# Usage: ./view_dashboard_logs.sh [options]
#   Options:
#     -f, --follow     Follow the log file (like tail -f)
#     -n, --lines N    Show the last N lines (default: 50)
#     -l, --level LVL  Filter by log level (INFO, WARNING, ERROR, DEBUG)
#     -h, --help       Show this help message

# Default values
FOLLOW=false
LINES=50
LEVEL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    -n|--lines)
      LINES="$2"
      shift 2
      ;;
    -l|--level)
      LEVEL="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: ./view_dashboard_logs.sh [options]"
      echo "  Options:"
      echo "    -f, --follow     Follow the log file (like tail -f)"
      echo "    -n, --lines N    Show the last N lines (default: 50)"
      echo "    -l, --level LVL  Filter by log level (INFO, WARNING, ERROR, DEBUG)"
      echo "    -h, --help       Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Check if log file exists
LOG_FILE="dashboard_run.log"
if [ ! -f "$LOG_FILE" ]; then
  echo "Error: Log file $LOG_FILE not found!"
  echo "The dashboard may not be running or logs are being written elsewhere."
  exit 1
fi

# Build the command based on options
CMD="cat"
if $FOLLOW; then
  CMD="tail -f"
else
  CMD="tail -n $LINES"
fi

# Apply level filtering if specified
if [ -n "$LEVEL" ]; then
  case $LEVEL in
    INFO|WARNING|ERROR|DEBUG|CRITICAL)
      echo "Showing $LEVEL level logs:"
      $CMD "$LOG_FILE" | grep -i "$LEVEL"
      ;;
    *)
      echo "Invalid log level: $LEVEL"
      echo "Valid levels are: INFO, WARNING, ERROR, DEBUG, CRITICAL"
      exit 1
      ;;
  esac
else
  # No filtering, show all logs
  echo "Showing last $LINES lines of logs:"
  $CMD "$LOG_FILE"
fi
