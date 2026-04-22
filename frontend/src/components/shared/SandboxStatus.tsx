import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

export const SandboxStatus = () => {
  return (
    <motion.div
      className="sandbox-indicator"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      {/* Glowing Green Dot */}
      <div className="sandbox-dot" />

      <Shield className="w-4 h-4 text-green-400" />

      <span className="text-green-400 font-semibold">
        Analysis Environment: ISOLATED
      </span>
    </motion.div>
  );
};
