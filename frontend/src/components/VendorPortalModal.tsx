import React from 'react';
import { Globe, ExternalLink, ShieldCheck, RefreshCw } from 'lucide-react';

export const VendorPortalModal: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col h-[700px]">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">Controlled Demo Vendor Portal</h2>
            <p className="text-xs text-slate-400">Sandbox environment used by Playwright & HTTP Browser tools</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="/portal"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-lg transition-colors flex items-center gap-1.5 font-medium"
          >
            <span>Open in New Tab</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Frame Preview */}
      <div className="flex-1 bg-slate-950 p-2">
        <iframe
          src="/portal"
          title="Vendor Portal Sandbox"
          className="w-full h-full rounded-lg border border-slate-800 bg-slate-900"
        />
      </div>
    </div>
  );
};
