import { motion } from 'framer-motion';
import { Play, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface AnalysisFormProps {
  onSubmit: (data: { incident: string; goal: string; format: string }) => void;
  loading?: boolean;
}

export const AnalysisForm = ({ onSubmit, loading = false }: AnalysisFormProps) => {
  const [incident, setIncident] = useState('');
  const [goal, setGoal] = useState('');
  const [format, setFormat] = useState('html');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ incident, goal, format });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Incident Description */}
      <div>
        <label className="block text-sm font-medium mb-2">Incident Description</label>
        <textarea
          value={incident}
          onChange={(e) => setIncident(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-purple-400 focus:outline-none transition-colors resize-none"
          rows={3}
          placeholder="e.g., Ransomware detected encrypting files on Windows server..."
          required
        />
      </div>

      {/* Investigation Goal */}
      <div>
        <label className="block text-sm font-medium mb-2">Investigation Goal</label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-purple-400 focus:outline-none transition-colors resize-none"
          rows={2}
          placeholder="e.g., Identify malicious processes and IOCs..."
          required
        />
      </div>

      {/* Format Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">Report Format</label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-purple-400 focus:outline-none transition-colors"
        >
          <option value="html">HTML (with interactive graph)</option>
          <option value="markdown">Markdown</option>
        </select>
      </div>

      {/* Submit Button */}
      <motion.button
        type="submit"
        disabled={loading}
        className={`
          w-full glass-button flex items-center justify-center gap-2
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        whileHover={!loading ? { scale: 1.02 } : {}}
        whileTap={!loading ? { scale: 0.98 } : {}}
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            Start Analysis
          </>
        )}
      </motion.button>
    </form>
  );
};
