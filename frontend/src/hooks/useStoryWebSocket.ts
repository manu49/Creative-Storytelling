"use client";

import { useEffect, useRef, useState } from "react";
import { useStoryStore } from "@/store/storyStore";
import { WSFrameType, AgentTask } from "@/types";

interface UseWebSocketOptions {
  storyId: string;
  enabled?: boolean;
}

export function useStoryWebSocket({ storyId, enabled = true }: UseWebSocketOptions) {
  const store = useStoryStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const INITIAL_BACKOFF_MS = 1000;

  const connect = () => {
    if (!enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${storyId}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("✅ WebSocket connected");
        store.setWsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Send initial ping to keep connection alive
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const frame: WSFrameType = JSON.parse(event.data);
          handleFrame(frame);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error("❌ WebSocket error:", event);
        store.setWsConnected(false);
      };

      wsRef.current.onclose = () => {
        console.log("🔌 WebSocket closed");
        store.setWsConnected(false);
        attemptReconnect();
      };
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      attemptReconnect();
    }
  };

  const attemptReconnect = () => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      console.error("Max WebSocket reconnect attempts reached");
      return;
    }

    reconnectAttemptsRef.current += 1;
    const backoffMs = INITIAL_BACKOFF_MS * Math.pow(2, reconnectAttemptsRef.current - 1);
    console.log(`Reconnecting in ${backoffMs}ms (attempt ${reconnectAttemptsRef.current})...`);

    setTimeout(connect, backoffMs);
  };

  const startHeartbeat = () => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      } else {
        clearInterval(interval);
      }
    }, 30000); // 30 second heartbeat
  };

  const handleFrame = (frame: WSFrameType) => {
    switch (frame.type) {
      case "agent:task_started":
        console.log(`🚀 Task started: ${frame.task_type}`);
        // Clear previous chunks for this task
        store.clearTaskChunks(frame.task_id);
        break;

      case "agent:chunk":
        // Accumulate streaming chunks
        store.appendTaskChunk(frame.task_id, frame.text);
        break;

      case "agent:task_done":
        console.log(`✅ Task done: ${frame.task_id}`);
        // Create a completed task and add it to store
        const completedTask: AgentTask = {
          id: frame.task_id,
          story_id: storyId,
          scene_id: undefined,
          task_type: "grammar_fix", // Default, should be in the frame ideally
          status: "completed",
          priority: 0,
          suggestion: frame.suggestion || store.getTaskChunks(frame.task_id),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        store.upsertAgentTask(completedTask);
        break;

      case "agent:task_failed":
        console.error(`❌ Task failed: ${frame.error}`);
        break;

      case "scene:updated":
        console.log(`Scene updated: ${frame.scene_id}`);
        // Trigger a refetch of the story to get updated scene
        break;

      case "pong":
        // Heartbeat response
        break;

      default:
        // @ts-ignore - exhaustive check
        console.warn(`Unknown frame type: ${frame.type}`);
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    store.setWsConnected(false);
  };

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [storyId, enabled]);

  return {
    connected: store.wsConnected,
  };
}
