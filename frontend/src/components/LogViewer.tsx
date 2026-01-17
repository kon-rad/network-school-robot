import { useRef, useEffect, useState } from 'react';
import type { LogEntry } from '../types';

interface LogViewerProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

const levelColors: Record<string, string> = {
  INFO: 'text-blue-400',
  WARN: 'text-yellow-400',
  ERROR: 'text-red-400',
  DEBUG: 'text-gray-400',
};

const levelBgColors: Record<string, string> = {
  INFO: 'bg-blue-900/30',
  WARN: 'bg-yellow-900/30',
  ERROR: 'bg-red-900/30',
  DEBUG: 'bg-gray-900/30',
};

export function LogViewer({ logs, onClearLogs }: LogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<string>('ALL');

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  const filteredLogs = filter === 'ALL'
    ? logs
    : logs.filter((log) => log.level === filter);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="bg-gray-800 rounded-lg flex flex-col h-[600px]">
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold">Logs</h2>

        <div className="flex items-center gap-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1 rounded text-sm border border-gray-600"
          >
            <option value="ALL">All Levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warning</option>
            <option value="ERROR">Error</option>
          </select>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1 rounded text-sm ${
              autoScroll
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            Auto-scroll: {autoScroll ? 'On' : 'Off'}
          </button>

          <button
            onClick={onClearLogs}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No logs to display. Connect to the robot to see logs.
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={log.id || index}
                className={`flex gap-3 p-2 rounded ${levelBgColors[log.level] || ''}`}
              >
                <span className="text-gray-500 shrink-0">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span
                  className={`shrink-0 w-14 ${levelColors[log.level] || 'text-white'}`}
                >
                  [{log.level}]
                </span>
                <span className="text-purple-400 shrink-0">
                  {log.source}
                </span>
                <span className="text-white break-all">
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-2 border-t border-gray-700 text-sm text-gray-500">
        {filteredLogs.length} log entries
        {filter !== 'ALL' && ` (filtered from ${logs.length} total)`}
      </div>
    </div>
  );
}
