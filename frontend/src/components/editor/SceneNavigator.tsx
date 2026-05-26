"use client";

import { useStoryStore } from "@/store/storyStore";
import { Scene } from "@/types";
import { Plus, Trash2 } from "lucide-react";

interface SceneNavigatorProps {
  onAddScene: () => void;
  onDeleteScene: (sceneId: string) => void;
}

export function SceneNavigator({
  onAddScene,
  onDeleteScene,
}: SceneNavigatorProps) {
  const store = useStoryStore();
  const activeSceneId = store.activeSceneId;
  const scenes = store.activeStory?.scenes || [];

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Scenes</h2>
        <button
          onClick={onAddScene}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Scene
        </button>
      </div>

      {/* Scene List */}
      <div className="flex-1 overflow-y-auto">
        {scenes.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No scenes yet. Create one to start writing.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {scenes.map((scene, index) => (
              <li key={scene.id}>
                <button
                  onClick={() => store.setActiveSceneId(scene.id)}
                  className={`w-full text-left p-4 hover:bg-blue-50 transition ${
                    activeSceneId === scene.id
                      ? "bg-blue-50 border-l-4 border-blue-600"
                      : ""
                  }`}
                >
                  <div className="font-medium text-gray-900">
                    {scene.title || `Scene ${index + 1}`}
                  </div>
                  {scene.location && (
                    <div className="text-sm text-gray-600 mt-1">
                      📍 {scene.location}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 mt-2">
                    {scene.content.split(" ").length} words
                  </div>
                </button>

                {activeSceneId === scene.id && (
                  <div className="px-4 py-2 flex gap-2 bg-blue-50">
                    <button
                      onClick={() => onDeleteScene(scene.id)}
                      className="flex-1 flex items-center justify-center gap-1 text-red-600 hover:bg-red-50 px-3 py-1 rounded text-sm font-medium"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Stats */}
      {scenes.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>{scenes.length} scenes</span>
            <span>
              {scenes.reduce((sum, s) => sum + s.content.split(" ").length, 0)}{" "}
              words
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
