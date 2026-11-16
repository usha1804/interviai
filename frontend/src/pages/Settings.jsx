import React from 'react';
import { Mail, ShieldCheck, UserCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { PageHeader } from '../components/PageHeader';

export const Settings = () => {
  const { user } = useAuth();

  return (
    <div className="pb-8">
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Review the account details currently associated with your InterviAI profile."
      />
      <section className="max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
        <div className="flex items-start gap-4 border-b border-slate-100 pb-5">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-700">
            <UserCircle2 className="h-5 w-5" />
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">{user?.name || 'Account name unavailable'}</h3>
            <p className="mt-1 text-sm text-slate-500">Your profile details are managed by your account.</p>
          </div>
        </div>
        <dl className="divide-y divide-slate-100">
          <div className="flex items-center gap-3 py-4">
            <Mail className="h-4 w-4 text-slate-400" />
            <dt className="w-24 text-sm text-slate-500">Email</dt>
            <dd className="min-w-0 truncate text-sm font-medium text-slate-800">{user?.email || 'Not available'}</dd>
          </div>
          <div className="flex items-center gap-3 py-4">
            <ShieldCheck className="h-4 w-4 text-slate-400" />
            <dt className="w-24 text-sm text-slate-500">Role</dt>
            <dd className="text-sm font-medium capitalize text-slate-800">{user?.role?.toLowerCase() || 'User'}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
};
