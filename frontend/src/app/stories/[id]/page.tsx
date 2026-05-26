"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useStoryStore } from "@/store/storyStore";
import { useStoryWebSocket } from "@/hooks/useStoryWebSocket";
import { EditorLayout } from "@/components/editor/EditorLayout";
import { apiClient } from "@/lib/api";

export default function StoryEditorPage() {
  const params = useParams();
  const storyId = params.id as string;
  const store = useStoryStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize WebSocket connection
  useStoryWebSocket({ storyId, enabled: true });

  useEffect(() => {
    fetchStory();
  }, [storyId]);

  const fetchStory = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getStory(storyId);
      store.setActiveStory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading story...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return <EditorLayout storyId={storyId} />;
}
