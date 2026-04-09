import React, { useState } from 'react';
import {
  CheckCircle2, AlertTriangle, ChevronDown, ChevronRight,
  ShieldCheck, ShieldAlert, Zap, Target, BookOpen,
  Clipboard, Eye, EyeOff, Activity
} from 'lucide-react';
import Card from './design-system/Card';
import Badge from './design-system/Badge';

/**
 * ConfidenceBar — renders a colored progress bar for confidence score (0.0–1.0)
 */
const ConfidenceBar = ({ value }) => {
  const pct = Math.round((value || 0) * 100);
  const color =
    pct >= 80 ? 'bg-green-500' :
    pct >= 50 ? 'bg-yellow-500' :
    'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-semibold w-10 text-right">{pct}%</span>
    </div>
  );
};

/**
 * EvidenceList — collapsible list of evidence strings
 */
const EvidenceList = ({ evidence }) => {
  const [expanded, setExpanded] = useState(false);
  if (!evidence || evidence.length === 0) return null;

  const visible = expanded ? evidence : evidence.slice(0, 2);

  return (
    <div className="mt-2">
      <div className="space-y-1">
        {visible.map((e, i) => (
          <div
            key={i}
            className="font-mono text-xs bg-gray-100 text-gray-800 px-3 py-1.5 rounded border-l-2 border-green-400 break-all"
          >
            {e}
          </div>
        ))}
      </div>
      {evidence.length > 2 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
        >
          {expanded
            ? <><EyeOff className="w-3 h-3" />收起</>
            : <><Eye className="w-3 h-3" />展开全部 {evidence.length} 条证据</>}
        </button>
      )}
    </div>
  );
};

/**
 * VerifiedFindingCard — displays a single confirmed vulnerability
 */
