import { useRef, useEffect, useState } from 'react';
import type { LogEntry } from '../types';

interface LogViewerProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

const levelConfig: Record<string, { color: string; bg: string; icon: string }> = {
  INFO: {
    color: 'text-[var(--info)]',
    bg: 'bg-[var(--info)]/5 border-l-2 border-[var(--info)]/50',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  WARN: {
    color: 'text-[var(--warning)]',
    bg: 'bg-[var(--warning)]/5 border-l-2 border-[var(--warning)]/50',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  ERROR: {
    color: 'text-[var(--error)]',
    bg: 'bg-[var(--error)]/5 border-l-2 border-[var(--error)]/50',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  DEBUG: {
    color: 'text-[var(--text-tertiary)]',
    bg: 'bg-[var(--bg-tertiary)] border-l-2 border-[var(--border-default)]',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
  },
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
    <div className="card flex flex-col h-[600px]">
      {/* Header */}
      <div className="card-header flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--accent-secondary)]/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--accent-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <h2 className="font-medium text-[var(--text-primary)]">System Logs</h2>
            <p className="text-xs text-[var(--text-tertiary)]">{filteredLogs.length} entries</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Dropdown */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="select"
          >
            <option value="ALL">All Levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warning</option>
            <option value="ERROR">Error</option>
          </select>

          {/* Auto-scroll Toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`btn btn-sm ${autoScroll ? 'btn-primary' : 'btn-secondary'}`}
          >
            <svg className={`w-4 h-4 ${autoScroll ? 'animate-bounce' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            <span className="hidden sm:inline">Auto</span>
          </button>

          {/* Clear Button */}
          <button onClick={onClearLogs} className="btn btn-sm btn-ghost">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </div>

      {/* Log Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs bg-[var(--bg-primary)]"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-[var(--text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-1">No logs yet</h3>
            <p className="text-sm text-[var(--text-secondary)]">Connect to the robot to start streaming logs</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => {
              const config = levelConfig[log.level] || levelConfig.DEBUG;
              return (
                <div
                  key={log.id || index}
                  className={`flex items-start gap-3 p-2 rounded ${config.bg} animate-fade-in`}
                >
                  {/* Timestamp */}
                  <span className="text-[var(--text-tertiary)] shrink-0 tabular-nums">
                    {formatTimestamp(log.timestamp)}
                  </span>

                  {/* Level Badge */}
                  <span className={`shrink-0 flex items-center gap-1 ${config.color}`}>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={config.icon} />
                    </svg>
                    <span className="w-12 font-medium">[{log.level}]</span>
                  </span>

                  {/* Source */}
                  <span className="text-[var(--accent-secondary)] shrink-0 w-24 truncate">
                    {log.source}
                  </span>

                  {/* Message */}
                  <span className="text-[var(--text-primary)] break-all flex-1">
                    {log.message}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Status Bar */}
      <div className="px-4 py-3 border-t border-[var(--border-default)] bg-[var(--bg-tertiary)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
            <span className="flex items-center gap-2">
              <span className="status-indicator online" />
              Stream active
            </span>
            <span>
              {filteredLogs.length} / {logs.length} entries
              {filter !== 'ALL' && ` (${filter})`}
            </span>
          </div>

          <div className="text-xs font-mono text-[var(--text-tertiary)]">
            tail -f /var/log/reachy.log
          </div>
        </div>
      </div>
    </div>
  );
}
