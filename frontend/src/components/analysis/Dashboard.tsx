import { BentoGrid, BentoTile } from '../layout/BentoGrid';
import { DefaultAuditTrail } from './AuditTrail';
import { ObfuscationAlert } from './ObfuscationAlert';
import { AnalysisForm } from './AnalysisForm';
import { HITLApprovalDialog } from './HITLApprovalDialog';
import { BarChart3, Activity, Clock, Shield } from 'lucide-react';
import { useState } from 'react';
import { api } from '../../api/client';
import type { InvestigationResponse, Lead } from '../../api/client';

export const Dashboard = () => {
  const [loading, setLoading] = useState(false);
  const [_result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const [currentLead, setCurrentLead] = useState<Lead | null>(null);

  const handleAnalysisSubmit = async (data: {
    incident: string;
    goal: string;
    format: string;
    mode: string;
    maxIterations?: number
  }) => {
    console.log('Analysis submitted:', data);
    setLoading(true);
    setError(null);
    setAwaitingApproval(false);
    setCurrentLead(null);

    try {
      if (data.mode === 'investigative') {
        // Investigative mode with HITL support
        const response: InvestigationResponse = await api.investigate({
          incident: data.incident,
          goal: data.goal,
          format: data.format as 'html' | 'markdown',
          max_iterations: data.maxIterations || 5
        });

        console.log('Investigation response:', response);
        setResult(response);
        setSessionId(response.session_id || null);

        // Check if HITL approval is needed
        if (response.stopping_reason === 'Waiting for Human Approval') {
          setAwaitingApproval(true);
          // Get the last lead from investigation chain as the pending lead
          const pendingLead = response.investigation_chain?.[response.investigation_chain.length - 1];
          setCurrentLead(pendingLead || null);
        } else if (response.success) {
          alert(`Investigation complete!\nSession: ${response.session_id}\nIterations: ${response.iterations?.length || 0}\nFindings: ${response.all_findings?.length || 0}`);
        } else {
          setError(response.error || 'Investigation failed');
        }
      } else {
        // Single analysis mode
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
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!sessionId) return;

    setLoading(true);
    setAwaitingApproval(false);
    setCurrentLead(null);

    try {
      const response: InvestigationResponse = await api.resume(sessionId, true);
      console.log('Resume response (approved):', response);
      setResult(response);

      // Check if another HITL approval is needed
      if (response.stopping_reason === 'Waiting for Human Approval') {
        setAwaitingApproval(true);
        const pendingLead = response.investigation_chain?.[response.investigation_chain.length - 1];
        setCurrentLead(pendingLead || null);
      } else if (response.success) {
        alert(`Investigation complete!\nSession: ${response.session_id}\nIterations: ${response.iterations?.length || 0}\nFindings: ${response.all_findings?.length || 0}`);
      } else {
        setError(response.error || 'Investigation failed');
      }
    } catch (err: any) {
      console.error('Resume error:', err);
      setError(err.message || 'Failed to resume investigation');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!sessionId) return;

    setLoading(true);
    setAwaitingApproval(false);
    setCurrentLead(null);

    try {
      const response: InvestigationResponse = await api.resume(sessionId, false);
      console.log('Resume response (rejected):', response);
      setResult(response);

      alert('Investigation stopped by analyst decision');
    } catch (err: any) {
      console.error('Resume error:', err);
      setError(err.message || 'Failed to stop investigation');
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

      {/* HITL Approval Dialog */}
      {awaitingApproval && currentLead && (
        <HITLApprovalDialog
          lead={currentLead}
          onApprove={handleApprove}
          onReject={handleReject}
          loading={loading}
        />
      )}
    </BentoGrid>
  );
};
