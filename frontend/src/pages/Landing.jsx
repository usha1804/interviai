import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Navbar } from '../components/Navbar';
import { ArrowRight, Zap, Target, TrendingUp } from 'lucide-react';

export const Landing = () => {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-dark">
        {/* Hero Section */}
        <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 gradient-text">
              Master Your Interviews with AI
            </h1>
            <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto">
              Practice technical, HR, and mixed interviews with AI-powered question generation,
              real-time feedback, and personalized improvement plans.
            </p>
            <div className="flex gap-4 justify-center">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="btn-primary flex items-center gap-2"
                >
                  Go to Dashboard <ArrowRight size={20} />
                </Link>
              ) : (
                <>
                  <Link to="/signup" className="btn-primary">
                    Get Started <ArrowRight size={20} />
                  </Link>
                  <Link to="/login" className="btn-secondary">
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-8 mt-20">
            <div className="card text-center">
              <Zap className="text-yellow-500 mx-auto mb-4" size={32} />
              <h3 className="text-xl font-bold mb-2">AI-Powered</h3>
              <p className="text-slate-400">
                Advanced AI generates realistic interview questions tailored to your needs
              </p>
            </div>

            <div className="card text-center">
              <Target className="text-blue-500 mx-auto mb-4" size={32} />
              <h3 className="text-xl font-bold mb-2">Instant Feedback</h3>
              <p className="text-slate-400">
                Get immediate AI evaluation and actionable improvement suggestions
              </p>
            </div>

            <div className="card text-center">
              <TrendingUp className="text-green-500 mx-auto mb-4" size={32} />
              <h3 className="text-xl font-bold mb-2">Track Progress</h3>
              <p className="text-slate-400">
                Monitor your performance with detailed analytics and skill assessments
              </p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-slate-900 py-16 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-6">Ready to ace your interviews?</h2>
            {!isAuthenticated && (
              <Link to="/signup" className="btn-primary text-lg px-8 py-3 inline-block">
                Start Free Trial
              </Link>
            )}
          </div>
        </section>
      </div>
    </>
  );
};
