import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ShieldCheck } from 'lucide-react';

export const ForgotPassword = () => (
  <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 text-slate-900">
    <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-900/[0.04]">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-700">Password reset</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">Forgot your password?</h1>
        </div>
      </div>

      <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <div className="mb-2 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-amber-700" />
          <span className="font-medium">Password recovery is not available yet</span>
        </div>
        <p className="text-amber-800">
          The backend does not currently provide a password-reset endpoint. Contact your administrator for account recovery.
        </p>
      </div>

      <div className="mt-6 flex items-center justify-center text-sm text-slate-500">
        <Link to="/login" className="inline-flex items-center gap-2 font-medium text-indigo-700 hover:text-indigo-900">
          <ArrowLeft className="h-4 w-4" /> Back to sign in
        </Link>
      </div>
    </div>
  </div>
);
