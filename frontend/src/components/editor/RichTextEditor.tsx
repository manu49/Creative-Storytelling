"use client";

import { useEffect } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Typography from "@tiptap/extension-typography";
import Placeholder from "@tiptap/extension-placeholder";
import CharacterCount from "@tiptap/extension-character-count";
import { Scene } from "@/types";
import "./RichTextEditor.css";

interface RichTextEditorProps {
  scene: Scene | null;
  onUpdate: (content: string) => void;
  disabled?: boolean;
}

export function RichTextEditor({
  scene,
  onUpdate,
  disabled = false,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Typography,
      Placeholder.configure({
        placeholder: "Start writing your scene...",
      }),
      CharacterCount.configure({
        limit: 50000,
      }),
    ],
    content: scene?.content || "",
    onUpdate: ({ editor }) => {
      const content = editor.getHTML();
      // Convert HTML to Markdown for storage
      const markdown = htmlToMarkdown(content);
      onUpdate(markdown);
    },
    editorProps: {
      attributes: {
        class: "focus:outline-none prose prose-sm max-w-none",
      },
    },
  });

  // Update editor content when scene changes
  useEffect(() => {
    if (editor && scene) {
      editor.commands.setContent(scene.content);
    }
  }, [scene?.id, editor]);

  if (!editor) {
    return <div className="text-gray-500">Loading editor...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Toolbar */}
      <div className="border-b border-gray-200 p-4 flex gap-2 flex-wrap bg-gray-50">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`px-3 py-2 rounded text-sm font-medium ${
            editor.isActive("bold")
              ? "bg-blue-600 text-white"
              : "bg-white border border-gray-300 hover:bg-gray-50"
          }`}
          disabled={disabled}
        >
          Bold
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`px-3 py-2 rounded text-sm font-medium ${
            editor.isActive("italic")
              ? "bg-blue-600 text-white"
              : "bg-white border border-gray-300 hover:bg-gray-50"
          }`}
          disabled={disabled}
        >
          Italic
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`px-3 py-2 rounded text-sm font-medium ${
            editor.isActive("heading", { level: 2 })
              ? "bg-blue-600 text-white"
              : "bg-white border border-gray-300 hover:bg-gray-50"
          }`}
          disabled={disabled}
        >
          H2
        </button>
        <div className="ml-auto text-sm text-gray-500">
          {editor.storage.characterCount.characters()} / 50000 characters
        </div>
      </div>

      {/* Editor Content */}
      <div className="flex-1 overflow-auto p-6">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

function htmlToMarkdown(html: string): string {
  // Simple HTML to Markdown conversion
  let markdown = html
    .replace(/<h1[^>]*>(.*?)<\/h1>/gi, "# $1\n")
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, "## $1\n")
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, "### $1\n")
    .replace(/<strong[^>]*>(.*?)<\/strong>/gi, "**$1**")
    .replace(/<b[^>]*>(.*?)<\/b>/gi, "**$1**")
    .replace(/<em[^>]*>(.*?)<\/em>/gi, "*$1*")
    .replace(/<i[^>]*>(.*?)<\/i>/gi, "*$1*")
    .replace(/<u[^>]*>(.*?)<\/u>/gi, "__$1__")
    .replace(/<br[^>]*>/gi, "\n")
    .replace(/<p[^>]*>(.*?)<\/p>/gi, "$1\n\n")
    .replace(/<ul[^>]*>/gi, "")
    .replace(/<\/ul>/gi, "")
    .replace(/<li[^>]*>(.*?)<\/li>/gi, "- $1\n")
    .replace(/<ol[^>]*>/gi, "")
    .replace(/<\/ol>/gi, "")
    .replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gi, "> $1\n")
    .replace(/<[^>]*>/g, "")
    .trim();

  return markdown;
}
