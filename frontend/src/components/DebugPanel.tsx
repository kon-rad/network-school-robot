import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface CommandResult {
  success: boolean;
  message?: string;
  response?: unknown;
  error?: string;
}

const PRESET_COMMANDS = [
  { id: 'wake_up', label: 'Wake Up', icon: '☀️' },
  { id: 'sleep', label: 'Sleep', icon: '😴' },
  { id: 'look_center', label: 'Look Center', icon: '👀' },
  { id: 'nod', label: 'Nod', icon: '✓' },
  { id: 'shake', label: 'Shake Head', icon: '✗' },
  { id: 'wiggle', label: 'Wiggle Antennas', icon: '📡' },
  { id: 'happy', label: 'Happy', icon: '😊' },
  { id: 'sad', label: 'Sad', icon: '😢' },
  { id: 'curious', label: 'Curious', icon: '🤔' },
];

export function DebugPanel() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [rawEndpoint, setRawEndpoint] = useState('/api/daemon/status');
  const [rawMethod, setRawMethod] = useState('GET');
  const [rawBody, setRawBody] = useState('');

  // Head position controls
  const [headX, setHeadX] = useState(0);
  const [headY, setHeadY] = useState(0);
  const [headZ, setHeadZ] = useState(0);
  const [headRoll, setHeadRoll] = useState(0);

  const executePreset = async (command: string) => {
    setLoading(command);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/robot/debug/preset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult({ success: false, error: String(err) });
    } finally {
      setLoading(null);
    }
  };

  const executeRaw = async () => {
    setLoading('raw');
    setResult(null);
    try {
      const body: { endpoint: string; method: string; body?: unknown } = {
        endpoint: rawEndpoint,
        method: rawMethod,
      };
      if (rawMethod === 'POST' && rawBody.trim()) {
        try {
          body.body = JSON.parse(rawBody);
        } catch {
          setResult({ success: false, error: 'Invalid JSON body' });
          setLoading(null);
          return;
        }
      }

      const response = await fetch(`${API_BASE}/api/robot/debug/raw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult({ success: false, error: String(err) });
    } finally {
      setLoading(null);
    }
  };

  const moveHead = async () => {
    setLoading('head');
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/robot/head/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x: headX,
          y: headY,
          z: headZ,
          roll: headRoll,
          duration: 1.0,
        }),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult({ success: false, error: String(err) });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Preset Commands */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Quick Commands</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-3 gap-2">
            {PRESET_COMMANDS.map((cmd) => (
              <button
                key={cmd.id}
                onClick={() => executePreset(cmd.id)}
                disabled={loading !== null}
                className="btn btn-secondary text-sm py-2 px-3 flex items-center justify-center gap-2"
              >
                <span>{cmd.icon}</span>
                <span>{cmd.label}</span>
                {loading === cmd.id && (
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Head Position Control */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Head Position</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-1">
                X (Left/Right): {headX}°
              </label>
              <input
                type="range"
                min="-45"
                max="45"
                value={headX}
                onChange={(e) => setHeadX(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-1">
                Y (Forward/Back): {headY}°
              </label>
              <input
                type="range"
                min="-30"
                max="30"
                value={headY}
                onChange={(e) => setHeadY(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-1">
                Z (Up/Down): {headZ}°
              </label>
              <input
                type="range"
                min="-45"
                max="45"
                value={headZ}
                onChange={(e) => setHeadZ(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-[var(--text-secondary)] mb-1">
                Roll (Tilt): {headRoll}°
              </label>
              <input
                type="range"
                min="-30"
                max="30"
                value={headRoll}
                onChange={(e) => setHeadRoll(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={moveHead}
              disabled={loading !== null}
              className="btn btn-primary flex-1"
            >
              {loading === 'head' ? 'Moving...' : 'Move Head'}
            </button>
            <button
              onClick={() => {
                setHeadX(0);
                setHeadY(0);
                setHeadZ(0);
                setHeadRoll(0);
              }}
              className="btn btn-secondary"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Raw API Command */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Raw API Command</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="flex gap-2">
            <select
              value={rawMethod}
              onChange={(e) => setRawMethod(e.target.value)}
              className="input w-24"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
            </select>
            <input
              type="text"
              value={rawEndpoint}
              onChange={(e) => setRawEndpoint(e.target.value)}
              placeholder="/api/daemon/status"
              className="input flex-1"
            />
          </div>
          {rawMethod === 'POST' && (
            <textarea
              value={rawBody}
              onChange={(e) => setRawBody(e.target.value)}
              placeholder='{"key": "value"}'
              className="input w-full h-20 font-mono text-sm"
            />
          )}
          <div className="flex gap-2">
            <button
              onClick={executeRaw}
              disabled={loading !== null}
              className="btn btn-primary flex-1"
            >
              {loading === 'raw' ? 'Executing...' : 'Execute'}
            </button>
            <button
              onClick={() => {
                setRawEndpoint('/api/daemon/status');
                setRawMethod('GET');
                setRawBody('');
              }}
              className="btn btn-secondary"
            >
              Reset
            </button>
          </div>

          {/* Quick endpoint buttons */}
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => { setRawEndpoint('/api/daemon/status'); setRawMethod('GET'); }}
              className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
            >
              Daemon Status
            </button>
            <button
              onClick={() => { setRawEndpoint('/api/state/present_head_pose'); setRawMethod('GET'); }}
              className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
            >
              Head Pose
            </button>
            <button
              onClick={() => { setRawEndpoint('/api/motors/status'); setRawMethod('GET'); }}
              className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
            >
              Motors
            </button>
            <button
              onClick={() => { setRawEndpoint('/api/move/play/wake_up'); setRawMethod('POST'); }}
              className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
            >
              Wake Up
            </button>
          </div>
        </div>
      </div>

      {/* Result Display */}
      {result && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
              Result
              <span className={`text-xs px-2 py-0.5 rounded ${result.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {result.success ? 'Success' : 'Failed'}
              </span>
            </h3>
          </div>
          <div className="card-body">
            <pre className="text-xs font-mono bg-[var(--bg-tertiary)] p-3 rounded overflow-auto max-h-60">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
