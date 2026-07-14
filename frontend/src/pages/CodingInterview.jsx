import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useNavigate } from 'react-router-dom';
import { codingService } from '../services/api';
import { useProctor } from '../hooks/useProctor.jsx';
import { useNetwork } from '../contexts/NetworkContext';
import {
  Play, Send, RefreshCw, ChevronDown, CheckCircle,
  XCircle, Loader, AlertCircle, Code2, ArrowLeft, WifiOff,
} from 'lucide-react';

const LANGUAGES = ['python', 'javascript', 'java', 'cpp', 'c'];
const TOPICS = [
  'Arrays', 'Strings', 'HashMaps', 'Trees', 'Graphs',
  'Dynamic Programming', 'Stacks', 'Queues', 'Linked Lists',
];
const DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD'];

const STARTERS = {
  python: '# Write your solution here\ndef solution():\n    pass\n',
  javascript: '// Write your solution here\nfunction solution() {\n\n}\n',
  java: 'class Solution {\n    public static void main(String[] args) {\n        // Write your solution here\n    }\n}\n',
  cpp: '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n',
  c: '#include <stdio.h>\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n',
};

const MONACO_LANG = { cpp: 'cpp', c: 'c', javascript: 'javascript', python: 'python', java: 'java' };

export const CodingInterview = () => {
  const navigate = useNavigate();
  const { fullyOnline, isOnline } = useNetwork();

  const [topic, setTopic] = useState('Arrays');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [language, setLanguage] = useState('python');

  const [problem, setProblem] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [code, setCode] = useState(STARTERS['python']);
  const [stdin, setStdin] = useState('');
  const [runOutput, setRunOutput] = useState(null);
  const [result, setResult] = useState(null);

  const [loadingProblem, setLoadingProblem] = useState(false);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const sessionKey = sessionId ? `coding_${sessionId}` : 'coding_pending';
  const { ProctorOverlay, stopProctor } = useProctor(sessionKey, 'CODING');

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    // Only reset code if no problem is loaded yet
    if (!problem) setCode(STARTERS[lang] || '');
  };

  const handleGetProblem = async () => {
    if (!fullyOnline) { setError('No internet connection. Cannot generate problem.'); return; }
    setLoadingProblem(true);
    setError('');
    setResult(null);
    setRunOutput(null);
    try {
      const res = await codingService.getProblem({ topic, difficulty, language });
      const prob = res.data.problem;
      setProblem(prob);
      setSessionId(res.data.session_id);
      // Load skeleton starter code — never the solution
      setCode(prob.starter_code || STARTERS[language] || '');
      // Pre-fill stdin with sample input so Run works immediately
      setStdin(prob.sample_input || '');
    } catch (err) {
      setError(
        err.isNetworkError
          ? 'No internet connection. Cannot generate problem.'
          : err.response?.data?.detail || 'Failed to generate problem.'
      );
    } finally {
      setLoadingProblem(false);
    }
  };

  const handleRun = async () => {
    if (!fullyOnline) { setError('No internet connection. Cannot run code.'); return; }
    setRunning(true);
    setError('');
    setRunOutput(null);
    // Auto-use sample_input if user hasn't typed custom stdin
    const stdinToUse = stdin.trim() ? stdin : (problem?.sample_input || '');
    try {
      const res = await codingService.runCode({ code, language, stdin: stdinToUse });
      setRunOutput(res.data);
    } catch (err) {
      setError(
        err.isNetworkError
          ? 'No internet connection. Cannot run code.'
          : err.response?.data?.detail || 'Run failed.'
      );
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = async () => {
    if (!problem || !sessionId) return;
    if (!fullyOnline) { setError('No internet connection. Cannot submit solution.'); return; }
    setSubmitting(true);
    setError('');
    try {
      // Strip internal fields before sending to backend
      const { starter_code, _solution_code, ...problemData } = problem;
      const res = await codingService.submit({
        session_id: sessionId,
        problem_data: problemData,
        code,
        language,
      });
      await stopProctor();
      setResult(res.data);
    } catch (err) {
      setError(
        err.isNetworkError
          ? 'Connection lost. Please reconnect and try again.'
          : err.response?.data?.detail || 'Submission failed.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark">
      <ProctorOverlay />

      {/* Offline overlay */}
      {!fullyOnline && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center">
          <div className="bg-slate-900 border border-red-700 rounded-2xl p-8 max-w-sm text-center shadow-2xl">
            <WifiOff size={48} className="text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Connection Lost</h2>
            <p className="text-slate-400 mb-4">
              {!isOnline ? 'No internet connection.' : 'Cannot reach the server.'}
            </p>
            <p className="text-slate-500 text-sm">Code execution requires an active connection.</p>
            <div className="mt-4 animate-pulse text-yellow-400 text-sm font-medium">⏳ Waiting for connection...</div>
          </div>
        </div>
      )}

      {/* Top bar */}
      <div className="border-b border-slate-700 bg-slate-900/50 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={18} />
          </button>
          <Code2 size={20} className="text-indigo-400" />
          <span className="font-bold">Coding Interview</span>
        </div>

        <div className="flex items-center gap-3">
          {[
            { val: topic, setVal: setTopic, options: TOPICS },
            { val: difficulty, setVal: setDifficulty, options: DIFFICULTIES },
            { val: language, setVal: (v) => handleLanguageChange(v), options: LANGUAGES },
          ].map(({ val, setVal, options }, i) => (
            <div key={i} className="relative">
              <select
                value={val}
                onChange={(e) => setVal(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-indigo-500 appearance-none pr-7"
              >
                {options.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
              <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            </div>
          ))}

          <button
            onClick={handleGetProblem}
            disabled={loadingProblem || !fullyOnline}
            className="btn-primary py-1.5 px-4 text-sm flex items-center gap-1.5 disabled:opacity-60"
          >
            {loadingProblem ? <Loader size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            New Problem
          </button>
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-900/20 border border-red-800 rounded-lg flex gap-2 items-center">
          <AlertCircle size={16} className="text-red-400" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {!problem && !loadingProblem && (
        <div className="flex items-center justify-center h-[70vh]">
          <div className="text-center">
            <Code2 size={56} className="text-slate-700 mx-auto mb-4" />
            <p className="text-slate-400 mb-6">Select a topic, difficulty and language, then generate a problem.</p>
            <button
              onClick={handleGetProblem}
              disabled={!fullyOnline}
              className="btn-primary px-8 py-3 text-base flex items-center gap-2 mx-auto disabled:opacity-50"
            >
              <Play size={18} /> Generate Problem
            </button>
          </div>
        </div>
      )}

      {loadingProblem && (
        <div className="flex items-center justify-center h-[70vh]">
          <div className="text-center">
            <Loader size={32} className="animate-spin text-indigo-400 mx-auto mb-3" />
            <p className="text-slate-400">Generating problem with AI...</p>
          </div>
        </div>
      )}

      {problem && !loadingProblem && (
        <div className="flex h-[calc(100vh-57px)]">

          {/* LEFT — Problem Panel */}
          <div className="w-[42%] border-r border-slate-700 overflow-y-auto p-5 space-y-4 text-sm">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-bold">{problem.title}</h2>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                  difficulty === 'EASY' ? 'bg-green-500/20 text-green-400' :
                  difficulty === 'HARD' ? 'bg-red-500/20 text-red-400' :
                  'bg-yellow-500/20 text-yellow-400'
                }`}>{difficulty}</span>
              </div>
              <p className="text-slate-300 leading-relaxed">{problem.description}</p>
            </div>

            {problem.constraints && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Constraints</p>
                <p className="text-slate-400 font-mono text-xs bg-slate-800 rounded-lg p-3">{problem.constraints}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Sample Input</p>
                <pre className="bg-slate-800 rounded-lg p-3 text-xs text-slate-300 overflow-auto">{problem.sample_input}</pre>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Sample Output</p>
                <pre className="bg-slate-800 rounded-lg p-3 text-xs text-slate-300 overflow-auto">{problem.sample_output}</pre>
              </div>
            </div>

            {problem.expected_complexity && (
              <div className="flex gap-3">
                <span className="px-2.5 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300">
                  Expected: {problem.expected_complexity}
                </span>
              </div>
            )}

            {problem.hints?.length > 0 && (
              <details className="group">
                <summary className="cursor-pointer text-xs font-semibold text-indigo-400 hover:text-indigo-300">
                  💡 Show Hints
                </summary>
                <ul className="mt-2 space-y-1">
                  {problem.hints.map((h, i) => (
                    <li key={i} className="text-xs text-slate-400">• {h}</li>
                  ))}
                </ul>
              </details>
            )}

            {problem.test_cases?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Test Cases</p>
                <div className="space-y-2">
                  {problem.test_cases.map((tc, i) => (
                    <div key={i} className="bg-slate-800 rounded-lg p-3 text-xs">
                      <span className="text-slate-500">Input: </span>
                      <span className="text-slate-300 font-mono">{tc.input}</span>
                      <br />
                      <span className="text-slate-500">Expected: </span>
                      <span className="text-green-400 font-mono">{tc.expected_output}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT — Editor + Output */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 min-h-0">
              <Editor
                language={MONACO_LANG[language] || 'python'}
                value={code}
                onChange={(v) => setCode(v || '')}
                theme="vs-dark"
                options={{
                  fontSize: 14,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  padding: { top: 16 },
                  lineNumbers: 'on',
                  automaticLayout: true,
                  suggestOnTriggerCharacters: true,
                }}
              />
            </div>

            <div className="border-t border-slate-700 bg-slate-900">
              <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-700">
                <input
                  value={stdin}
                  onChange={(e) => setStdin(e.target.value)}
                  placeholder="Custom stdin (optional)"
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleRun}
                  disabled={running || !fullyOnline}
                  className="btn-secondary py-1.5 px-4 text-sm flex items-center gap-1.5 disabled:opacity-60"
                >
                  {running ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
                  Run
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !fullyOnline}
                  className="btn-primary py-1.5 px-4 text-sm flex items-center gap-1.5 disabled:opacity-60"
                >
                  {submitting ? <Loader size={14} className="animate-spin" /> : <Send size={14} />}
                  Submit
                </button>
              </div>

              <div className="h-48 overflow-y-auto p-4">
                {runOutput && !result && (
                  <div>
                    <p className="text-xs font-semibold text-slate-400 mb-2">Output</p>
                    {runOutput.compile_error && (
                      <pre className="text-red-400 text-xs font-mono whitespace-pre-wrap mb-2">{runOutput.compile_error}</pre>
                    )}
                    {runOutput.stderr && (
                      <pre className="text-red-400 text-xs font-mono whitespace-pre-wrap mb-2">{runOutput.stderr}</pre>
                    )}
                    <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap">
                      {runOutput.output || '(no output)'}
                    </pre>
                    {runOutput.status && (
                      <p className="text-xs text-slate-500 mt-1">{runOutput.status}</p>
                    )}
                  </div>
                )}

                {result && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <div className={`flex items-center gap-2 font-semibold ${result.passed_tests === result.total_tests ? 'text-green-400' : 'text-yellow-400'}`}>
                        {result.passed_tests === result.total_tests
                          ? <CheckCircle size={18} />
                          : <XCircle size={18} />}
                        {result.passed_tests}/{result.total_tests} tests passed
                      </div>
                      <span className="text-2xl font-black text-indigo-400">{result.score?.toFixed(0)}/100</span>
                      <span className="text-xs text-slate-400">Time: {result.time_complexity}</span>
                      <span className="text-xs text-slate-400">Space: {result.space_complexity}</span>
                    </div>

                    {result.ai_feedback?.overall_feedback && (
                      <p className="text-sm text-slate-300">{result.ai_feedback.overall_feedback}</p>
                    )}

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <p className="text-green-400 font-semibold mb-1">Strengths</p>
                        {(result.ai_feedback?.strengths || []).map((s, i) => (
                          <p key={i} className="text-slate-400">• {s}</p>
                        ))}
                      </div>
                      <div>
                        <p className="text-amber-400 font-semibold mb-1">Improvements</p>
                        {(result.ai_feedback?.improvements || []).map((s, i) => (
                          <p key={i} className="text-slate-400">• {s}</p>
                        ))}
                      </div>
                    </div>

                    <button onClick={handleGetProblem} className="btn-secondary py-1.5 px-4 text-sm flex items-center gap-1.5">
                      <RefreshCw size={14} /> Next Problem
                    </button>
                  </div>
                )}

                {!runOutput && !result && (
                  <p className="text-slate-600 text-sm">Output will appear here after Run or Submit.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodingInterview;
