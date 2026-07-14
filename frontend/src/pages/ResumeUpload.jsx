import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeService } from '../services/api';
import {
  Upload, FileText, X, CheckCircle, AlertCircle,
  Loader, ChevronRight, Trash2,
} from 'lucide-react';

const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED = ['pdf', 'docx', 'doc'];

export const ResumeUpload = () => {
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);   // parsed resume from API
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);
  const [questions, setQuestions] = useState(null);

  const validate = (f) => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) return `File type .${ext} not allowed. Use PDF or DOCX.`;
    if (f.size > MAX_SIZE) return 'File exceeds 5 MB limit.';
    return null;
  };

  const pickFile = (f) => {
    const err = validate(f);
    if (err) { setError(err); return; }
    setError('');
    setFile(f);
    setResult(null);
    setQuestions(null);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setError('');

    // Simulate progress while waiting
    const interval = setInterval(() => {
      setProgress((p) => (p < 85 ? p + 5 : p));
    }, 200);

    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await resumeService.upload(fd);
      clearInterval(interval);
      setProgress(100);
      setResult(res.data);
    } catch (err) {
      clearInterval(interval);
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!result) return;
    setGenerating(true);
    setError('');
    try {
      const res = await resumeService.generateQuestions(result.id);
      setQuestions(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate questions.');
    } finally {
      setGenerating(false);
    }
  };

  const handleStartResumeInterview = () => {
    navigate('/resume/interview', { state: { resume: result, questions } });
  };

  return (
    <div className="min-h-screen bg-dark py-8 px-4">
      <div className="max-w-3xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-1">Resume Upload</h1>
          <p className="text-slate-400 text-sm">
            Upload your resume to get personalized AI interview questions.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 p-4 bg-red-900/20 border border-red-800 rounded-lg flex gap-3 items-start">
            <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={16} />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Upload Zone */}
        {!result && (
          <div className="card mb-6">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => !file && inputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer
                ${dragging ? 'border-indigo-500 bg-indigo-500/10' : 'border-slate-700 hover:border-slate-500'}
                ${file ? 'cursor-default' : ''}`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,.doc"
                className="hidden"
                onChange={(e) => { if (e.target.files[0]) pickFile(e.target.files[0]); }}
              />

              {!file ? (
                <>
                  <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                  <p className="font-semibold text-slate-300">
                    Drag & drop your resume here
                  </p>
                  <p className="text-slate-500 text-sm mt-1">
                    or click to browse — PDF, DOCX (max 5 MB)
                  </p>
                </>
              ) : (
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <FileText className="text-indigo-400 shrink-0" size={28} />
                    <div className="text-left">
                      <p className="font-medium text-sm">{file.name}</p>
                      <p className="text-slate-500 text-xs">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); setFile(null); setProgress(0); }}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              )}
            </div>

            {/* Progress bar */}
            {uploading && (
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Uploading & analysing with AI...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {file && !uploading && progress === 0 && (
              <button
                onClick={handleUpload}
                className="w-full mt-4 btn-primary py-3 flex items-center justify-center gap-2"
              >
                <Upload size={18} /> Upload & Analyse Resume
              </button>
            )}
          </div>
        )}

        {/* Analysis Result */}
        {result && (
          <div className="space-y-5">
            <div className="card border border-green-800/40 bg-green-900/10">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="text-green-400" size={20} />
                <div>
                  <p className="font-semibold">{result.file_name}</p>
                  <p className="text-xs text-slate-400">Resume analysed successfully</p>
                </div>
                <button
                  onClick={() => { setResult(null); setFile(null); setProgress(0); setQuestions(null); }}
                  className="ml-auto text-slate-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              {/* Skills */}
              {result.skills?.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {result.skills.map((s) => (
                      <span key={s} className="px-2.5 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {result.projects?.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Projects</p>
                  <ul className="space-y-1">
                    {result.projects.map((p) => (
                      <li key={p} className="text-sm text-slate-300 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0" />{p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Experience */}
              {result.experience?.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Experience</p>
                  <ul className="space-y-1">
                    {result.experience.map((e, i) => (
                      <li key={i} className="text-sm text-slate-300">
                        {e.role} {e.company ? `@ ${e.company}` : ''} {e.duration ? `(${e.duration})` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Education */}
              {result.education?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Education</p>
                  <ul className="space-y-1">
                    {result.education.map((e, i) => (
                      <li key={i} className="text-sm text-slate-300">
                        {e.degree} {e.institution ? `— ${e.institution}` : ''} {e.year ? `(${e.year})` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Generate Questions */}
            {!questions && (
              <button
                onClick={handleGenerateQuestions}
                disabled={generating}
                className="w-full btn-primary py-4 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {generating
                  ? <><Loader size={18} className="animate-spin" /> Generating Questions...</>
                  : <><ChevronRight size={18} /> Generate Resume-Based Questions</>}
              </button>
            )}

            {/* Questions Preview */}
            {questions && (
              <div className="card">
                <h3 className="font-bold mb-4">Generated Questions</h3>

                {[
                  { label: 'Technical', items: questions.technical, color: 'text-indigo-400' },
                  { label: 'Project Based', items: questions.project_based, color: 'text-purple-400' },
                  { label: 'Behavioral', items: questions.behavioral, color: 'text-green-400' },
                ].map(({ label, items, color }) => (
                  <div key={label} className="mb-4">
                    <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${color}`}>{label}</p>
                    <ol className="space-y-1.5">
                      {items.map((q, i) => (
                        <li key={i} className="text-sm text-slate-300 flex gap-2">
                          <span className="text-slate-500 shrink-0">{i + 1}.</span> {q}
                        </li>
                      ))}
                    </ol>
                  </div>
                ))}

                <button
                  onClick={handleStartResumeInterview}
                  className="w-full mt-4 btn-primary py-4 flex items-center justify-center gap-2"
                >
                  Start Resume Interview <ChevronRight size={18} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUpload;
