export type Board = { heading: string; bullets: string[]; example?: string; fractionBars?: { label: string; parts: number; filled: number }[] };
export type LessonStep = { id: string; title: string; narration: string; board: Board; question: string; expectedAnswer: string; sourcePages: number[] };
export type Lesson = { id: string; title: string; language: string; steps: LessonStep[]; provider: 'gemini' | 'demo' };
export type Material = { sourceId: string; title: string; text: string; pages: { page: number; text: string }[] };
export type Health = { geminiConfigured: boolean; sarvamConfigured: boolean; model: string };
export type AnswerResult = { status: 'correct' | 'needs_work' | 'unclear'; feedback: string; narration: string; board?: Board; followUpQuestion?: string };
export async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { method: body === undefined ? 'GET' : 'POST', headers: body === undefined || body instanceof FormData ? undefined : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body), signal });
  if (!response.ok) {
    let message = `Request failed (${response.status}). Try again.`;
    try { const error = await response.json(); message = typeof error.detail === 'string' ? error.detail : typeof error.message === 'string' ? error.message : message; } catch { /* preserve safe message */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
