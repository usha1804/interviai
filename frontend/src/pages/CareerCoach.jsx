import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { careerCoachService } from '../services/api';

const scoreRows = [
  ['Resume match', 'resume_match_score'],
  ['Job match', 'job_match_score'],
  ['Interview readiness', 'interview_readiness'],
  ['Hiring probability', 'hiring_probability'],
];

const asList = (value) => Array.isArray(value) ? value : [];

export const CareerCoach = () => {
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    careerCoachService.getProfile()
      .then(({ data }) => {
        if (active) setProfile(data.profile);
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'Your career profile could not be loaded.');
      })
      .finally(() => {
        if (active) setInitializing(false);
      });
    return () => { active = false; };
  }, []);

  const runAnalysis = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await careerCoachService.analyze({});
      setAnalysis(data);
      setProfile(data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Career analysis could not be completed.');
    } finally {
      setLoading(false);
    }
  };

  const results = analysis || profile;

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        eyebrow="Career tools"
        title="AI career coach"
        description="Get a career-readiness assessment from your saved resume, job description, and practice data."
        action={
          <button
            type="button"
            onClick={runAnalysis}
            disabled={loading || initializing}
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? 'Analyzing…' : 'Run career analysis'}
          </button>
        }
      />

      {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}

      {initializing ? (
        <div className="h-44 animate-pulse rounded-2xl bg-white ring-1 ring-slate-200" aria-label="Loading career profile" />
      ) : !results ? (
        <section className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-indigo-600" />
          <h3 className="mt-4 text-base font-semibold text-slate-900">Build your career snapshot</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
            The coach analyzes your saved resume, job description, and interview results. Add your career materials first to get a useful assessment.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link to="/career-tools/resume-analyzer" className="inline-flex items-center gap-1 text-sm font-medium text-indigo-700 hover:text-indigo-900">Resume analyzer <ArrowRight className="h-4 w-4" /></Link>
            <Link to="/career-tools/job-description" className="inline-flex items-center gap-1 text-sm font-medium text-indigo-700 hover:text-indigo-900">Job description <ArrowRight className="h-4 w-4" /></Link>
          </div>
        </section>
      ) : (
        <div className="space-y-5">
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {scoreRows.map(([label, key]) => (
              <div key={key} className="rounded-xl border border-slate-200 bg-white p-5">
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {typeof results[key] === 'number' ? `${results[key].toFixed(1)}%` : '—'}
                </p>
              </div>
            ))}
          </section>
          {results.ai_summary && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
              <h3 className="text-base font-semibold text-slate-900">Career summary</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{results.ai_summary}</p>
            </section>
          )}
          <section className="grid gap-5 lg:grid-cols-2">
            {[
              ['Skills to build', results.missing_skills],
              ['Recommended projects', results.recommended_projects],
              ['Recommended courses', results.recommended_courses],
              ['Recommended certifications', results.recommended_certifications],
            ].map(([title, values]) => (
              <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                {asList(values).length ? (
                  <ul className="mt-3 space-y-2 text-sm text-slate-600">
                    {asList(values).map((value, index) => <li key={`${title}-${index}`}>{typeof value === 'string' ? value : value.title || JSON.stringify(value)}</li>)}
                  </ul>
                ) : <p className="mt-2 text-sm text-slate-500">No recommendations are available.</p>}
              </div>
            ))}
          </section>
        </div>
      )}
    </div>
  );
};
