"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { StoryDetail } from "@/types";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

export default function StoryEditorPage() {
  const params = useParams();
  const storyId = params.id as string;
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStory();
  }, [storyId]);

  const fetchStory = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getStory(storyId);
      setStory(data);
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

  if (error || !story) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500">{error || "Story not found"}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
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
              {story.genre && (
                <p className="text-sm text-gray-500">
                  Genre: <span className="font-medium">{story.genre}</span>
                </p>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - TODO: Implement three-panel editor */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-500 mb-6">
            Story editor coming soon...
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-6 rounded">
              <h3 className="font-bold text-lg mb-2">🗂️ Scene Navigator</h3>
              <p className="text-sm text-gray-600">
                Navigate {story.scenes.length} scenes
              </p>
            </div>
            <div className="bg-white p-6 rounded">
              <h3 className="font-bold text-lg mb-2">✍️ Rich Editor</h3>
              <p className="text-sm text-gray-600">
                Edit scene content with Markdown
              </p>
            </div>
            <div className="bg-white p-6 rounded">
              <h3 className="font-bold text-lg mb-2">✨ AI Suggestions</h3>
              <p className="text-sm text-gray-600">
                Real-time agent improvements
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
