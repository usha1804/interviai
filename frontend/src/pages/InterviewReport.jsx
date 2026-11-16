import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { reportService } from '../services/api';

const listValue = (value) => Array.isArray(value) ? value : value ? [value] : [];
const itemLabel = (value) =>
  typeof value === 'string' ? value : value?.title || value?.description || JSON.stringify(value);

export const InterviewReport = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const fetchReport = async () => {
      try {
        const { data } = await reportService.get(id);
        if (active) setReport(data);
      } catch (requestError) {
        if (requestError.response?.status !== 404) throw requestError;
        const { data } = await reportService.generate(id);
        if (active) setReport(data);
      }
    };
    fetchReport()
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'This report could not be loaded.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [id]);

  if (loading) {
    return <div className="h-64 animate-pulse rounded-2xl bg-white ring-1 ring-slate-200" aria-label="Loading report" />;
  }

  if (error || !report) {
    return (
      <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
        <div className="flex items-start gap-2"><AlertCircle className="h-4 w-4 shrink-0" />{error || 'No report is available for this session.'}</div>
        <Link to="/history" className="mt-4 inline-flex items-center gap-2 font-medium text-red-800 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to history
        </Link>
      </div>
    );
  }

  const scoreMetrics = [
    ['Overall score', report.overall_score],
    ['Technical score', report.technical_score],
    ['Communication score', report.communication_score],
  ];
  const topicScores = Object.values((report.question_feedback || []).reduce((topics, item) => {
    if (item.score == null) return topics;
    const topic = item.category || 'General';
    const entry = topics[topic] || { topic, total: 0, count: 0 };
    entry.total += Number(item.score);
    entry.count += 1;
    topics[topic] = entry;
    return topics;
  }, {}));

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        eyebrow="Interview report"
        title="Session feedback"
        description="A summary of the feedback saved for this interview."
        action={<Link to="/history" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900"><ArrowLeft className="h-4 w-4" /> Back to history</Link>}
      />
      <section className="grid gap-4 sm:grid-cols-3">
        {scoreMetrics.map(([label, value]) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-900">{value == null ? '—' : Number(value).toFixed(1)}</p>
          </div>
        ))}
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
        <h3 className="text-base font-semibold text-slate-900">Summary</h3>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{report.summary || report.ai_summary || 'No written summary was saved for this session.'}</p>
      </section>
      {topicScores.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
          <h3 className="text-base font-semibold text-slate-900">Topic performance</h3>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {topicScores.map(({ topic, total, count }) => (
              <div key={topic} className="rounded-lg bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-700">{topic}</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">{(total / count).toFixed(1)}<span className="text-sm font-normal text-slate-500"> / 10</span></p>
              </div>
            ))}
          </div>
        </section>
      )}
      {report.question_feedback?.length > 0 && (
        <section className="space-y-4">
          <h3 className="text-base font-semibold text-slate-900">Question-by-question feedback</h3>
          {report.question_feedback.map((item, index) => (
            <article key={`${index}-${item.category}`} className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.category} · {item.difficulty}</p>
                  <h4 className="mt-2 font-semibold leading-6 text-slate-900">{item.question}</h4>
                </div>
                <p className="rounded-lg bg-indigo-50 px-3 py-1.5 text-sm font-semibold text-indigo-700">
                  {item.score == null ? 'Not scored' : `${Number(item.score).toFixed(1)} / 10`}
                </p>
              </div>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.feedback || 'No feedback available.'}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <p className="text-sm text-slate-600"><span className="font-medium text-slate-800">Strengths: </span>{item.strengths || '—'}</p>
                <p className="text-sm text-slate-600"><span className="font-medium text-slate-800">To improve: </span>{item.improvements || '—'}</p>
              </div>
            </article>
          ))}
        </section>
      )}
      <div className="grid gap-5 lg:grid-cols-2">
        {[
          { title: 'Strengths', values: report.strengths_list || report.strengths },
          { title: 'Areas to improve', values: report.improvements_list || report.weaknesses || report.topics_to_improve },
          { title: 'Recommendations', values: report.recommendations || report.learning_recommendations },
        ].map(({ title, values }) => (
          <section key={title} className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
            <h3 className="flex items-center gap-2 text-base font-semibold text-slate-900">
              <CheckCircle2 className="h-4 w-4 text-indigo-600" /> {title}
            </h3>
            {listValue(values).length ? (
              <ul className="mt-4 space-y-2">
                {listValue(values).map((value, index) => <li key={`${title}-${index}`} className="text-sm leading-6 text-slate-600">{itemLabel(value)}</li>)}
              </ul>
            ) : <p className="mt-3 text-sm text-slate-500">No details are available for this section.</p>}
          </section>
        ))}
      </div>
    </div>
  );
};
