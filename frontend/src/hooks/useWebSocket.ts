import { useState, useEffect, useCallback, useRef } from 'react';
import { getWebSocketUrl } from '../services/api';
import type { LogEntry } from '../types';

interface UseWebSocketResult {
  connected: boolean;
  logs: LogEntry[];
  clearLogs: () => void;
}

export function useWebSocket(): UseWebSocketResult {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(getWebSocketUrl());

    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');

      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle connection confirmation
        if (data.type === 'connected') {
          console.log('Log stream connected:', data.message);
          return;
        }

        // Handle log entries
        if (data.timestamp && data.level && data.message) {
          setLogs((prevLogs) => {
            const newLogs = [...prevLogs, data as LogEntry];
            // Keep only the last 500 logs to prevent memory issues
            if (newLogs.length > 500) {
              return newLogs.slice(-500);
            }
            return newLogs;
          });
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { connected, logs, clearLogs };
}
