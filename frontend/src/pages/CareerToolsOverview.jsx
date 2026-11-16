import React from 'react';
import { Briefcase, Github, FileSearch } from 'lucide-react';
import { FeatureCard } from '../components/FeatureCard';
import { PageHeader } from '../components/PageHeader';

const cards = [
  { title: 'Resume analyzer', description: 'Compare your resume against a job description using the existing analysis service.', to: '/career-tools/resume-analyzer', icon: FileSearch },
  { title: 'Job description', description: 'Review how your experience aligns with a target role.', to: '/career-tools/job-description', icon: Briefcase },
  { title: 'GitHub analyzer', description: 'Get an AI assessment of the repositories you choose to share.', to: '/career-tools/github', icon: Github },
];

export const CareerToolsOverview = () => (
  <div className="pb-8">
    <PageHeader
      eyebrow="Career tools"
      title="Make your next move with clarity"
      description="Explore tools to prepare your resume, profile, and career plan."
    />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => <FeatureCard key={card.title} {...card} />)}
      <FeatureCard title="AI career coach" description="Get recommendations from your saved career materials and interview data." to="/career-coach" icon={Briefcase} />
    </div>
  </div>
);
