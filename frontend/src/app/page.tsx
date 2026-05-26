"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, BookOpen, Trash2 } from "lucide-react";

interface Story {
  id: string;
  title: string;
  genre?: string;
  logline?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function Dashboard() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStories();
  }, []);

  const fetchStories = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/stories`
      );
      if (!response.ok) throw new Error("Failed to fetch stories");
      const data = await response.json();
      setStories(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStory = async () => {
    const title = prompt("Enter story title:");
    if (!title) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/stories`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            genre: prompt("Enter genre (optional):") || undefined,
            logline: prompt("Enter logline (optional):") || undefined,
          }),
        }
      );
      if (!response.ok) throw new Error("Failed to create story");
      const newStory = await response.json();
      setStories([...stories, newStory]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const handleDeleteStory = async (id: string) => {
    if (!confirm("Delete this story?")) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/stories/${id}`,
        { method: "DELETE" }
      );
      if (!response.ok) throw new Error("Failed to delete story");
      setStories(stories.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Creative Storytelling
            </h1>
          </div>
          <button
            onClick={handleCreateStory}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
          >
            <Plus className="w-5 h-5" />
            New Story
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-500">Loading stories...</div>
        ) : stories.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-xl text-gray-500 mb-6">No stories yet</p>
            <button
              onClick={handleCreateStory}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
            >
              Create Your First Story
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stories.map((story) => (
              <div
                key={story.id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition"
              >
                <div className="p-6">
                  <Link href={`/stories/${story.id}`} className="block mb-4">
                    <h2 className="text-xl font-bold text-gray-900 hover:text-blue-600">
                      {story.title}
                    </h2>
                  </Link>

                  {story.genre && (
                    <p className="text-sm text-gray-600 mb-2">
                      <span className="font-medium">Genre:</span> {story.genre}
                    </p>
                  )}

                  {story.logline && (
                    <p className="text-sm text-gray-600 mb-3 italic">
                      {story.logline}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="capitalize bg-gray-100 px-2 py-1 rounded">
                      {story.status}
                    </span>
                    <span>
                      {new Date(story.updated_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex gap-3 mt-4 pt-4 border-t">
                    <Link
                      href={`/stories/${story.id}`}
                      className="flex-1 text-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDeleteStory(story.id)}
                      className="bg-red-100 hover:bg-red-200 text-red-600 p-2 rounded"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
