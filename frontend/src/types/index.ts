export interface Story {
  id: string;
  title: string;
  genre?: string;
  logline?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface StoryDetail extends Story {
  scenes: Scene[];
  characters: Character[];
}

export interface Scene {
  id: string;
  story_id: string;
  title?: string;
  content: string;
  scene_type: string;
  order_index: number;
  location?: string;
  time_of_day?: string;
  characters_present?: string;
  notes?: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  story_id: string;
  name: string;
  role?: string;
  traits?: string;
  backstory?: string;
  arc_summary?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentTask {
  id: string;
  story_id: string;
  scene_id?: string;
  task_type: string;
  status: string;
  priority: number;
  suggestion?: string;
  tool_calls_log?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type WSFrameType =
  | { type: "agent:task_started"; task_id: string; task_type: string }
  | { type: "agent:chunk"; task_id: string; text: string }
  | { type: "agent:task_done"; task_id: string; suggestion: string }
  | { type: "agent:task_failed"; task_id: string; error: string }
  | { type: "scene:updated"; scene_id: string }
  | { type: "ping" }
  | { type: "pong" };
