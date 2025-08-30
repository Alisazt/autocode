import React, { useState } from 'react';

// Define the shape of a project template based on the specification
export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  category: 'api' | 'web' | 'fullstack';
  stack: {
    frontend?: string[];
    backend?: string[];
    database?: string[];
    infrastructure?: string[];
  };
  estimated: {
    duration_minutes: number;
    cost_usd: number;
    complexity: 'simple' | 'medium' | 'complex';
  };
  team_config: 'compact' | 'full';
  hitl_checkpoints: string[];
}

// A small catalogue of templates for demonstration purposes
const TEMPLATES: ProjectTemplate[] = [
  {
    id: 'rest_api',
    name: 'REST API Service',
    description: 'FastAPI + PostgreSQL + Docker + CI/CD',
    category: 'api',
    stack: {
      backend: ['Python', 'FastAPI', 'SQLAlchemy'],
      database: ['PostgreSQL'],
      infrastructure: ['Docker', 'GitHub Actions'],
    },
    estimated: {
      duration_minutes: 45,
      cost_usd: 2.5,
      complexity: 'simple',
    },
    team_config: 'compact',
    hitl_checkpoints: ['architecture_review'],
  },
  {
    id: 'nextjs_web_app',
    name: 'Next.js Web Application',
    description: 'React + TypeScript + Tailwind + Vercel deployment',
    category: 'web',
    stack: {
      frontend: ['Next.js', 'TypeScript', 'Tailwind CSS'],
      backend: ['Supabase'],
      infrastructure: ['Vercel', 'GitHub Actions'],
    },
    estimated: {
      duration_minutes: 60,
      cost_usd: 3.75,
      complexity: 'medium',
    },
    team_config: 'compact',
    hitl_checkpoints: ['architecture_review', 'ui_review'],
  },
  {
    id: 'fullstack_saas',
    name: 'Full-Stack SaaS Platform',
    description: 'Complete SaaS with auth, payments, admin panel',
    category: 'fullstack',
    stack: {
      frontend: ['Next.js', 'TypeScript', 'Tailwind'],
      backend: ['Python', 'FastAPI', 'Celery'],
      database: ['PostgreSQL', 'Redis'],
      infrastructure: ['Docker', 'Kubernetes', 'GitHub Actions'],
    },
    estimated: {
      duration_minutes: 180,
      cost_usd: 15.0,
      complexity: 'complex',
    },
    team_config: 'full',
    hitl_checkpoints: ['architecture_review', 'security_review', 'release_approval'],
  },
];

interface TemplateSelectorProps {
  onSelect: (template: ProjectTemplate) => void;
}

export default function TemplateSelector({ onSelect }: TemplateSelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredTemplates = selectedCategory
    ? TEMPLATES.filter((t) => t.category === selectedCategory)
    : TEMPLATES;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Choose Project Template</h2>

      {/* Category Filter */}
      <div className="flex gap-2 mb-8">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded ${!selectedCategory ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          All
        </button>
        {['api', 'web', 'fullstack'].map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded capitalize ${selectedCategory === category ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Template Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            className="border rounded-lg p-6 hover:shadow-lg cursor-pointer transition-shadow"
            onClick={() => onSelect(template)}
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-semibold text-lg">{template.name}</h3>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  template.estimated.complexity === 'simple'
                    ? 'bg-green-100 text-green-800'
                    : template.estimated.complexity === 'medium'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {template.estimated.complexity}
              </span>
            </div>

            <p className="text-gray-600 text-sm mb-4">{template.description}</p>

            {/* Stack Tags */}
            <div className="mb-4">
              <div className="flex flex-wrap gap-1">
                {[
                  ...(template.stack.frontend || []),
                  ...(template.stack.backend || []),
                  ...(template.stack.database || []),
                ]
                  .slice(0, 4)
                  .map((tech) => (
                    <span
                      key={tech}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                    >
                      {tech}
                    </span>
                  ))}
                {[
                  ...(template.stack.frontend || []),
                  ...(template.stack.backend || []),
                  ...(template.stack.database || []),
                ].length > 4 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    +{[
                      ...(template.stack.frontend || []),
                      ...(template.stack.backend || []),
                      ...(template.stack.database || []),
                    ].length - 4}{' '}
                    more
                  </span>
                )}
              </div>
            </div>

            {/* Estimates */}
            <div className="flex justify-between text-sm text-gray-500 mb-4">
              <span>⏱ {template.estimated.duration_minutes}min</span>
              <span>💰 ${template.estimated.cost_usd}</span>
              <span>👥 {template.team_config}</span>
            </div>

            {/* HITL Checkpoints */}
            <div className="text-xs text-gray-500">
              <span>Reviews: {template.hitl_checkpoints.length}</span>
              <div className="mt-1">
                {template.hitl_checkpoints.map((checkpoint) => (
                  <span
                    key={checkpoint}
                    className="inline-block w-2 h-2 bg-orange-400 rounded-full mr-1"
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Custom Template Option */}
      <div className="mt-8 p-6 border-2 border-dashed border-gray-300 rounded-lg text-center">
        <h3 className="font-semibold text-gray-700 mb-2">Need something custom?</h3>
        <p className="text-gray-500 text-sm mb-4">
          Build your own template or request a new one
        </p>
        <button className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
          Create Custom Template
        </button>
      </div>
    </div>
  );
}
