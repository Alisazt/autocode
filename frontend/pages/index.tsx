import React, { useState } from 'react';
import TemplateSelector, { ProjectTemplate } from '../components/TemplateSelector';
import CrewMonitor from '../components/CrewMonitor';

export default function HomePage() {
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);

  const handleSelect = (template: ProjectTemplate) => {
    setSelectedTemplate(template);
    // For demo purposes generate a fake execution ID
    setExecutionId(`exec_${Date.now()}`);
  };

  return (
    <main className="min-h-screen p-8">
      {!selectedTemplate && <TemplateSelector onSelect={handleSelect} />}
      {selectedTemplate && executionId && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Selected template: {selectedTemplate.name}</h2>
          <CrewMonitor executionId={executionId} />
        </div>
      )}
    </main>
  );
}
