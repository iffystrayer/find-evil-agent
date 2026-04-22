import { BentoGrid, BentoTile } from '../layout/BentoGrid';
import { DefaultAuditTrail } from './AuditTrail';
import { ObfuscationAlert } from './ObfuscationAlert';
import { AnalysisForm } from './AnalysisForm';
import { BarChart3, Activity, Clock, Shield } from 'lucide-react';

export const Dashboard = () => {
  const handleAnalysisSubmit = (data: { incident: string; goal: string; format: string }) => {
    console.log('Analysis submitted:', data);
    // TODO: Connect to backend API
  };

  return (
    <BentoGrid columns={3}>
      {/* Quick Stats */}
      <BentoTile>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Total Analyses</p>
            <p className="text-3xl font-bold mt-1">247</p>
          </div>
          <BarChart3 className="w-10 h-10 text-purple-400" />
        </div>
      </BentoTile>

      <BentoTile>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Active Investigations</p>
            <p className="text-3xl font-bold mt-1">3</p>
          </div>
          <Activity className="w-10 h-10 text-blue-400" />
        </div>
      </BentoTile>

      <BentoTile>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Avg. Time</p>
            <p className="text-3xl font-bold mt-1">47s</p>
          </div>
          <Clock className="w-10 h-10 text-green-400" />
        </div>
      </BentoTile>

      {/* Analysis Form */}
      <BentoTile span={2} tall>
        <h3 className="text-xl font-semibold mb-4">New Analysis</h3>
        <AnalysisForm onSubmit={handleAnalysisSubmit} />
      </BentoTile>

      {/* Audit Trail */}
      <BentoTile tall>
        <DefaultAuditTrail />
      </BentoTile>

      {/* Obfuscation Alert */}
      <BentoTile span={2}>
        <ObfuscationAlert
          detected={true}
          confidence={0.92}
          details="High entropy detected in PowerShell script - possible obfuscation techniques identified"
        />
      </BentoTile>

      {/* Security Status */}
      <BentoTile>
        <div className="flex items-center gap-3">
          <Shield className="w-12 h-12 text-green-400" />
          <div>
            <p className="font-semibold">Sandbox Active</p>
            <p className="text-sm text-gray-400">All tools isolated</p>
          </div>
        </div>
      </BentoTile>
    </BentoGrid>
  );
};
