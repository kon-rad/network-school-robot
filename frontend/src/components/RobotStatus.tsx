import type { RobotStatus as RobotStatusType } from '../types';

interface RobotStatusProps {
  status: RobotStatusType | null;
  loading: boolean;
  error: string | null;
}

export function RobotStatus({ status, loading, error }: RobotStatusProps) {
  if (loading && !status) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Robot Status</h2>
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Robot Status</h2>
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Robot Status</h2>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">Connection</span>
          <span
            className={`px-3 py-1 rounded-full text-sm ${
              status?.connected
                ? 'bg-green-900 text-green-300'
                : 'bg-red-900 text-red-300'
            }`}
          >
            {status?.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400">Mode</span>
          <span className="text-white">
            {status?.connection_mode || 'N/A'}
          </span>
        </div>

        {status?.last_heartbeat && (
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Last Heartbeat</span>
            <span className="text-white text-sm">
              {new Date(status.last_heartbeat).toLocaleTimeString()}
            </span>
          </div>
        )}

        {status?.robot_info && (
          <>
            <hr className="border-gray-700" />
            <h3 className="text-lg font-medium">Robot Info</h3>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Type</span>
              <span className="text-white capitalize">
                {status.robot_info.mode}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">SDK Version</span>
              <span className="text-white">
                {status.robot_info.sdk_version}
              </span>
            </div>
          </>
        )}

        {status?.imu_data && (
          <>
            <hr className="border-gray-700" />
            <h3 className="text-lg font-medium">IMU Data</h3>
            {status.imu_data.accelerometer && (
              <div>
                <span className="text-gray-400 text-sm">Accelerometer</span>
                <div className="text-white text-sm font-mono">
                  {status.imu_data.accelerometer.map((v) => v.toFixed(2)).join(', ')}
                </div>
              </div>
            )}
            {status.imu_data.gyroscope && (
              <div>
                <span className="text-gray-400 text-sm">Gyroscope</span>
                <div className="text-white text-sm font-mono">
                  {status.imu_data.gyroscope.map((v) => v.toFixed(2)).join(', ')}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
