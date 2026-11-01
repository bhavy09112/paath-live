import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, Check, CheckCircle2, ChevronRight, FileText, Headphones, Lightbulb, LoaderCircle, Mic, Pause, Play, Plus, RotateCcw, Send, Sparkles, Square, Upload, Volume2, X } from 'lucide-react';
import { request, type AnswerResult, type Board, type Health, type Lesson, type Material } from './types';
import { recordWav, type Recording } from './recorder';

const sample = 'Fractions compare equal parts of the same whole. A numerator tells us how many parts we have. A denominator tells us how many equal parts the whole has. When the whole stays the same, one third is larger than one fourth: splitting a whole into more equal pieces makes each piece smaller. For example, one half is larger than one fifth.';
const languages = [{ code: 'en-IN', name: 'English', native: 'English' }, { code: 'hi-IN', name: 'Hindi', native: 'हिन्दी' }, { code: 'kn-IN', name: 'Kannada', native: 'ಕನ್ನಡ' }, { code: 'ta-IN', name: 'Tamil', native: 'தமிழ்' }, { code: 'te-IN', name: 'Telugu', native: 'తెలుగు' }, { code: 'mr-IN', name: 'Marathi', native: 'मराठी' }, { code: 'bn-IN', name: 'Bengali', native: 'বাংলা' }];
function teachingText(narration: string, question: string) { return question && !narration.includes(question) ? `${narration}\n\n${question}` : narration; }
function speechChunks(text: string) { const chunks: string[] = []; let remaining = text.trim(); while (remaining.length > 1100) { let cut = remaining.lastIndexOf(' ', 1100); if (cut < 500) cut = 1100; chunks.push(remaining.slice(0, cut)); remaining = remaining.slice(cut).trim(); } if (remaining) chunks.push(remaining); return chunks; }
type Phase = 'ready' | 'loading' | 'speaking' | 'paused' | 'question' | 'checking' | 'complete';
function BoardContent({ board }: { board: Board }) {
  return <div className="board-content"><h2>{board.heading}</h2><div className="board-rule" /><ul>{board.bullets.map((bullet, i) => <li key={i}><span className="bullet-dot"/>{bullet}</li>)}</ul>{board.fractionBars?.length ? <div className="fraction-diagram" aria-label="Fraction comparison diagram">{board.fractionBars.map((bar, i) => <div className="fraction-row" key={i}><strong>{bar.label}</strong><div className="fraction-track" style={{ gridTemplateColumns: `repeat(${Math.max(1, Math.min(24, bar.parts))},1fr)` }}>{Array.from({ length: Math.max(1, Math.min(24, bar.parts)) }, (_, j) => <span key={j} className={j < bar.filled ? 'filled' : ''}/>)}</div></div>)}</div> : null}{board.example && <div className="example-box"><Lightbulb size={19}/><p>{board.example}</p></div>}</div>;
}
function App() {
  const [studioOpen, setStudioOpen] = useState(false);
  const [studioVersion, setStudioVersion] = useState(0);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [text, setText] = useState(''); const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState('en-IN'); const [level, setLevel] = useState('Middle school');
  const [sourceTab, setSourceTab] = useState<'upload' | 'text'>('upload');
  const [mode, setMode] = useState<'live' | 'demo'>('live');
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [speechError, setSpeechError] = useState('');
  const [index, setIndex] = useState(0); const [phase, setPhase] = useState<Phase>('ready');
  const [board, setBoard] = useState<Board | null>(null); const [spokenText, setSpokenText] = useState('');
  const [answer, setAnswer] = useState(''); const [feedback, setFeedback] = useState<AnswerResult | null>(null);
  const [question, setQuestion] = useState(''); const [doubtOpen, setDoubtOpen] = useState(false); const [doubt, setDoubt] = useState('');
  const [doubtResponse, setDoubtResponse] = useState(''); const [answered, setAnswered] = useState<number[]>([]);
  const [recording, setRecording] = useState(false);
  const [pdfUrl, setPdfUrl] = useState('');
  const [continuous, setContinuous] = useState(false);
  const playbackPosition = useRef({ content: '', chunk: 0, time: 0 });
  const interrupted = useRef<{content: string; chunk: number; time: number} | null>(null);
  useEffect(() => { if (!file) { setPdfUrl(''); return; } const url = URL.createObjectURL(file); setPdfUrl(url); return () => URL.revokeObjectURL(url); }, [file]);

  const audio = useRef<HTMLAudioElement | null>(null); const generation = useRef(0); const controller = useRef<AbortController | null>(null);
  const recordingRef = useRef<Recording | null>(null); const recordTimer = useRef<ReturnType<typeof setTimeout>>(); const mounted = useRef(true);
  const session = useRef(crypto.randomUUID()); const resumeNarration = useRef<string | null>(null);
  const step = lesson?.steps[index]; const selectedLanguage = languages.find(l => l.code === language)!;

  useEffect(() => { mounted.current = true; request<Health>('/api/health').then(setHealth).catch(() => setHealthError(true)); return () => { mounted.current = false; generation.current++; controller.current?.abort(); audio.current?.pause(); recordingRef.current?.cancel(); clearTimeout(recordTimer.current); }; }, []);
  function stopAudio() { generation.current++; controller.current?.abort(); controller.current = null; if (audio.current) { audio.current.pause(); audio.current.src = ''; audio.current = null; } }
  function cancelRecording() { clearTimeout(recordTimer.current); recordingRef.current?.cancel(); recordingRef.current = null; setRecording(false); }
  async function speak(content: string, targetStep = step, finish: Phase = 'question', fromChunk = 0, fromTime = 0) {
    if (!lesson || !targetStep) return;
    stopAudio(); const version = generation.current; const abort = new AbortController(); controller.current = abort;
    setSpokenText(content); setSpeechError(''); setPhase('loading');
    const chunks = speechChunks(content);
    playbackPosition.current = { content, chunk: fromChunk, time: fromTime };
    async function playChunk(chunkIndex: number) {
      try {
        const result = await request<{ responseVersion: number; audioUrl: string; mimeType: string }>('/api/speech', { sessionId: session.current, lessonStepId: targetStep!.id, responseVersion: version, text: chunks[chunkIndex], languageCode: lesson!.language, voice: { kind: 'preset' } }, abort.signal);
        if (version !== generation.current || result.responseVersion !== version) return;
        const playback = new Audio(result.audioUrl); audio.current = playback;
        playbackPosition.current = { content, chunk: chunkIndex, time: 0 };
        if (chunkIndex === fromChunk && fromTime > 0) playback.onloadedmetadata = () => { playback.currentTime = Math.min(fromTime, Math.max(0, playback.duration - 0.1)); };
        playback.ontimeupdate = () => { if (generation.current === version) playbackPosition.current.time = playback.currentTime; };
        playback.onended = () => { if (generation.current !== version) return; if (chunkIndex + 1 < chunks.length) { setPhase('loading'); void playChunk(chunkIndex + 1); } else setPhase(finish); };
        playback.onerror = () => { if (generation.current === version) { setSpeechError('Audio could not play. You can keep learning from the text below.'); setPhase(finish); } };
        await playback.play(); if (generation.current === version) setPhase('speaking');
      } catch (e) { if (version !== generation.current || (e instanceof DOMException && e.name === 'AbortError')) return; setSpeechError(e instanceof Error ? `${e.message} Continue with the written explanation.` : 'Speech is unavailable. Continue with the written explanation.'); setPhase(finish); }
    }
    if (chunks.length) await playChunk(fromChunk); else setPhase(finish);
  }

  function interruptLesson() {
    if (!interrupted.current) interrupted.current = { ...playbackPosition.current, content: playbackPosition.current.content || step?.narration || '' };
    resumeNarration.current = interrupted.current.content;
    stopAudio(); cancelRecording(); setPhase('paused'); setDoubtOpen(true);
  }
  function resumeLesson() {
    const position = interrupted.current;
    interrupted.current = null; resumeNarration.current = null;
    setDoubtOpen(false); setDoubtResponse('');
    if (position) void speak(position.content, step, 'question', position.chunk, position.time);
    else void speak(spokenText || step!.narration);
  }
  useEffect(() => {
    if (!continuous || phase !== 'question' || doubtOpen || speechError || !lesson) return;
    const timer = setTimeout(() => { if (index + 1 < lesson.steps.length) startStep(index + 1); else setPhase('complete'); }, 1500);
    return () => clearTimeout(timer);
  }, [continuous, phase, doubtOpen, speechError, index, lesson]);

  async function createLesson(nextMode: 'live' | 'demo') {
    setError(''); setBusy(true); stopAudio(); cancelRecording(); interrupted.current = null; playbackPosition.current = {content:'',chunk:0,time:0};
    try {
      if (nextMode === 'live' && !file && !text.trim()) throw new Error('Upload a PDF or paste a little material to prepare your lesson.');
      const form = new FormData();
      if (nextMode === 'live' && file && sourceTab === 'upload') form.append('file', file);
      else form.append('text', nextMode === 'demo' ? sample : text);
      const source = await request<Material>('/api/material', form);
      const plan = await request<Lesson>('/api/lesson', { sourceId: source.sourceId, language: nextMode === 'demo' ? 'en-IN' : language, level, mode: nextMode });
      if (!plan.steps.length) throw new Error('The lesson was empty. Try a shorter source.');
      setMaterial(source); setLesson(plan); setMode(nextMode); setIndex(0); setBoard(plan.steps[0].board); setQuestion(plan.steps[0].question); setSpokenText(teachingText(plan.steps[0].narration, plan.steps[0].question)); setPhase('ready'); setFeedback(null); setAnswer(''); setAnswered([]); setSpeechError('');
    } catch (e) { setError(e instanceof Error ? e.message : 'The lesson could not be prepared. Try again.'); }
    finally { setBusy(false); }
  }
  function startStep(nextIndex: number) {
    resumeNarration.current = null; interrupted.current = null;
    if (!lesson) return; const nextStep = lesson.steps[nextIndex]; stopAudio(); cancelRecording(); setIndex(nextIndex); setBoard(nextStep.board); setQuestion(nextStep.question); setFeedback(null); setAnswer(''); setDoubtOpen(false); setDoubtResponse(''); setSpokenText(teachingText(nextStep.narration, nextStep.question)); void speak(teachingText(nextStep.narration, nextStep.question), nextStep);
  }
  async function submitAnswer() {
    resumeNarration.current = null;
    if (!step || !lesson || !answer.trim()) return; stopAudio(); const version = generation.current; setPhase('checking'); setError('');
    try {
      const result = await request<AnswerResult>('/api/answer', { lessonId: lesson.id, stepId: step.id, answer, language: lesson.language, mode });
      if (version !== generation.current) return;
      setFeedback(result); if (result.board) setBoard(result.board); if (result.followUpQuestion) setQuestion(result.followUpQuestion);
      if (result.status === 'correct') setAnswered(old => [...new Set([...old, index])]);
      setAnswer(''); await speak(teachingText(result.narration || result.feedback, result.status === 'correct' ? '' : result.followUpQuestion || question), step);
    } catch (e) { if (version !== generation.current) return; setError(e instanceof Error ? e.message : 'Your answer could not be checked.'); setPhase('question'); }
  }
  async function askDoubt() {
    if (!lesson || !step || !doubt.trim()) return; stopAudio(); const version = generation.current; setPhase('checking'); setError('');
    try { const result = await request<{ answer: string; narration: string }>('/api/doubt', { lessonId: lesson.id, stepId: step.id, question: doubt, language: lesson.language, mode }); if (version !== generation.current) return; setDoubtResponse(result.answer); setDoubt(''); await speak(result.narration || result.answer, step, 'paused'); }
    catch (e) { if (version === generation.current) { setError(e instanceof Error ? e.message : 'Your question could not be answered.'); setPhase('paused'); } }
  }
  async function endRecording() {
    const rec = recordingRef.current; if (!rec) return; recordingRef.current = null; clearTimeout(recordTimer.current); setRecording(false); const version = generation.current; setBusy(true); setError('');
    try { const blob = await rec.stop(); const form = new FormData(); form.append('file', blob, 'answer.wav'); form.append('language', lesson?.language || language); const result = await request<{ transcript: string }>('/api/transcribe', form); if (version === generation.current) { if (doubtOpen) setDoubt(result.transcript); else setAnswer(result.transcript); } }
    catch (e) { if (version === generation.current) setError(e instanceof Error ? e.message : 'Recording could not be transcribed. Type your answer instead.'); }
    finally { if (mounted.current) setBusy(false); }
  }
  async function toggleRecording() {
    if (recording) { await endRecording(); return; } stopAudio(); setPhase('paused'); setError('');
    const version = generation.current;
    try { const capture = await recordWav(); if (version !== generation.current || !mounted.current) { capture.cancel(); return; } recordingRef.current = capture; setRecording(true); recordTimer.current = setTimeout(() => void endRecording(), 25000); }
    catch (e) { setError(e instanceof Error ? e.message : 'Microphone access failed. Type your answer instead.'); }
  }
  function exitLesson() { interrupted.current = null; resumeNarration.current = null; stopAudio(); cancelRecording(); setLesson(null); setError(''); setDoubtOpen(false); }
  const statusLabel = { ready: 'Ready when you are', loading: 'Preparing voice', speaking: 'Your teacher is speaking', paused: 'Lesson paused', question: 'Your turn to think', checking: 'Thinking about your response', complete: 'Lesson complete' }[phase];

  return <div className="app-shell"><header className="topbar"><button className="brand" onClick={lesson ? exitLesson : undefined} aria-label="Paath Live home"><span className="brand-icon"><BookOpen size={23}/></span><span>paath<span className="brand-live">live</span></span></button><button className="studio-link" onClick={() => { if (lesson) { interruptLesson(); } setStudioOpen(true); }}>Lecture Studio</button><div className="provider-tag"><span className="status-dot"/> Built with Sarvam</div></header>
    {studioOpen ? <main className="studio-workspace"><div className="studio-workspace-heading"><div><span className="small-label">Your learning space</span><h1>Lecture Studio</h1><p>Turn recordings into multilingual notes and narrated lessons.</p></div><div><button className="secondary-button" onClick={() => setStudioVersion(v => v + 1)}>Recording library</button><button className="primary-button" onClick={() => setStudioOpen(false)}>Back to teacher</button></div></div><iframe key={studioVersion} className="studio-frame" title="Lecture Studio recording workspace" src="/studio/?embedded=1" /></main> : !lesson ? <main className="setup-layout"><section className="welcome"><div className="welcome-tag"><span className="tiny-spark">✳</span> Your own learning space</div><h1>A teacher that starts<br/>with your material.<span className="drawn-line"/></h1><p className="welcome-copy">Bring a chapter. Find your language. Learn through explanations, examples, and a teacher who listens.</p><div className="promise-row"><span><Headphones size={17}/> Listen & learn</span><span><Lightbulb size={17}/> Ask freely</span><span><BookOpen size={17}/> Understand deeply</span></div><div className="sample-board"><div className="sample-board-top"><span className="chalk-dot"/> A small idea, made clear<span className="board-page">From the sample lesson</span></div><BoardContent board={{ heading: 'Same whole. Different pieces.', bullets: ['A bigger denominator means smaller equal pieces.'], fractionBars: [{ label: '⅓', parts: 3, filled: 1 }, { label: '¼', parts: 4, filled: 1 }], example: 'One third is larger than one fourth when both wholes are equal.' }}/><span className="board-signature">Let’s make it make sense.</span></div></section>
    <section className="setup-card" aria-labelledby="setup-title"><div className="card-heading"><span className="small-icon"><Plus size={19}/></span><div><h2 id="setup-title">Prepare your lesson</h2><p>Something you want to understand.</p></div></div><div className="source-tabs" role="tablist" aria-label="Material source"><button role="tab" aria-selected={sourceTab === 'upload'} onClick={() => { setSourceTab('upload'); setText(''); }} className={sourceTab === 'upload' ? 'selected' : ''}><Upload size={16}/> Upload a PDF</button><button role="tab" aria-selected={sourceTab === 'text'} onClick={() => { setSourceTab('text'); setFile(null); }} className={sourceTab === 'text' ? 'selected' : ''}><FileText size={16}/> Paste material</button><button role="tab" aria-selected={false} onClick={() => setStudioOpen(true)}><Headphones size={16}/> Lecture Studio</button></div>
    {sourceTab === 'upload' ? <label className={`upload-zone ${file ? 'has-file' : ''}`}><input type="file" accept=".pdf,application/pdf" onChange={event => { const selected = event.target.files?.[0]; if (selected && selected.size > 8 * 1024 * 1024) { setError('Choose a PDF smaller than 8 MB.'); return; } setFile(selected || null); setError(''); }}/><span className="upload-symbol">{file ? <FileText size={27}/> : <Upload size={27}/>}</span><strong>{file ? file.name : 'Choose your chapter'}</strong><span>{file ? `${(file.size / 1024).toFixed(0)} KB · Click to change` : 'Click to select a PDF, up to 8 MB'}</span><span className="upload-hint">Short, text-based chapters work best</span></label> : <div className="field"><label htmlFor="material">Your notes or topic outline</label><textarea id="material" value={text} onChange={event => setText(event.target.value)} placeholder="Paste a chapter, your notes, or a topic you want to explore…" rows={6} maxLength={40000}/><small>A chapter gives the teacher more reliable context than a topic alone.</small></div>}
    <div className="setup-options"><div className="field"><label htmlFor="language">Teach me in</label><select id="language" value={language} onChange={event => setLanguage(event.target.value)}>{languages.map(item => <option key={item.code} value={item.code}>{item.native} · {item.name}</option>)}</select></div><div className="field"><label htmlFor="level">My learning level</label><select id="level" value={level} onChange={event => setLevel(event.target.value)}><option>Middle school</option><option>High school</option><option>College</option><option>Beginner</option></select></div></div>
    <div className="model-status"><span className={`status-dot ${health?.geminiConfigured ? '' : 'pending'}`}/><span>{healthError ? 'Backend is offline. Start the local server to begin.' : !health ? 'Checking your learning services…' : health.geminiConfigured ? 'Ready to prepare your lesson' : 'Live lesson setup is not complete yet'}</span></div>
    {error && <div className="error-message" role="alert">{error}</div>}<button className="primary-button full" disabled={busy || healthError} onClick={() => void createLesson('live')}>{busy ? <LoaderCircle size={18} className="spin"/> : <Sparkles size={18}/>} {busy ? 'Preparing your lesson…' : 'Prepare lesson'}{!busy && <ArrowRight size={18}/>}</button><div className="sample-divider"><span/>or explore first<span/></div><button className="sample-button" disabled={busy || healthError} onClick={() => void createLesson('demo')}><Play size={16}/> Try the English fractions sample <span className="mini-badge">Demo</span></button><p className="privacy-note">Your API keys stay on the server. The sample is a prepared lesson.</p></section><footer className="setup-footer">Learn at your pace. A question is always welcome.<span>Made for curious minds.</span></footer></main> : <main className="lesson-layout"><aside className="roadmap"><button className="back-button" onClick={exitLesson}><ArrowLeft size={15}/> Your material</button><div className="roadmap-title"><span className="small-label">Today's lesson</span><h1>{lesson.title}</h1><span className={`lesson-mode ${mode === 'demo' ? 'demo' : ''}`}>{mode === 'demo' ? 'Prepared sample' : 'Live lesson'}</span></div><div className="roadmap-list">{lesson.steps.map((item, i) => <button key={item.id} disabled={phase === 'checking'} className={`roadmap-step ${i === index ? 'active' : ''}`} onClick={() => { interrupted.current = null; playbackPosition.current = {content:teachingText(item.narration,item.question),chunk:0,time:0}; stopAudio(); cancelRecording(); setIndex(i); setBoard(item.board); setQuestion(item.question); setSpokenText(teachingText(item.narration, item.question)); setPhase('ready'); setFeedback(null); setAnswer(''); setDoubtOpen(false); }}><span className="step-number">{answered.includes(i) ? <Check size={14}/> : i + 1}</span><span>{item.title}</span>{i === index && <ChevronRight size={14}/>}</button>)}</div><div className="roadmap-progress"><div><span>Concepts checked</span><strong>{answered.length}/{lesson.steps.length}</strong></div><div className="progress-track"><span style={{ width: `${answered.length / lesson.steps.length * 100}%` }}/></div><p>Progress follows your answers,<br/>not time spent listening.</p></div><div className="source-note"><FileText size={18}/><div><strong>Your source</strong><span>{mode === 'demo' ? 'Reviewed fractions sample' : material?.title || 'Your material'}</span></div></div></aside>
    <section className="classroom">{pdfUrl && mode === 'live' && <section className="pdf-panel"><div className="pdf-heading"><strong>Your PDF · {step?.sourcePages?.length ? 'Page ' + step.sourcePages[0] : 'No page reference for this section'}</strong><a href={pdfUrl} target="_blank" rel="noreferrer">Open PDF</a></div><iframe key={step?.sourcePages?.[0] || 1} title="Current lecture PDF page" src={`${pdfUrl}#page=${step?.sourcePages?.[0] || 1}&view=FitH`} /></section>}<div className="classroom-heading"><div><span className="small-label">Your learning board</span><h2>Let’s work through it.</h2></div><span className="language-badge">{languages.find(l => l.code === lesson.language)?.native || lesson.language}</span></div><div className="learning-board"><div className="board-topline"><span><span className="chalk-dot"/> Concept {index + 1} of {lesson.steps.length}</span><span>{step?.sourcePages?.length ? `Source ${step.sourcePages.map(p => `p. ${p}`).join(', ')}` : mode === 'demo' ? 'Prepared sample' : 'Your material'}</span></div>{board && <BoardContent board={board}/>}<div className="board-bottom"><span>Take a moment. Picture the idea.</span><BookOpen size={18}/></div></div><div className="question-card"><span className="question-icon"><Lightbulb size={20}/></span><div><span className="small-label">A thought for you</span><h3>{question || step?.question}</h3><p>Explain your thinking. That helps your teacher find the next step.</p></div></div>{feedback && <div className={`feedback ${feedback.status}`} role="status">{feedback.status === 'correct' ? <CheckCircle2 size={20}/> : <Lightbulb size={20}/>}<div><strong>{feedback.status === 'correct' ? 'That reasoning connects.' : feedback.status === 'unclear' ? 'Let’s make that clearer.' : 'Let’s try another way.'}</strong><p>{feedback.feedback}</p></div></div>}
    {error && <div className="error-message" role="alert">{error}</div>}{phase === 'complete' ? <div className="completion"><CheckCircle2 size={28}/><h3>You’ve reached the end of this lesson.</h3><p>You applied your reasoning in {answered.length} of {lesson.steps.length} concept checks. Revisit any step for more practice.</p><button className="secondary-button" onClick={exitLesson}>Choose another chapter <ArrowRight size={16}/></button></div> : <div className="answer-area"><label htmlFor="answer">Your answer, in your words</label><div className="answer-input"><textarea id="answer" rows={2} placeholder="I think… because…" value={answer} onChange={event => setAnswer(event.target.value)} disabled={phase === 'checking' || recording}/><button className={`mic-button ${recording ? 'recording' : ''}`} onClick={() => void toggleRecording()} disabled={busy || phase === 'checking'} aria-label={recording ? 'Stop recording answer' : 'Record an answer'}>{recording ? <Square size={18}/> : <Mic size={19}/>}</button></div><div className="answer-actions"><small>{recording ? 'Listening… tap stop when finished (25 seconds max).' : busy ? 'Turning your speech into text…' : 'Type or speak. Review the transcript before sending.'}</small><button className="primary-button" disabled={!answer.trim() || phase === 'checking' || busy || recording} onClick={() => void submitAnswer()}>{phase === 'checking' ? <LoaderCircle className="spin" size={17}/> : <Send size={16}/>} Share my thinking</button></div></div>}
    {feedback?.status === 'correct' && phase !== 'checking' && phase !== 'complete' && <button className="next-button" onClick={() => { if (index + 1 < lesson.steps.length) startStep(index + 1); else { stopAudio(); setPhase('complete'); } }}>{index + 1 < lesson.steps.length ? 'Continue to the next concept' : 'Finish this lesson'}<ArrowRight size={18}/></button>}</section>
    <aside className="teacher-panel"><div className="teacher-label"><span className="status-dot"/> Your teacher</div><div className={`teacher-orb ${phase === 'speaking' ? 'is-speaking' : ''}`} aria-hidden="true"><span className="orb-ring"/><span className="orb-center"><BookOpen size={31}/></span><span className="orb-dot"/></div><div className="teacher-status" aria-live="polite"><span className={`waveform ${phase === 'speaking' ? 'animate' : ''}`}>{[0,1,2,3,4].map(n => <i key={n}/>)}</span><h3>{statusLabel}</h3><p>{phase === 'ready' ? 'Start when you’re ready. I’ll guide the lesson from here.' : phase === 'question' ? 'Take your time. I’m listening for how you think.' : phase === 'complete' ? 'Keep the ideas. Keep asking questions.' : 'You set the pace. We’ll find the explanation that clicks.'}</p></div><label className="continuous-option"><input type="checkbox" checked={continuous} onChange={e => setContinuous(e.target.checked)}/> Continuous teaching (skip question checkpoints)</label><div className="teacher-controls">{phase === 'speaking' || phase === 'loading' ? <button className="primary-button full" onClick={interruptLesson}><Pause size={17}/> Interrupt teaching</button> : <button className="primary-button full" disabled={phase === 'checking' || phase === 'complete' || recording || busy} onClick={resumeLesson}><Play size={17}/>{phase === 'ready' ? 'Start teaching' : phase === 'paused' ? 'Resume teaching' : 'Hear explanation again'}</button>}<div className="teacher-secondary"><button onClick={interruptLesson} disabled={phase === 'checking' || phase === 'complete'}><Plus size={16}/> I have a doubt</button><button onClick={() => void speak(teachingText(step!.narration, step!.question))} disabled={phase === 'checking' || phase === 'complete' || recording || busy} aria-label="Repeat this concept"><RotateCcw size={16}/></button></div></div>
    {speechError && <div className="speech-notice" role="status"><Volume2 size={16}/><p>{speechError}</p></div>}<div className="teacher-notes"><div><span className="small-label">{doubtResponse ? 'Your doubt, explained' : 'What we’re exploring'}</span><BookOpen size={15}/></div><p>{doubtResponse || spokenText || step?.narration}</p></div>{doubtOpen && <div className="doubt-box"><div><label htmlFor="doubt">Your doubt or teaching suggestion</label><button className="icon-button" onClick={() => { setDoubtOpen(false); setDoubtResponse(''); }} aria-label="Close doubt"><X size={16}/></button></div><textarea id="doubt" rows={3} value={doubt} onChange={event => setDoubt(event.target.value)} placeholder="Explain this more slowly, give an example, or ask a question…"/><button className="primary-button full" disabled={!doubt.trim() || phase === 'checking'} onClick={() => void askDoubt()}>{phase === 'checking' ? <LoaderCircle className="spin" size={15}/> : <Send size={15}/>} Ask my teacher</button></div>}<div className="voice-profile"><Headphones size={16}/><div><strong>Sarvam standard voice</strong><span>Custom teacher voice can be connected here.</span></div></div></aside></main>}
  </div>;
}
export default App;
