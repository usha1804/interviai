import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Building2, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { ragService } from '../services/api';

export const CompanySelection = () => {
  const [companies, setCompanies] = useState([]);
  const [selected, setSelected] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    ragService.listCompanies()
      .then(({ data }) => {
        if (!active) return;
        const availableCompanies = Array.isArray(data?.companies) ? data.companies : [];
        setCompanies(availableCompanies);
        setSelected(availableCompanies[0] || '');
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'Supported companies could not be loaded.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const filteredCompanies = useMemo(() => {
    const searchTerm = query.trim().toLowerCase();
    return companies.filter((company) => company.toLowerCase().includes(searchTerm));
  }, [companies, query]);

  return (
    <div className="pb-8">
      <PageHeader
        eyebrow="Interview suite"
        title="Company interview"
        description="Select a company supported by this workspace to start a focused practice session."
      />

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="font-semibold text-slate-900">Available companies</h3>
            <p className="mt-1 text-sm text-slate-500">Options are loaded from the interview service.</p>
          </div>
          <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 sm:w-64">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              aria-label="Search companies"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search companies"
              className="min-w-0 flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-slate-400"
            />
          </label>
        </div>

        {error && <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}

        {loading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading companies">
            {[1, 2, 3].map((item) => <div key={item} className="h-20 animate-pulse rounded-xl bg-slate-100" />)}
          </div>
        ) : !error && !filteredCompanies.length ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <Building2 className="mx-auto h-6 w-6 text-slate-400" />
            <p className="mt-3 text-sm font-medium text-slate-800">{companies.length ? 'No company matches your search' : 'No companies are currently available'}</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCompanies.map((company) => (
              <button
                key={company}
                type="button"
                onClick={() => setSelected(company)}
                aria-pressed={selected === company}
                className={`flex min-h-20 items-center gap-3 rounded-xl border p-4 text-left transition ${
                  selected === company
                    ? 'border-indigo-300 bg-indigo-50 text-indigo-900'
                    : 'border-slate-200 text-slate-800 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-600 ring-1 ring-slate-200"><Building2 className="h-4 w-4" /></span>
                <span className="font-medium">{company}</span>
              </button>
            ))}
          </div>
        )}

        <div className="mt-6 flex flex-col gap-4 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-xl text-xs leading-5 text-slate-500">
            Practice prompts are generated through this application. This is not a confidential or official company question bank.
          </p>
          {selected && !error && (
            <Link
              to="/interview/new"
              state={{ type: 'COMPANY', company: selected }}
              className="inline-flex min-h-10 shrink-0 items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
            >
              Practice for {selected}
            </Link>
          )}
        </div>
      </section>
    </div>
  );
};
