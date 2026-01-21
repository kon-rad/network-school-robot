import { useState, useCallback, useRef, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const WS_BASE = API_BASE.replace('http', 'ws');

interface CaptureResult {
  success: boolean;
  message: string;
  image_base64?: string;
  format?: string;
}

interface StreamFrame {
  image_base64?: string;
  format?: string;
  width?: number;
  height?: number;
  fps?: number;
  keepalive?: boolean;
  error?: string;
}

export function CameraView() {
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<CaptureResult | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fps, setFps] = useState(0);
  const [resolution, setResolution] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    console.log('Connecting to video stream:', `${WS_BASE}/api/robot/video-stream/ws`);
    const ws = new WebSocket(`${WS_BASE}/api/robot/video-stream/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsStreaming(true);
      setError(null);
      console.log('Video stream connected');
    };

    ws.onmessage = (event) => {
      try {
        const data: StreamFrame = JSON.parse(event.data);

        if (data.keepalive) {
          return;
        }

        if (data.error) {
          setError(data.error);
          setFps(0);
          return;
        }

        if (data.image_base64) {
          setCurrentFrame(`data:image/${data.format || 'jpeg'};base64,${data.image_base64}`);
          setError(null);

          if (data.fps !== undefined) {
            setFps(data.fps);
          }

          if (data.width && data.height) {
            setResolution(`${data.width}×${data.height}`);
          }
        }
      } catch (e) {
        console.error('Failed to parse frame:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('WebSocket error:', e);
      setError('Stream connection error - check if robot is connected');
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsStreaming(false);
      wsRef.current = null;
    };
  }, []);

  const startStreaming = useCallback(() => {
    setError(null);
    connectWebSocket();
  }, [connectWebSocket]);

  const stopStreaming = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsStreaming(false);
    setFps(0);
  }, []);

  const captureImage = useCallback(async () => {
    setIsCapturing(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/robot/camera/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to capture image');
      }

      const result: CaptureResult = await response.json();

      if (result.success && result.image_base64) {
        setCapturedImage(result);
        setError(null);
      } else {
        setError(result.message || 'Capture failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Capture failed');
    } finally {
      setIsCapturing(false);
    }
  }, []);

  const downloadImage = useCallback((imageData: CaptureResult | string) => {
    let href: string;
    let filename: string;

    if (typeof imageData === 'string') {
      href = imageData;
      filename = `robot-capture-${Date.now()}.jpg`;
    } else if (imageData.image_base64) {
      href = `data:image/${imageData.format || 'jpeg'};base64,${imageData.image_base64}`;
      filename = `robot-capture-${Date.now()}.${imageData.format || 'jpg'}`;
    } else {
      return;
    }

    const link = document.createElement('a');
    link.href = href;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  const displayFrame = currentFrame || (capturedImage?.image_base64 ? `data:image/${capturedImage.format || 'jpeg'};base64,${capturedImage.image_base64}` : null);

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--accent-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h2 className="font-medium text-[var(--text-primary)]">Robot Camera</h2>
            <p className="text-xs text-[var(--text-tertiary)]">
              {isStreaming ? (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  Live • {fps} FPS {resolution && `• ${resolution}`}
                </span>
              ) : (
                'View live feed or capture images'
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Stream Toggle */}
          <button
            onClick={isStreaming ? stopStreaming : startStreaming}
            className={`btn ${isStreaming ? 'btn-secondary' : 'btn-primary'}`}
          >
            {isStreaming ? (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                <span>Stop</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Live</span>
              </>
            )}
          </button>

          {/* Capture Button */}
          <button
            onClick={captureImage}
            disabled={isCapturing}
            className="btn btn-secondary"
          >
            {isCapturing ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Capture</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="p-5">
        {error && (
          <div className="bg-[var(--error)]/10 border border-[var(--error)]/20 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 text-[var(--error)]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {displayFrame ? (
          <div className="space-y-4">
            <div className="relative rounded-lg overflow-hidden border border-[var(--border-default)] bg-black">
              <img
                src={displayFrame}
                alt="Robot camera view"
                className="w-full"
              />
              {isStreaming && (
                <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  LIVE
                </div>
              )}
              {isStreaming && fps > 0 && (
                <div className="absolute top-3 right-3 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  {fps} FPS
                </div>
              )}
            </div>

            {/* Action buttons for displayed image */}
            <div className="flex items-center justify-between">
              <p className="text-xs text-[var(--text-tertiary)]">
                {isStreaming ? 'Streaming live from robot camera' : capturedImage ? 'Captured image' : 'Last frame'}
              </p>
              <div className="flex gap-2">
                {displayFrame && (
                  <button
                    onClick={() => currentFrame ? downloadImage(currentFrame) : capturedImage && downloadImage(capturedImage)}
                    className="text-xs text-[var(--accent-primary)] hover:underline flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="aspect-video bg-[var(--bg-tertiary)] rounded-lg flex flex-col items-center justify-center">
            <svg className="w-16 h-16 text-[var(--text-tertiary)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <p className="text-sm text-[var(--text-secondary)]">No camera feed</p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">Click "Live" to start streaming</p>
          </div>
        )}

        {/* Captured Image Gallery (when we have a separate capture while streaming) */}
        {capturedImage && currentFrame && (
          <div className="mt-4 pt-4 border-t border-[var(--border-default)]">
            <p className="text-xs text-[var(--text-secondary)] mb-2">Captured Image</p>
            <div className="flex items-start gap-4">
              <div className="w-32 h-24 rounded overflow-hidden border border-[var(--border-default)]">
                <img
                  src={`data:image/${capturedImage.format || 'jpeg'};base64,${capturedImage.image_base64}`}
                  alt="Captured"
                  className="w-full h-full object-cover"
                />
              </div>
              <button
                onClick={() => downloadImage(capturedImage)}
                className="text-xs text-[var(--accent-primary)] hover:underline flex items-center gap-1"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Save
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
