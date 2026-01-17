export interface RobotStatus {
  connected: boolean;
  connection_mode: string;
  last_heartbeat: string | null;
  robot_info: RobotInfo | null;
  imu_data: IMUData | null;
}

export interface RobotInfo {
  mode: string;
  sdk_version: string;
}

export interface IMUData {
  accelerometer: number[] | null;
  gyroscope: number[] | null;
  quaternion: number[] | null;
}

export interface LogEntry {
  id?: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface ActionResponse {
  success: boolean;
  message: string;
  connection_mode?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  page: number;
  limit: number;
}
