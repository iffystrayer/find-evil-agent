import { motion } from 'framer-motion';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

interface AuditStep {
  id: string;
  label: string;
  status: 'completed' | 'in-progress' | 'pending';
  timestamp?: string;
}

interface AuditTrailProps {
  steps: AuditStep[];
}

export const AuditTrail = ({ steps }: AuditTrailProps) => {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold mb-4">Audit Trail</h3>

      {steps.map((step, index) => {
        const Icon = step.status === 'completed'
          ? CheckCircle2
          : step.status === 'in-progress'
          ? Clock
          : AlertCircle;

        const statusColor = step.status === 'completed'
          ? 'text-green-400'
          : step.status === 'in-progress'
          ? 'text-blue-400'
          : 'text-gray-500';

        return (
          <motion.div
            key={step.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            <Icon className={`w-5 h-5 ${statusColor}`} />

            <div className="flex-1">
              <p className="font-medium">{step.label}</p>
              {step.timestamp && (
                <p className="text-xs text-gray-400">{step.timestamp}</p>
              )}
            </div>

            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="absolute left-[22px] top-[44px] w-0.5 h-6 bg-gradient-to-b from-white/20 to-transparent" />
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

// Example usage with default steps
export const DefaultAuditTrail = () => {
  const defaultSteps: AuditStep[] = [
    { id: '1', label: 'Static Analysis', status: 'completed', timestamp: '2s ago' },
    { id: '2', label: 'AST Traverse', status: 'completed', timestamp: '1s ago' },
    { id: '3', label: 'Entropy Check', status: 'completed', timestamp: 'just now' },
    { id: '4', label: 'Tool Selection', status: 'in-progress' },
    { id: '5', label: 'Execution', status: 'pending' },
  ];

  return <AuditTrail steps={defaultSteps} />;
};
