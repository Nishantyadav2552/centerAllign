import React from 'react';
import { 
  ShieldCheck, 
  CheckCircle, 
  XCircle, 
  FileText, 
  Database, 
  ExternalLink,
  Hash,
  Scale
} from 'lucide-react';
import { VerificationRecord } from '../types';

interface EvidenceVerificationPanelProps {
  verifications: VerificationRecord[];
}

export const EvidenceVerificationPanel: React.FC<EvidenceVerificationPanelProps> = ({ verifications }) => {
  if (!verifications || verifications.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-center text-xs text-slate-500">
        <Scale className="w-6 h-6 text-slate-600 mx-auto mb-2" />
        Independent read-back verification will execute automatically once records are created.
      </div>
    );
  }

  const latestVerification = verifications[verifications.length - 1];
  let fieldResults: Record<string, { expected: any; actual: any; match: boolean }> = {};
  let evidence: any = {};

  try {
    if (latestVerification.field_results_json) {
      fieldResults = JSON.parse(latestVerification.field_results_json);
    }
    if (latestVerification.evidence_json) {
      evidence = JSON.parse(latestVerification.evidence_json);
    }
  } catch (e) {
    // Parse fallback
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm my-4">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Independent Verification & Evidence Audit</h3>
        </div>
        <div className="flex items-center gap-2">
          {latestVerification.verified ? (
            <span className="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
              <CheckCircle className="w-3.5 h-3.5" />
              100% Field Parity
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1.5">
              <XCircle className="w-3.5 h-3.5" />
              Discrepancy Found
            </span>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Verification Summary */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs flex items-center justify-between">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider font-semibold">VERIFICATION METHOD:</span>
            <span className="text-slate-200 font-medium">Independent SQLite Read-Back & Direct Value Assertion</span>
          </div>
          <div className="text-right">
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider font-semibold">TARGET RECORD:</span>
            <span className="text-blue-400 font-mono font-semibold">{latestVerification.target_id}</span>
          </div>
        </div>

        {/* Field-by-Field Parity Table */}
        <div>
          <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-blue-400" />
            <span>Extracted Source Values vs Persisted Destination Database Record</span>
          </div>

          <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950/50">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Field</th>
                  <th className="py-2.5 px-3">Extracted Source (PDF)</th>
                  <th className="py-2.5 px-3">Persisted SQLite Record</th>
                  <th className="py-2.5 px-3 text-right">Parity Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {Object.entries(fieldResults).map(([fieldName, res]) => (
                  <tr key={fieldName} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2 px-3 font-semibold text-slate-300 font-sans">
                      {fieldName}
                    </td>
                    <td className="py-2 px-3 text-slate-300">
                      {String(res.expected)}
                    </td>
                    <td className="py-2 px-3 text-white font-bold">
                      {String(res.actual)}
                    </td>
                    <td className="py-2 px-3 text-right">
                      {res.match ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-semibold">
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Match</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 text-xs font-semibold">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Mismatch</span>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Provenance Evidence */}
        {evidence && (
          <div className="bg-blue-950/20 border border-blue-900/30 p-3 rounded-lg text-xs space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-blue-300 font-semibold flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" />
                Source Document Reference: {evidence.source_document_id || 'acme_invoice_latest.pdf'}
              </span>
              <a
                href={`/portal/download/${evidence.source_document_id || 'acme_invoice_latest.pdf'}`}
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1 font-mono text-[10px]"
              >
                <span>View Source PDF</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Cryptographically verified synthetic PDF artifact • Extracted via PyMuPDF with regex bounding anchors.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
