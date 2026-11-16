import React from 'react';
import { BrainCircuit, Building2, Mic, Sparkles } from 'lucide-react';
import { FeatureCard } from '../components/FeatureCard';
import { PageHeader } from '../components/PageHeader';

const interviewCards = [
  { title: 'AI interview', description: 'Practice technical or behavioral questions and receive AI feedback.', to: '/interviews/ai', icon: BrainCircuit },
  { title: 'Company interview', description: 'Choose a supported company and practice with the existing interview tools.', to: '/interviews/company', icon: Building2 },
  { title: 'Adaptive interview', description: 'Use the interview flow with an adaptive practice focus.', to: '/interviews/adaptive', icon: Sparkles },
  { title: 'Voice interview', description: 'Practice spoken responses with the available voice interview experience.', to: '/interviews/voice', icon: Mic },
];

export const InterviewsOverview = () => (
  <div className="pb-8">
    <PageHeader
      eyebrow="Interview suite"
      title="Choose your interview format"
      description="Practice with the interview tools available in your workspace."
    />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {interviewCards.map((card) => <FeatureCard key={card.title} {...card} />)}
    </div>
  </div>
);
