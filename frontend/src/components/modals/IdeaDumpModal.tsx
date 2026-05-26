"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { useStoryStore } from "@/store/storyStore";

interface IdeaDumpModalProps {
  storyId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function IdeaDumpModal({
  storyId,
  isOpen,
  onClose,
}: IdeaDumpModalProps) {
  const store = useStoryStore();
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setIsSubmitting(true);
    try {
      const task = await apiClient.dumpIdea(storyId, {
        raw_text: text,
        source_type: "text",
      });

      store.upsertAgentTask(task);

      // Clear form
      setText("");

      // Close after 1 second
      setTimeout(onClose, 1000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to submit idea");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Dump Raw Idea</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={isSubmitting}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Your Idea
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="What's your creative idea? A scene, dialogue, character moment, plot twist, etc."
              className="w-full h-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={isSubmitting}
            />
            <p className="text-xs text-gray-500 mt-2">
              The AI will expand this into a full scene with dialogue and details.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-900 font-medium hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
              disabled={isSubmitting || !text.trim()}
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {isSubmitting ? "Expanding..." : "Expand Idea"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
