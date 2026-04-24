import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Target, Zap } from 'lucide-react';

interface Lead {
  type: string;
  description: string;
  priority: string;
  confidence?: number;
  rationale?: string;
}

interface HITLApprovalDialogProps {
  lead: Lead | null;
  onApprove: () => void;
  onReject: () => void;
  loading?: boolean;
}

export const HITLApprovalDialog = ({ lead, onApprove, onReject, loading = false }: HITLApprovalDialogProps) => {
  if (!lead) return null;

  const priorityColors = {
    critical: 'text-red-400 bg-red-500/20 border-red-500/30',
    high: 'text-orange-400 bg-orange-500/20 border-orange-500/30',
    medium: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
    low: 'text-blue-400 bg-blue-500/20 border-blue-500/30',
  };

  const priorityColor = priorityColors[lead.priority as keyof typeof priorityColors] || priorityColors.medium;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={(e) => e.target === e.currentTarget && !loading && onReject()}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="glass-panel max-w-2xl w-full p-8 relative"
        >
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-purple-500/20 border border-purple-500/30">
              <AlertTriangle className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Human-In-The-Loop Approval Required</h2>
              <p className="text-sm text-gray-400 mt-1">Review investigative lead before execution</p>
            </div>
          </div>

          {/* Lead Details */}
          <div className="space-y-4 mb-6">
            {/* Lead Type */}
            <div>
              <label className="text-sm text-gray-400 uppercase tracking-wide">Lead Type</label>
              <div className="flex items-center gap-2 mt-1">
                <Target className="w-4 h-4 text-purple-400" />
                <p className="font-mono text-sm">{lead.type.replace(/_/g, ' ').toUpperCase()}</p>
              </div>
            </div>

            {/* Priority */}
            <div>
              <label className="text-sm text-gray-400 uppercase tracking-wide">Priority Level</label>
              <div className="mt-1">
                <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-sm font-semibold ${priorityColor}`}>
                  <Zap className="w-4 h-4" />
                  {lead.priority.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Confidence */}
            {lead.confidence !== undefined && (
              <div>
                <label className="text-sm text-gray-400 uppercase tracking-wide">Confidence Score</label>
                <div className="flex items-center gap-3 mt-1">
                  <div className="flex-1 bg-white/5 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${lead.confidence * 100}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut' }}
                      className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                    />
                  </div>
                  <span className="text-sm font-mono">{(lead.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}

            {/* Description */}
            <div>
              <label className="text-sm text-gray-400 uppercase tracking-wide">Description</label>
              <p className="mt-1 text-white">{lead.description}</p>
            </div>

            {/* Rationale */}
            {lead.rationale && (
              <div>
                <label className="text-sm text-gray-400 uppercase tracking-wide">Rationale</label>
                <p className="mt-1 text-gray-300 text-sm">{lead.rationale}</p>
              </div>
            )}
          </div>

          {/* Security Notice */}
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
            <p className="text-sm text-amber-200">
              <span className="font-semibold">Security Notice:</span> Approving this lead will execute forensic
              tools on the evidence. Ensure this action aligns with your investigation scope and authorization.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <motion.button
              onClick={onReject}
              disabled={loading}
              className={`
                flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl
                bg-red-500/20 border border-red-500/30 text-red-200
                hover:bg-red-500/30 transition-colors
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              whileHover={!loading ? { scale: 1.02 } : {}}
              whileTap={!loading ? { scale: 0.98 } : {}}
            >
              <XCircle className="w-5 h-5" />
              Reject & Stop Investigation
            </motion.button>

            <motion.button
              onClick={onApprove}
              disabled={loading}
              className={`
                flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl
                bg-green-500/20 border border-green-500/30 text-green-200
                hover:bg-green-500/30 transition-colors
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              whileHover={!loading ? { scale: 1.02 } : {}}
              whileTap={!loading ? { scale: 0.98 } : {}}
            >
              <CheckCircle className="w-5 h-5" />
              Approve & Continue Investigation
            </motion.button>
          </div>

          {/* Cryptographic Signature Notice */}
          <p className="mt-4 text-xs text-center text-gray-500">
            By approving, you cryptographically sign this execution path in the audit trail
          </p>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
