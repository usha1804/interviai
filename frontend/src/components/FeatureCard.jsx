import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const FeatureCard = ({ title, description, to, icon: Icon }) => (
  <Link
    to={to}
    className="group flex min-h-40 flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md hover:shadow-slate-900/[0.05]"
  >
    <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
      <Icon className="h-5 w-5" />
    </span>
    <span className="mt-4 flex items-center justify-between gap-3">
      <span className="text-sm font-semibold text-slate-900">{title}</span>
      <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-400 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-indigo-700" />
    </span>
    <span className="mt-1 text-sm leading-5 text-slate-500">{description}</span>
  </Link>
);