const VerifiedFindingCard = ({ finding, index }) => {
  const [open, setOpen] = useState(true);

  const typeLabel = (finding?.vuln_type || 'unknown').toUpperCase().replace('_', ' ');

  return (
    <div className="border border-green-300 rounded-lg overflow-hidden shadow-sm">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-green-50 cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-green-600 flex-shrink-0" />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900">
                #{index + 1} {typeLabel}
              </span>
              <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-green-600 text-white">
                已验证
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5">{finding.target}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-xs text-gray-500 mb-0.5">置信度</div>
            <ConfidenceBar value={finding.confidence} />
          </div>
          {open
            ? <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
            : <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0" />}
        </div>
      </div>

      {open && (
        <div className="px-4 py-4 bg-white space-y-4">
          {/* Confidence (mobile) */}
          <div className="sm:hidden">
            <div className="text-xs text-gray-500 mb-1">置信度</div>
            <ConfidenceBar value={finding.confidence} />
          </div>

          {/* Evidence */}
          {finding.evidence && finding.evidence.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-sm font-medium text-gray-700 mb-1">
                <Clipboard className="w-4 h-4" />
                证据
              </div>
              <EvidenceList evidence={finding.evidence} />
            </div>
          )}

          {/* Exploit proof */}
          {finding.exploit_proof && (
            <div>
              <div className="flex items-center gap-1 text-sm font-medium text-gray-700 mb-1">
                <Zap className="w-4 h-4" />
                利用证明
              </div>
              <div className="font-mono text-xs bg-gray-900 text-green-400 px-3 py-2 rounded whitespace-pre-wrap break-all">
                {finding.exploit_proof}
              </div>
            </div>
          )}

          {/* Suggested next */}
          {finding.suggested_next && (
            <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <BookOpen className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-semibold text-blue-700 mb-0.5">建议后续步骤</div>
                <div className="text-sm text-blue-900">{finding.suggested_next}</div>
              </div>
            </div>
          )}

          {/* Raw findings count */}
          {finding.raw_findings && finding.raw_findings.length > 0 && (
            <div className="text-xs text-gray-400">
              原始检测结果: {finding.raw_findings.length} 条
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * UnverifiedFindingCard — displays a suspected / unconfirmed finding
 */
const UnverifiedFindingCard = ({ finding, index }) => {
  const [open, setOpen] = useState(false);

  const typeLabel = (() => {
    const t = finding.vuln_type || finding.type || 'unknown';
    return t.toUpperCase().replace('_', ' ');
  })();

  const reason = finding.error
    ? `验证错误: ${finding.error}`
    : finding.description || '未能通过实际利用验证，可能为误报或需要人工确认。';

  return (
    <div className="border border-yellow-300 rounded-lg overflow-hidden">
      <div
        className="flex items-center justify-between px-4 py-3 bg-yellow-50 cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-yellow-600 flex-shrink-0" />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900">
                #{index + 1} {typeLabel}
              </span>
              <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-yellow-500 text-white">
                疑似
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {finding.target || '未知目标'}
            </div>
          </div>
        </div>
        {open
          ? <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
          : <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0" />}
      </div>

      {open && (
        <div className="px-4 py-3 bg-white">
          <p className="text-sm text-gray-700">{reason}</p>
          {finding.confidence !== undefined && (
            <div className="mt-3">
              <div className="text-xs text-gray-500 mb-1">置信度</div>
              <ConfidenceBar value={finding.confidence} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ValidationResults — main component
 *
 * Props:
 *   verifiedFindings   Array<ValidationResult>  — confirmed vulns
 *   unverifiedFindings Array<any>               — suspected / failed
 */
const ValidationResults = ({ verifiedFindings = [], unverifiedFindings = [] }) => {
  const [activeTab, setActiveTab] = useState('verified');

  const hasVerified = verifiedFindings.length > 0;
  const hasUnverified = unverifiedFindings.length > 0;
  const hasAny = hasVerified || hasUnverified;

  if (!hasAny) {
    return (
      <div className="flex items-center justify-center py-10 text-gray-400">
        <Activity className="w-5 h-5 mr-2" />
        <span>暂无验证结果</span>
      </div>
    );
  }

  return (
    <div>
      {/* Summary row */}
      <div className="flex flex-wrap gap-4 mb-5">
        <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <div>
            <div className="text-2xl font-bold text-green-700 leading-none">{verifiedFindings.length}</div>
            <div className="text-xs text-green-600 mt-0.5">已验证漏洞</div>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-yellow-600" />
          <div>
            <div className="text-2xl font-bold text-yellow-700 leading-none">{unverifiedFindings.length}</div>
            <div className="text-xs text-yellow-600 mt-0.5">疑似漏洞</div>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg">
          <Target className="w-5 h-5 text-gray-500" />
          <div>
            <div className="text-2xl font-bold text-gray-700 leading-none">
              {verifiedFindings.length + unverifiedFindings.length}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">总计</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => setActiveTab('verified')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'verified'
              ? 'border-green-500 text-green-700'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-4 h-4" />
            已验证 ({verifiedFindings.length})
          </span>
        </button>
        <button
          onClick={() => setActiveTab('unverified')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'unverified'
              ? 'border-yellow-500 text-yellow-700'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <span className="flex items-center gap-1">
            <ShieldAlert className="w-4 h-4" />
            疑似 ({unverifiedFindings.length})
          </span>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {activeTab === 'verified' && (
          hasVerified
            ? verifiedFindings.map((f, i) => (
                <VerifiedFindingCard key={i} finding={f} index={i} />
              ))
            : <p className="text-sm text-gray-400 py-4 text-center">没有经过验证的漏洞。</p>
        )}
        {activeTab === 'unverified' && (
          hasUnverified
            ? unverifiedFindings.map((f, i) => (
                <UnverifiedFindingCard key={i} finding={f} index={i} />
              ))
            : <p className="text-sm text-gray-400 py-4 text-center">没有疑似漏洞。</p>
        )}
      </div>
    </div>
  );
};

export default ValidationResults;
