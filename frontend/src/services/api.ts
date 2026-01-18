import type { RobotStatus, ActionResponse, LogsResponse, ChatResponse, ChatStatusResponse, ChatHistoryResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}

export const robotApi = {
  getStatus: async (): Promise<RobotStatus> => {
    const response = await fetch(`${API_BASE}/api/robot/status`);
    return handleResponse<RobotStatus>(response);
  },

  connect: async (connectionMode: string = 'auto'): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ connection_mode: connectionMode }),
    });
    return handleResponse<ActionResponse>(response);
  },

  disconnect: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/disconnect`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

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

  sendMessage: async (message: string): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE}/api/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    return handleResponse<ChatResponse>(response);
  },

  streamMessage: async function* (message: string): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
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
            const parsed = JSON.parse(data);
            if (parsed.content) {
              yield parsed.content;
            }
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
