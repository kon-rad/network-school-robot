export interface RobotStatus {
  connected: boolean;
  connection_mode: string;
  robot_host?: string;
  last_heartbeat: string | null;
  robot_info: RobotInfo | null;
  imu_data: IMUData | null;
  audio_status?: AudioStatus;
}

export interface RobotInfo {
  mode: string;
  sdk_version: string;
  has_camera?: boolean;
  has_audio?: boolean;
}

export interface IMUData {
  accelerometer: number[] | null;
  gyroscope: number[] | null;
  quaternion: number[] | null;
}

export interface AudioStatus {
  playing: boolean;
  recording: boolean;
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
  host?: string;
}

export interface ActionResult {
  action: string;
  success: boolean;
  message: string;
  image_base64?: string;
  format?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  page: number;
  limit: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actions?: string[];
  actionResults?: ActionResult[];
  timestamp: Date;
}

export interface ChatResponse {
  response: string;
  actions: string[];
  action_results: ActionResult[];
}

export interface ChatStatusResponse {
  configured: boolean;
  model: string;
  robot_connected: boolean;
  auto_execute_actions: boolean;
}

export interface HistoryMessage {
  role: string;
  content: string;
}

export interface ChatHistoryResponse {
  history: HistoryMessage[];
  configured: boolean;
}

export interface ConversationResponse {
  response: string;
  actions: string[];
  action_results: ActionResult[];
  robot_connected: boolean;
}

export interface HeadMoveRequest {
  x?: number;
  y?: number;
  z?: number;
  roll?: number;
  duration?: number;
  method?: string;
}

export interface AntennaMoveRequest {
  left_angle?: number;
  right_angle?: number;
  duration?: number;
  method?: string;
}

export interface BodyRotateRequest {
  yaw_degrees?: number;
  duration?: number;
  method?: string;
}

export interface StreamEvent {
  content?: string;
  actions?: string[];
  action_results?: ActionResult[];
}
