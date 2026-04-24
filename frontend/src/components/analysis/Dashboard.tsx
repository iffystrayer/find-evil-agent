import { BentoGrid, BentoTile } from '../layout/BentoGrid';
import { DefaultAuditTrail } from './AuditTrail';
import { ObfuscationAlert } from './ObfuscationAlert';
import { AnalysisForm } from './AnalysisForm';
import { BarChart3, Activity, Clock, Shield } from 'lucide-react';
import { useState } from 'react';
import { api } from '../../api/client';

export const Dashboard = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalysisSubmit = async (data: { incident: string; goal: string; format: string }) => {
    console.log('Analysis submitted:', data);
    setLoading(true);
    setError(null);

    try {
      const response = await api.analyze({
        incident: data.incident,
        goal: data.goal,
        format: data.format as 'html' | 'markdown'
      });

      console.log('Analysis response:', response);
      setResult(response);

      if (response.success) {
        alert(`Analysis complete!\nSession: ${response.session_id}\nFindings: ${response.findings?.length || 0}`);
      } else {
        setError(response.error || 'Analysis failed');
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
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
        <AnalysisForm onSubmit={handleAnalysisSubmit} loading={loading} />
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-200">
            <p className="text-sm font-semibold">Error:</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
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
