"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useStoryStore } from "@/store/storyStore";
import { apiClient } from "@/lib/api";
import { SceneNavigator } from "./SceneNavigator";
import { RichTextEditor } from "./RichTextEditor";
import { AISuggestionPanel } from "./AISuggestionPanel";
import { IdeaDumpModal } from "../modals/IdeaDumpModal";
import { AgentTask, Scene } from "@/types";
import { ChevronLeft, Download, Lightbulb } from "lucide-react";
import Link from "next/link";

interface EditorLayoutProps {
  storyId: string;
}

export function EditorLayout({ storyId }: EditorLayoutProps) {
  const router = useRouter();
  const store = useStoryStore();
  const story = store.activeStory;
  const activeSceneId = store.activeSceneId;
  const activeScene = story?.scenes.find((s) => s.id === activeSceneId);

  const [savingSceneId, setSavingSceneId] = useState<string | null>(null);
  const [creatingScene, setCreatingScene] = useState(false);
  const [ideaModalOpen, setIdeaModalOpen] = useState(false);

  if (!story) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-500">Loading story...</div>
      </div>
    );
  }

  const handleAddScene = async () => {
    setCreatingScene(true);
    try {
      const title = prompt("Scene title (optional):");
      const newScene = await apiClient.createScene(storyId, {
        title: title || undefined,
        content: "",
      });
      store.addScene(newScene);
      store.setActiveSceneId(newScene.id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create scene");
    } finally {
      setCreatingScene(false);
    }
  };

  const handleDeleteScene = async (sceneId: string) => {
    if (!confirm("Delete this scene?")) return;
    try {
      await apiClient.deleteScene(storyId, sceneId);
      store.deleteScene(sceneId);
      if (activeSceneId === sceneId && story.scenes.length > 1) {
        store.setActiveSceneId(story.scenes[0].id);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete scene");
    }
  };

  const handleUpdateScene = async (content: string) => {
    if (!activeScene) return;

    setSavingSceneId(activeScene.id);
    try {
      // Debounce updates - just update local store for now
      store.updateScene(activeScene.id, { content });

      // Make API call
      await apiClient.updateScene(storyId, activeScene.id, { content });
    } catch (err) {
      console.error("Failed to save scene:", err);
    } finally {
      setSavingSceneId(null);
    }
  };

  const handleAcceptTask = async (task: AgentTask) => {
    try {
      await apiClient.acceptAgentTask(storyId, task.id);
      // Update local task status
      store.upsertAgentTask({ ...task, status: "accepted" });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to accept suggestion");
    }
  };

  const handleRejectTask = async (task: AgentTask) => {
    try {
      await apiClient.rejectAgentTask(storyId, task.id);
      // Update local task status
      store.upsertAgentTask({ ...task, status: "rejected" });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to reject suggestion");
    }
  };

  const handleExport = async (format: "markdown" | "pdf") => {
    try {
      const blob = await apiClient.exportStory(storyId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${story.title}.${format === "pdf" ? "pdf" : "md"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Export failed");
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-full px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-gray-500 hover:text-gray-700 transition"
            >
              <ChevronLeft className="w-6 h-6" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {story.title}
              </h1>
              {activeScene && (
                <p className="text-sm text-gray-600 mt-1">
                  Editing: <span className="font-medium">{activeScene.title || "Untitled Scene"}</span>
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setIdeaModalOpen(true)}
              className="flex items-center gap-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-900 px-4 py-2 rounded-lg text-sm font-medium"
            >
              <Lightbulb className="w-4 h-4" />
              Dump Idea
            </button>
            <button
              onClick={() => handleExport("markdown")}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>
      </header>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Scene Navigator */}
        <div className="w-64 overflow-hidden">
          <SceneNavigator
            onAddScene={handleAddScene}
            onDeleteScene={handleDeleteScene}
          />
        </div>

        {/* Center Panel - Rich Text Editor */}
        <div className="flex-1 overflow-hidden">
          {activeScene ? (
            <div className="h-full flex flex-col relative">
              <RichTextEditor
                scene={activeScene}
                onUpdate={handleUpdateScene}
                disabled={savingSceneId === activeScene.id}
              />
              {savingSceneId === activeScene.id && (
                <div className="absolute bottom-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">
                  ✓ Saving...
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p className="text-lg mb-4">No scene selected</p>
                <button
                  onClick={handleAddScene}
                  disabled={creatingScene}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                  {creatingScene ? "Creating..." : "Create Your First Scene"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - AI Suggestions */}
        <div className="w-96 overflow-hidden">
          <AISuggestionPanel
            onAccept={handleAcceptTask}
            onReject={handleRejectTask}
          />
        </div>
      </div>

      {/* Modals */}
      <IdeaDumpModal
        storyId={storyId}
        isOpen={ideaModalOpen}
        onClose={() => setIdeaModalOpen(false)}
      />
    </div>
  );
}
