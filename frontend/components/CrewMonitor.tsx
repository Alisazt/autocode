import React, { useEffect, useState } from 'react';

// Types describing the status and log events
interface CrewStatus {
  executionId: string;
  currentAgent: string;
  currentTask: string;
  progress: number;
  blockedReason?: string;
  nextAction: string;
  metrics: {
    tokensUsed: number;
    costUSD: number;
    duration: number;
  };
}

interface ExecutionEvent {
  timestamp: string;
  agent: string;
  message: string;
}

// Dummy agent list for display purposes
const AGENTS = ['planner', 'architect', 'developer', 'tester'];

function formatDuration(seconds?: number) {
  if (!seconds) return '0s';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

export default function CrewMonitor({ executionId }: { executionId: string }) {
  const [status, setStatus] = useState<CrewStatus | undefined>();
  const [logs, setLogs] = useState<ExecutionEvent[]>([]);

  // In a real implementation this effect would establish a WebSocket
  // connection to the backend and listen for status updates.
  useEffect(() => {
    // Simulate updates every few seconds
    const interval = setInterval(() => {
      setStatus({
        executionId,
        currentAgent: 'developer',
        currentTask: 'backend',
        progress: Math.random(),
        nextAction: 'Continue coding',
        metrics: {
          tokensUsed: Math.floor(Math.random() * 1000),
          costUSD: Math.random() * 2,
          duration: Math.floor(Math.random() * 300),
        },
      });
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          agent: 'developer',
          message: 'Simulated log event',
        },
      ]);
    }, 5000);
    return () => clearInterval(interval);
  }, [executionId]);

  const getAgentStatus = (agent: string, status?: CrewStatus) => {
    if (!status) return 'idle';
    return status.currentAgent === agent ? 'active' : 'waiting';
  };

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* Agent Status Cards */}
      <div className="col-span-2">
        <h3>Team Status</h3>
        <div className="grid grid-cols-2 gap-4">
          {AGENTS.map((agent) => (
            <div
              key={agent}
              className={`border rounded p-4 ${
                getAgentStatus(agent, status) === 'active'
                  ? 'bg-green-100'
                  : 'bg-white'
              }`}
            >
              <h4 className="font-semibold mb-2 capitalize">{agent}</h4>
              <p className="text-sm text-gray-500">
                Status: {getAgentStatus(agent, status)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Progress & Metrics */}
      <div>
        <div className="bg-gray-50 p-4 rounded">
          <div className="flex justify-between">
            <span>Progress</span>
            <span>{Math.round((status?.progress ?? 0) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(status?.progress ?? 0) * 100}%` }}
            />
          </div>
        </div>

        <div className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Tokens Used:</span>
            <span>{status?.metrics.tokensUsed.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Cost:</span>
            <span>${status?.metrics.costUSD.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Duration:</span>
            <span>{formatDuration(status?.metrics.duration)}</span>
          </div>
        </div>

        {status?.blockedReason && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="font-medium text-yellow-800">Blocked</div>
            <div className="text-yellow-700 text-sm">{status.blockedReason}</div>
            <div className="text-yellow-600 text-xs mt-1">
              Next: {status.nextAction}
            </div>
          </div>
        )}
      </div>

      {/* Live Logs */}
      <div className="col-span-3">
        <h4>Live Execution Log</h4>
        <div className="bg-black text-green-400 p-4 rounded font-mono text-sm h-64 overflow-y-auto">
          {logs.map((event, i) => (
            <div key={i} className="flex">
              <span className="text-gray-500 mr-2">
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
              <span className="text-blue-400 mr-2">[{event.agent}]</span>
              <span>{event.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
