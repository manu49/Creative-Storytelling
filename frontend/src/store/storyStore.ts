import { create } from "zustand";
import { StoryDetail, Scene, AgentTask, Character } from "@/types";

interface StoryStore {
  // State
  stories: StoryDetail[];
  activeStory: StoryDetail | null;
  activeSceneId: string | null;
  agentTasks: Record<string, AgentTask>;
  agentTaskChunks: Record<string, string>; // Accumulate streaming chunks per task
  wsConnected: boolean;
  loading: boolean;

  // Actions
  setStories: (stories: StoryDetail[]) => void;
  setActiveStory: (story: StoryDetail) => void;
  setActiveSceneId: (sceneId: string) => void;
  updateScene: (sceneId: string, patch: Partial<Scene>) => void;
  addScene: (scene: Scene) => void;
  deleteScene: (sceneId: string) => void;

  // Agent tasks
  upsertAgentTask: (task: AgentTask) => void;
  appendTaskChunk: (taskId: string, text: string) => void;
  clearTaskChunks: (taskId: string) => void;
  getTaskChunks: (taskId: string) => string;

  // WebSocket
  setWsConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
}

export const useStoryStore = create<StoryStore>((set, get) => ({
  stories: [],
  activeStory: null,
  activeSceneId: null,
  agentTasks: {},
  agentTaskChunks: {},
  wsConnected: false,
  loading: false,

  setStories: (stories) => set({ stories }),

  setActiveStory: (story) => {
    set({ activeStory: story });
    // Select first scene by default
    if (story.scenes.length > 0) {
      set({ activeSceneId: story.scenes[0].id });
    }
  },

  setActiveSceneId: (sceneId) => set({ activeSceneId: sceneId }),

  updateScene: (sceneId, patch) =>
    set((state) => {
      if (!state.activeStory) return state;
      return {
        activeStory: {
          ...state.activeStory,
          scenes: state.activeStory.scenes.map((s) =>
            s.id === sceneId ? { ...s, ...patch } : s
          ),
        },
      };
    }),

  addScene: (scene) =>
    set((state) => {
      if (!state.activeStory) return state;
      return {
        activeStory: {
          ...state.activeStory,
          scenes: [...state.activeStory.scenes, scene],
        },
      };
    }),

  deleteScene: (sceneId) =>
    set((state) => {
      if (!state.activeStory) return state;
      return {
        activeStory: {
          ...state.activeStory,
          scenes: state.activeStory.scenes.filter((s) => s.id !== sceneId),
        },
      };
    }),

  upsertAgentTask: (task) =>
    set((state) => ({
      agentTasks: {
        ...state.agentTasks,
        [task.id]: task,
      },
    })),

  appendTaskChunk: (taskId, text) =>
    set((state) => ({
      agentTaskChunks: {
        ...state.agentTaskChunks,
        [taskId]: (state.agentTaskChunks[taskId] || "") + text,
      },
    })),

  clearTaskChunks: (taskId) =>
    set((state) => {
      const { [taskId]: _, ...rest } = state.agentTaskChunks;
      return { agentTaskChunks: rest };
    }),

  getTaskChunks: (taskId) => get().agentTaskChunks[taskId] || "",

  setWsConnected: (connected) => set({ wsConnected: connected }),

  setLoading: (loading) => set({ loading }),
}));
