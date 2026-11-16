import React from 'react';
import { Code2, Database, MessageSquare } from 'lucide-react';
import { FeatureCard } from '../components/FeatureCard';
import { PageHeader } from '../components/PageHeader';

const practiceCards = [
  { title: 'Coding practice', description: 'Work through coding interview problems and review your results.', to: '/practice/coding', icon: Code2 },
  { title: 'System design', description: 'Practice architecture discussions and design trade-offs.', to: '/practice/system-design', icon: Database },
  { title: 'Technical questions', description: 'Prepare with technical topics supported by the interview engine.', to: '/practice/technical', icon: MessageSquare },
];

export const PracticeOverview = () => (
  <div className="pb-8">
    <PageHeader
      eyebrow="Practice"
      title="Build your interview skills"
      description="Choose a focused exercise and keep progressing at your own pace."
    />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {practiceCards.map((card) => <FeatureCard key={card.title} {...card} />)}
    </div>
  </div>
);
