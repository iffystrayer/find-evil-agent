import { motion } from 'framer-motion';
import { AlertTriangle, Eye } from 'lucide-react';

interface ObfuscationAlertProps {
  detected: boolean;
  confidence?: number;
  details?: string;
}

export const ObfuscationAlert = ({
  detected,
  confidence = 0.85,
  details = 'High entropy detected in code blocks'
}: ObfuscationAlertProps) => {
  if (!detected) return null;

  return (
    <motion.div
      className="alert-obfuscation p-4"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start gap-3">
        {/* Flashing Icon */}
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <AlertTriangle className="w-6 h-6 text-amber-400" />
        </motion.div>

        <div className="flex-1">
          <h4 className="font-semibold text-amber-400 flex items-center gap-2">
            Obfuscation Detected
            <span className="text-xs bg-amber-500/30 px-2 py-0.5 rounded">
              {Math.round(confidence * 100)}% confidence
            </span>
          </h4>

          <p className="text-sm text-gray-300 mt-1">{details}</p>

          <div className="mt-3 flex gap-2">
            <button className="glass-button text-xs py-2">
              <Eye className="w-3 h-3 inline mr-1" />
              View Analysis
            </button>
            <button className="glass-button text-xs py-2">
              Flag for Review
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
