"use client";

import { useStoryStore } from "@/store/storyStore";
import { AgentTask } from "@/types";
import { CheckCircle2, XCircle, Loader2, AlertCircle } from "lucide-react";
import { useState } from "react";

interface AISuggestionPanelProps {
  onAccept: (task: AgentTask) => Promise<void>;
  onReject: (task: AgentTask) => Promise<void>;
}

export function AISuggestionPanel({
  onAccept,
  onReject,
}: AISuggestionPanelProps) {
  const store = useStoryStore();
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const tasks = Object.values(store.agentTasks).sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const pendingTasks = tasks.filter(
    (t) => t.status === "pending" || t.status === "running"
  );
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const failedTasks = tasks.filter((t) => t.status === "failed");

  const handleAccept = async (task: AgentTask) => {
    setAcceptingId(task.id);
    try {
      await onAccept(task);
    } finally {
      setAcceptingId(null);
    }
  };

  const handleReject = async (task: AgentTask) => {
    setRejectingId(task.id);
    try {
      await onReject(task);
    } finally {
      setRejectingId(null);
    }
  };

  return (
    <div className="h-full bg-white border-l border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-bold text-gray-900">AI Suggestions</h2>
        <div className="mt-2 flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              store.wsConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-600">
            {store.wsConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Pending Tasks */}
        {pendingTasks.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              🔄 Processing ({pendingTasks.length})
            </h3>
            <div className="space-y-3">
              {pendingTasks.map((task) => (
                <div
                  key={task.id}
                  className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                    <span className="font-medium text-sm text-gray-900">
                      {formatTaskType(task.task_type)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">
                    {store.getTaskChunks(task.id) || "Analyzing..."}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              ✅ Suggestions ({completedTasks.length})
            </h3>
            <div className="space-y-3">
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-sm text-gray-900">
                      {formatTaskType(task.task_type)}
                    </span>
                  </div>

                  <div className="bg-gray-50 rounded p-3 mb-3 max-h-48 overflow-y-auto text-sm text-gray-700 whitespace-pre-wrap">
                    {task.suggestion || store.getTaskChunks(task.id)}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAccept(task)}
                      disabled={acceptingId === task.id}
                      className="flex-1 text-sm font-medium px-3 py-2 rounded bg-green-100 text-green-700 hover:bg-green-200 disabled:opacity-50"
                    >
                      {acceptingId === task.id ? "Applying..." : "Accept"}
                    </button>
                    <button
                      onClick={() => handleReject(task)}
                      disabled={rejectingId === task.id}
                      className="flex-1 text-sm font-medium px-3 py-2 rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
                    >
                      {rejectingId === task.id ? "Rejecting..." : "Reject"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Failed Tasks */}
        {failedTasks.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              ❌ Failed ({failedTasks.length})
            </h3>
            <div className="space-y-3">
              {failedTasks.map((task) => (
                <div
                  key={task.id}
                  className="bg-red-50 border border-red-200 rounded-lg p-3"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <span className="font-medium text-sm text-gray-900">
                      {formatTaskType(task.task_type)}
                    </span>
                  </div>
                  <p className="text-sm text-red-700">
                    {task.error_message || "An error occurred"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {tasks.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No suggestions yet.</p>
            <p className="text-xs mt-2">Edit scenes to get AI suggestions.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function formatTaskType(type: string): string {
  const names: Record<string, string> = {
    grammar_fix: "Grammar & Style",
    coherence_check: "Story Coherence",
    character_arc: "Character Development",
    idea_generate: "Scene Expansion",
  };
  return names[type] || type;
}
