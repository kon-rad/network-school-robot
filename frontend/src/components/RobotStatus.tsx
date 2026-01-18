import type { RobotStatus as RobotStatusType } from '../types';

interface RobotStatusProps {
  status: RobotStatusType | null;
  loading: boolean;
  error: string | null;
}

export function RobotStatus({ status, loading, error }: RobotStatusProps) {
  if (loading && !status) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-[var(--text-secondary)]">Loading status...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="flex items-center gap-3 text-[var(--error)]">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm">Error: {error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-[var(--text-primary)]">Robot Status</h2>
          <span className={`badge ${status?.connected ? 'badge-success' : 'badge-warning'}`}>
            <span className={`status-indicator ${status?.connected ? 'online' : 'warning'}`} />
            {status?.connected ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="card-body space-y-4">
        {/* Connection Info */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--text-secondary)]">Connection</span>
            <span className={`text-sm font-medium ${status?.connected ? 'text-[var(--success)]' : 'text-[var(--text-tertiary)]'}`}>
              {status?.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--text-secondary)]">Mode</span>
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {status?.connection_mode || 'N/A'}
            </span>
          </div>

          {status?.last_heartbeat && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Last Heartbeat</span>
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {new Date(status.last_heartbeat).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>

        {/* Robot Info */}
        {status?.robot_info && (
          <>
            <div className="border-t border-[var(--border-default)] pt-4">
              <h3 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Hardware</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">Type</span>
                  <span className="text-sm font-medium text-[var(--text-primary)] capitalize">
                    {status.robot_info.mode}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">SDK Version</span>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    v{status.robot_info.sdk_version}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* IMU Data */}
        {status?.imu_data && (status.imu_data.accelerometer || status.imu_data.gyroscope) && (
          <div className="border-t border-[var(--border-default)] pt-4">
            <h3 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-3">IMU Data</h3>

            {status.imu_data.accelerometer && (
              <div className="mb-3">
                <span className="text-xs text-[var(--text-tertiary)]">Accelerometer</span>
                <div className="grid grid-cols-3 gap-2 mt-1">
                  {['X', 'Y', 'Z'].map((axis, i) => (
                    <div key={axis} className="bg-[var(--bg-tertiary)] rounded p-2 text-center">
                      <div className="text-xs text-[var(--text-tertiary)]">{axis}</div>
                      <div className="text-sm font-mono text-[var(--text-primary)]">
                        {status.imu_data!.accelerometer![i].toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {status.imu_data.gyroscope && (
              <div>
                <span className="text-xs text-[var(--text-tertiary)]">Gyroscope</span>
                <div className="grid grid-cols-3 gap-2 mt-1">
                  {['X', 'Y', 'Z'].map((axis, i) => (
                    <div key={axis} className="bg-[var(--bg-tertiary)] rounded p-2 text-center">
                      <div className="text-xs text-[var(--text-tertiary)]">{axis}</div>
                      <div className="text-sm font-mono text-[var(--text-primary)]">
                        {status.imu_data!.gyroscope![i].toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
