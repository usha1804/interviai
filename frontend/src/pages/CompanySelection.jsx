import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { ragService } from '../services/api';

const COMPANY_OPTIONS = [
  'Google', 'Amazon', 'Microsoft', 'Meta', 'Apple', 'Netflix', 'Accenture', 'TCS',
  'Infosys', 'Wipro', 'Capgemini', 'Deloitte', 'Cognizant', 'IBM', 'Oracle',
  'Salesforce', 'Adobe', 'Uber', 'Flipkart', 'Atlassian'
];

export const CompanySelection = () => {
  const [companies, setCompanies] = useState(COMPANY_OPTIONS);
  const [selected, setSelected] = useState('Google');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ragService.listCompanies().then((res) => {
      if (Array.isArray(res?.data?.companies)) {
        setCompanies(res.data.companies);
      }
    }).finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold">Company-Specific Interview Engine</h1>
            <p className="mt-2 text-slate-400">Select a company to start a RAG-grounded interview flow.</p>
          </div>

          {loading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center text-slate-400">Loading supported companies…</div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {companies.map((company) => (
                <button
                  key={company}
                  onClick={() => setSelected(company)}
                  className={`rounded-2xl border p-4 text-left transition ${selected === company ? 'border-amber-500 bg-amber-500/10 text-amber-300' : 'border-slate-800 bg-slate-900/70 text-slate-200 hover:border-slate-600'}`}
                >
                  <div className="font-semibold">{company}</div>
                  <div className="mt-2 text-sm text-slate-400">Company-specific interview questions and guidance</div>
                </button>
              ))}
            </div>
          )}

          <div className="mt-8 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div>
              <div className="text-sm text-slate-400">Selected company</div>
              <div className="font-semibold text-white">{selected}</div>
            </div>
            <Link
              to="/interview/new"
              state={{ type: 'COMPANY', company: selected }}
              className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 font-semibold text-white"
            >
              Start Company Interview
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};
