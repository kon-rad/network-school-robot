import { useState, useEffect, useCallback } from 'react';
import { robotApi } from '../services/api';
import type { RobotStatus } from '../types';

interface UseRobotStatusResult {
  status: RobotStatus | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useRobotStatus(pollInterval: number = 5000): UseRobotStatusResult {
  const [status, setStatus] = useState<RobotStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await robotApi.getStatus();
      setStatus(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();

    const interval = setInterval(fetchStatus, pollInterval);

    return () => clearInterval(interval);
  }, [fetchStatus, pollInterval]);

  return { status, loading, error, refetch: fetchStatus };
}
