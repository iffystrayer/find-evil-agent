import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { NavRail } from './NavRail';
import { SandboxStatus } from '../shared/SandboxStatus';

interface GlassShellProps {
  children: ReactNode;
}

export const GlassShell = ({ children }: GlassShellProps) => {
  return (
    <div className="min-h-screen flex">
      {/* Nav Rail - Left Sidebar */}
      <NavRail />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Header with Sandbox Status */}
        <motion.header
          className="glass-panel m-4 mb-2 p-4 flex items-center justify-between"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Find Evil Agent
            </h1>
            <span className="text-sm text-gray-400">Autonomous Forensic Analysis</span>
          </div>

          <SandboxStatus />
        </motion.header>

        {/* Main Content */}
        <main className="flex-1 p-4 pt-2">
          {children}
        </main>

        {/* Footer */}
        <motion.footer
          className="glass-panel m-4 mt-2 p-3 text-center text-sm text-gray-400"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <p>Powered by LangGraph • SIFT Toolkit • Multi-Agent Orchestration</p>
        </motion.footer>
      </div>
    </div>
  );
};
