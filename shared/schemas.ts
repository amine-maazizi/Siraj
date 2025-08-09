// shared/schemas.ts
import { z } from "zod";

// ---- Ingest
export const IngestResponse = z.object({
  doc_id: z.string(),
  title: z.string(),
  pages: z.number(),
  chunks: z.number(),
});
export type IngestResponse = z.infer<typeof IngestResponse>;

// ---- Summarize
export const SummarizeRequest = z.object({ doc_id: z.string() });
export type SummarizeRequest = z.infer<typeof SummarizeRequest>;

export const SummarySection = z.object({
  title: z.string(),
  bullets: z.array(z.string()).default([]),
});
export const SummarizeResponse = z.object({
  summary_sections: z.array(SummarySection).default([]),
});
export type SummarizeResponse = z.infer<typeof SummarizeResponse>;

// ---- Chat
export const ChatMessage = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});
export const ChatCitation = z.object({ page: z.number(), snippet: z.string() });
export const ChatRequest = z.object({
  doc_id: z.string(),
  messages: z.array(ChatMessage),
});
export const ChatResponse = z.object({
  answer: z.string(),
  citations: z.array(ChatCitation).default([]),
});
export type ChatRequest = z.infer<typeof ChatRequest>;
export type ChatResponse = z.infer<typeof ChatResponse>;

// ---- Quiz
export const QuizOption = z.object({ id: z.string(), text: z.string() });
export const QuizQuestion = z.object({
  id: z.string(),
  stem: z.string(),
  options: z.array(QuizOption),
  multi: z.boolean().default(true),
});
export const QuizGenerateRequest = z.object({
  doc_id: z.string(),
  n_questions: z.number().default(6),
  type: z.literal("checkbox").default("checkbox"),
});
export const QuizGenerateResponse = z.object({
  quiz_id: z.string(),
  questions: z.array(QuizQuestion),
});
export type QuizGenerateRequest = z.infer<typeof QuizGenerateRequest>;
export type QuizGenerateResponse = z.infer<typeof QuizGenerateResponse>;

export const QuizAnswer = z.object({
  question_id: z.string(),
  option_ids: z.array(z.string()),
});
export const QuizGradeRequest = z.object({
  quiz_id: z.string(),
  answers: z.array(QuizAnswer),
});
export const PerQuestionResult = z.object({
  id: z.string(),
  correct_option_ids: z.array(z.string()),
  rationale: z.string(),
});
export const QuizGradeResponse = z.object({
  score: z.number(),
  per_question: z.array(PerQuestionResult),
});
export type QuizGradeRequest = z.infer<typeof QuizGradeRequest>;
export type QuizGradeResponse = z.infer<typeof QuizGradeResponse>;

// ---- Progress
export const ProgressTotals = z.object({
  docs: z.number(),
  quizzes: z.number(),
  avgScore: z.number(),
});
export const ProgressHistoryPoint = z.object({
  date: z.string(),
  score: z.number(),
});
export const ProgressSkill = z.object({
  name: z.string(),
  level: z.number(),
});
export const ProgressGap = z.object({
  topic: z.string(),
  note: z.string(),
});
export const ProgressResponse = z.object({
  totals: ProgressTotals,
  history: z.array(ProgressHistoryPoint),
  skills: z.array(ProgressSkill),
  gaps: z.array(ProgressGap),
});
export type ProgressResponse = z.infer<typeof ProgressResponse>;

// ---- Suggestions
export const SuggestRequest = z.object({
  gaps: z.array(z.string()),
  time_per_day: z.number(),
  horizon_weeks: z.number(),
});
export const PlanItem = z.object({
  week: z.number(),
  focus: z.string(),
  tasks: z.array(z.string()),
});
export const ResourceItem = z.object({
  title: z.string(),
  type: z.enum(["book", "video", "web"]),
  link: z.string().optional(),
});
export const SuggestResponse = z.object({
  plan: z.array(PlanItem),
  resources: z.array(ResourceItem),
});
export type SuggestRequest = z.infer<typeof SuggestRequest>;
export type SuggestResponse = z.infer<typeof SuggestResponse>;

// ---- Brainrot
export const BrainrotStyle = z.enum(["tldr", "memetic", "motivational"]);
export const BrainrotSummaryRequest = z.object({
  doc_id: z.string(),
  style: BrainrotStyle.default("tldr"),
  duration_sec: z.number().default(30),
});
export const BrainrotSummaryResponse = z.object({
  job_id: z.string(),
  summary_text: z.string(),
  sections: z.array(SummarySection),
});

export const BrainrotTTSRequest = z.object({
  job_id: z.string(),
  text: z.string(),
  voice: z.string().default("en_female_1"),
  speed: z.number().default(1.0),
});
export const BrainrotTTSResponse = z.object({
  audio_path: z.string(),
  duration_ms: z.number(),
});

export const BrainrotCaptionsRequest = z.object({
  job_id: z.string(),
  audio_path: z.string(),
  text: z.string(),
  level: z.enum(["line", "word"]).default("line"),
});
export const BrainrotCaptionsResponse = z.object({
  vtt_path: z.string(),
  srt_path: z.string(),
});

export const BrainrotRenderRequest = z.object({
  job_id: z.string(),
  audio_path: z.string(),
  vtt_path: z.string(),
  aspect: z.enum(["9:16", "16:9"]).default("9:16"),
  theme: z.string().default("siraj"),
  include_waveform: z.boolean().default(true),
});
export const BrainrotRenderResponse = z.object({
  video_path: z.string(),
  thumbnail_path: z.string().optional(),
  duration_ms: z.number(),
});
