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
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className={`w-3 h-3 rounded-full ${
              wsConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-400">
            WebSocket: {wsConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`w-3 h-3 rounded-full ${
              robotConnected ? 'bg-green-500' : 'bg-yellow-500'
            }`}
          />
          <span className="text-sm text-gray-400">
            Robot: {robotConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {!robotConnected ? (
          <button
            onClick={handleConnect}
            disabled={loading}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white text-sm rounded transition-colors"
          >
            {loading ? 'Connecting...' : 'Connect Robot'}
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            disabled={loading}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white text-sm rounded transition-colors"
          >
            {loading ? 'Disconnecting...' : 'Disconnect'}
          </button>
        )}
      </div>

      {error && (
        <span className="text-red-400 text-sm">{error}</span>
      )}
    </div>
  );
}
