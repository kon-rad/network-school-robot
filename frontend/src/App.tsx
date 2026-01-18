import './App.css';
import { useState } from 'react';
import { ConnectionIndicator } from './components/ConnectionIndicator';
import { RobotStatus } from './components/RobotStatus';
import { LogViewer } from './components/LogViewer';
import { ChatInterface } from './components/ChatInterface';
import { CameraView } from './components/CameraView';
import { useWebSocket } from './hooks/useWebSocket';
import { useRobotStatus } from './hooks/useRobotStatus';

function App() {
  const { connected: wsConnected, logs, clearLogs } = useWebSocket();
  const { status, loading, error, refetch } = useRobotStatus(5000);
  const [activeTab, setActiveTab] = useState<'chat' | 'camera' | 'logs'>('chat');

  const handleRobotAction = async (action: string) => {
    console.log('Executing robot action:', action);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/api/robot/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (!response.ok) {
        console.error('Action failed:', await response.text());
      }
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--accent-primary)] flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-[var(--text-primary)]">Network School</h1>
                <p className="text-xs text-[var(--text-tertiary)]">Reachy Robot Interface</p>
              </div>
            </div>

            {/* Connection Status */}
            <ConnectionIndicator
              wsConnected={wsConnected}
              robotConnected={status?.connected ?? false}
              onRobotStatusChange={refetch}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-4 xl:col-span-3 space-y-6">
            <RobotStatus status={status} loading={loading} error={error} />
          </aside>

          {/* Main Panel */}
          <section className="lg:col-span-8 xl:col-span-9">
            {/* Tabs */}
            <div className="tabs mb-6">
              <button
                onClick={() => setActiveTab('chat')}
                className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  Chat
                </span>
              </button>
              <button
                onClick={() => setActiveTab('camera')}
                className={`tab ${activeTab === 'camera' ? 'active' : ''}`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Camera
                </span>
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  Logs
                </span>
              </button>
            </div>

            {/* Content */}
            <div className="animate-fade-in">
              {activeTab === 'chat' && (
                <ChatInterface onAction={handleRobotAction} />
              )}
              {activeTab === 'camera' && (
                <CameraView />
              )}
              {activeTab === 'logs' && (
                <LogViewer logs={logs} onClearLogs={clearLogs} />
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
