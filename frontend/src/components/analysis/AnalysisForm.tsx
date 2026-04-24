import { motion } from 'framer-motion';
import { Play, Loader2, Zap, Target } from 'lucide-react';
import { useState } from 'react';

interface AnalysisFormProps {
  onSubmit: (data: { incident: string; goal: string; format: string; mode: string; maxIterations?: number }) => void;
  loading?: boolean;
}

export const AnalysisForm = ({ onSubmit, loading = false }: AnalysisFormProps) => {
  const [incident, setIncident] = useState('');
  const [goal, setGoal] = useState('');
  const [format, setFormat] = useState('html');
  const [mode, setMode] = useState<'single' | 'investigative'>('single');
  const [maxIterations, setMaxIterations] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ incident, goal, format, mode, maxIterations: mode === 'investigative' ? maxIterations : undefined });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Mode Toggle */}
      <div>
        <label className="block text-sm font-medium mb-2">Analysis Mode</label>
        <div className="grid grid-cols-2 gap-3">
          <motion.button
            type="button"
            onClick={() => setMode('single')}
            className={`
              px-4 py-3 rounded-xl border flex items-center justify-center gap-2 transition-colors
              ${mode === 'single'
                ? 'bg-purple-500/20 border-purple-500/50 text-purple-200'
                : 'bg-white/5 border-white/10 text-gray-400 hover:border-white/20'
              }
            `}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Zap className="w-4 h-4" />
            <span className="font-medium">Single Analysis</span>
          </motion.button>
          <motion.button
            type="button"
            onClick={() => setMode('investigative')}
            className={`
              px-4 py-3 rounded-xl border flex items-center justify-center gap-2 transition-colors
              ${mode === 'investigative'
                ? 'bg-blue-500/20 border-blue-500/50 text-blue-200'
                : 'bg-white/5 border-white/10 text-gray-400 hover:border-white/20'
              }
            `}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Target className="w-4 h-4" />
            <span className="font-medium">Investigative Mode</span>
          </motion.button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {mode === 'single'
            ? 'Quick single-shot analysis with immediate results'
            : 'Autonomous iterative investigation with HITL approval gates'
          }
        </p>
      </div>

      {/* Max Iterations (only for investigative mode) */}
      {mode === 'investigative' && (
        <div>
          <label className="block text-sm font-medium mb-2">Max Iterations</label>
          <input
            type="number"
            min={1}
            max={10}
            value={maxIterations}
            onChange={(e) => setMaxIterations(parseInt(e.target.value) || 5)}
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-blue-400 focus:outline-none transition-colors"
          />
          <p className="text-xs text-gray-500 mt-1">
            Maximum number of investigative iterations (1-10)
          </p>
        </div>
      )}

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
