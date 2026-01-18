import type {
  RobotStatus,
  ActionResponse,
  LogsResponse,
  ChatResponse,
  ChatStatusResponse,
  ChatHistoryResponse,
  ConversationResponse,
  HeadMoveRequest,
  AntennaMoveRequest,
  BodyRotateRequest,
  StreamEvent,
  ActionResult,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}

export const robotApi = {
  // Connection
  getStatus: async (): Promise<RobotStatus> => {
    const response = await fetch(`${API_BASE}/api/robot/status`);
    return handleResponse<RobotStatus>(response);
  },

  connect: async (connectionMode: string = 'auto', host?: string): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ connection_mode: connectionMode, host }),
    });
    return handleResponse<ActionResponse>(response);
  },

  disconnect: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/disconnect`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  // Actions
  executeAction: async (action: string): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    return handleResponse<ActionResponse>(response);
  },

  executeActions: async (actions: string[]): Promise<{ results: ActionResult[] }> => {
    const response = await fetch(`${API_BASE}/api/robot/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actions }),
    });
    return handleResponse<{ results: ActionResult[] }>(response);
  },

  // Head
  moveHead: async (request: HeadMoveRequest): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/head/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ActionResponse>(response);
  },

  lookAtUser: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/head/look-at-user`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  nod: async (times: number = 2): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/head/nod?times=${times}`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  shakeHead: async (times: number = 2): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/head/shake?times=${times}`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  tiltHead: async (roll: number = 15, duration: number = 0.5): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/head/tilt?roll=${roll}&duration=${duration}`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  // Antennas
  moveAntennas: async (request: AntennaMoveRequest): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/antennas/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ActionResponse>(response);
  },

  wiggleAntennas: async (times: number = 3, angle: number = 30): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/antennas/wiggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ times, angle }),
    });
    return handleResponse<ActionResponse>(response);
  },

  raiseAntennas: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/antennas/raise`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  lowerAntennas: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/antennas/lower`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  // Body
  rotateBody: async (request: BodyRotateRequest): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/body/rotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ActionResponse>(response);
  },

  // Emotions
  expressEmotion: async (emotion: string): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/emotion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emotion }),
    });
    return handleResponse<ActionResponse>(response);
  },

  // Audio
  startRecording: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/start-recording`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  stopRecording: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/stop-recording`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  startPlaying: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/start-playing`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  stopPlaying: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/stop-playing`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  stopAudio: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/stop`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  getVoiceDirection: async (): Promise<{ direction_of_arrival: number | null; speech_detected: boolean }> => {
    const response = await fetch(`${API_BASE}/api/robot/audio/voice-direction`);
    return handleResponse(response);
  },

  // Logs
  getLogs: async (page: number = 1, limit: number = 50): Promise<LogsResponse> => {
    const response = await fetch(`${API_BASE}/api/logs?page=${page}&limit=${limit}`);
    return handleResponse<LogsResponse>(response);
  },

  clearLogs: async (): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE}/api/logs`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export const getWebSocketUrl = (): string => {
  const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  return `${wsBase}/api/logs/stream`;
};

export const chatApi = {
  getStatus: async (): Promise<ChatStatusResponse> => {
    const response = await fetch(`${API_BASE}/api/chat/status`);
    return handleResponse<ChatStatusResponse>(response);
  },

  sendMessage: async (message: string, executeActions?: boolean): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE}/api/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, execute_actions: executeActions }),
    });
    return handleResponse<ChatResponse>(response);
  },

  conversation: async (
    message: string,
    executeActions?: boolean,
    autoConnect?: boolean
  ): Promise<ConversationResponse> => {
    const response = await fetch(`${API_BASE}/api/chat/conversation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        execute_actions: executeActions,
        auto_connect: autoConnect,
      }),
    });
    return handleResponse<ConversationResponse>(response);
  },

  streamMessage: async function* (
    message: string,
    executeActions?: boolean
  ): AsyncGenerator<StreamEvent, void, unknown> {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, execute_actions: executeActions }),
    });

    if (!response.ok) {
      throw new Error('Stream request failed');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No reader available');

    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            const parsed: StreamEvent = JSON.parse(data);
            yield parsed;
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  },

  getHistory: async (): Promise<ChatHistoryResponse> => {
    const response = await fetch(`${API_BASE}/api/chat/history`);
    return handleResponse<ChatHistoryResponse>(response);
  },

  clearHistory: async (): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE}/api/chat/history`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};
