import './App.css';
import { ConnectionIndicator } from './components/ConnectionIndicator';
import { RobotStatus } from './components/RobotStatus';
import { LogViewer } from './components/LogViewer';
import { useWebSocket } from './hooks/useWebSocket';
import { useRobotStatus } from './hooks/useRobotStatus';

function App() {
  const { connected: wsConnected, logs, clearLogs } = useWebSocket();
  const { status, loading, error, refetch } = useRobotStatus(5000);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold">Network School Robot Dashboard</h1>
          <ConnectionIndicator
            wsConnected={wsConnected}
            robotConnected={status?.connected ?? false}
            onRobotStatusChange={refetch}
          />
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <aside className="lg:col-span-1">
            <RobotStatus status={status} loading={loading} error={error} />
          </aside>
          <section className="lg:col-span-2">
            <LogViewer logs={logs} onClearLogs={clearLogs} />
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
