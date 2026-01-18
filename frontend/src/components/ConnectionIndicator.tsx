import { useState } from 'react';
import { robotApi } from '../services/api';

interface ConnectionIndicatorProps {
  wsConnected: boolean;
  robotConnected: boolean;
  onRobotStatusChange: () => void;
}

export function ConnectionIndicator({
  wsConnected,
  robotConnected,
  onRobotStatusChange,
}: ConnectionIndicatorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await robotApi.connect();
      if (!result.success) {
        setError(result.message);
      }
      onRobotStatusChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await robotApi.disconnect();
      if (!result.success) {
        setError(result.message);
      }
      onRobotStatusChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Disconnect failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row items-end md:items-center gap-3 md:gap-4 relative">
      {/* Status Indicators */}
      <div className="flex items-center gap-4">
        {/* WebSocket Status */}
        <div className="flex items-center gap-2">
          <span className={`status-indicator ${wsConnected ? 'online' : 'offline'}`} />
          <div className="hidden sm:flex flex-col">
            <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider">WebSocket</span>
            <span className={`text-xs font-medium ${wsConnected ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
              {wsConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-8 bg-[var(--border-default)]" />

        {/* Robot Status */}
        <div className="flex items-center gap-2">
          <span className={`status-indicator ${robotConnected ? 'online' : 'warning'}`} />
          <div className="hidden sm:flex flex-col">
            <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider">Robot</span>
            <span className={`text-xs font-medium ${robotConnected ? 'text-[var(--success)]' : 'text-[var(--warning)]'}`}>
              {robotConnected ? 'Synced' : 'Standby'}
            </span>
          </div>
        </div>
      </div>

      {/* Connect/Disconnect Button */}
      <div className="flex items-center gap-2">
        {!robotConnected ? (
          <button
            onClick={handleConnect}
            disabled={loading}
            className="btn btn-sm btn-success"
          >
            {loading ? (
              <>
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span className="hidden sm:inline">Connecting</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="hidden sm:inline">Connect</span>
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            disabled={loading}
            className="btn btn-sm btn-danger"
          >
            {loading ? (
              <>
                <span className="w-3 h-3 border-2 border-[var(--error)] border-t-transparent rounded-full animate-spin" />
                <span className="hidden sm:inline">Disconnecting</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
                <span className="hidden sm:inline">Disconnect</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute top-full right-0 mt-2 px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--error)] rounded-lg text-[var(--error)] text-xs max-w-xs shadow-lg">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
}
