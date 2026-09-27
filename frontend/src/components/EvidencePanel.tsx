import React from "react";
import type { SafetyFinding } from "../types/screening";
import { BookOpen, ExternalLink, AlertTriangle, Info, Calendar } from "lucide-react";

export interface EvidencePanelProps {
  /** The finding whose evidence is being shown. */
  finding: SafetyFinding;
}

/**
 * Renders supporting evidence items for a finding, or an explicit
 * "evidence unavailable" state when `finding.evidenceUnavailable` is
 * true, or a "no evidence requested" state when
 * `finding.evidence.length === 0 && !evidenceUnavailable`. These three
 * states must never look the same to the user.
 *
 * @param props - {@link EvidencePanelProps}
 */
export const EvidencePanel: React.FC<EvidencePanelProps> = ({ finding }) => {
  // State 1: Evidence was requested but all external sources failed/timed out
  if (finding.evidenceUnavailable) {
    return (
      <div className="evidence-state-box evidence-unavailable" role="status">
        <div className="evidence-header-line">
          <AlertTriangle size={17} className="text-amber-600 shrink-0" aria-hidden="true" />
          <span className="font-semibold text-amber-900">External Evidence Unavailable</span>
        </div>
        <p className="text-xs text-amber-800 mt-1">
          External clinical literature lookup was attempted, but external evidence sources
          (e.g. OpenFDA, DailyMed) failed to respond within the configured timeout threshold.
          The deterministic rule finding remains clinically actionable based on established ruleset tables.
        </p>
      </div>
    );
  }

  // State 2: Evidence was not requested or empty without failure
  if (!finding.evidence || finding.evidence.length === 0) {
    return (
      <div className="evidence-state-box evidence-unrequested" role="status">
        <div className="evidence-header-line">
          <Info size={17} className="text-slate-500 shrink-0" aria-hidden="true" />
          <span className="font-medium text-slate-700">No External Evidence Requested</span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          This screening was processed using local validated interaction and contraindication rules.
          To query and attach live citations from OpenFDA / DailyMed, enable the "Include external literature" option before running review.
        </p>
      </div>
    );
  }

  // State 3: Evidence items available
  return (
    <div className="evidence-items-container" aria-label="Supporting Clinical Literature">
      <div className="evidence-section-header">
        <BookOpen size={16} className="text-indigo-600" aria-hidden="true" />
        <h5 className="font-semibold text-slate-800 text-sm">
          Clinical Citations & External Evidence ({finding.evidence.length})
        </h5>
      </div>

      <ul className="evidence-cards-list">
        {finding.evidence.map((item, idx) => (
          <li key={idx} className="evidence-citation-card">
            <div className="citation-header">
              <span className="citation-title font-semibold text-slate-800 text-sm">
                {item.title || `Clinical Evidence Entry #${idx + 1}`}
              </span>
              {item.source && (
                <span className="citation-source-tag">
                  {item.source}
                </span>
              )}
            </div>

            {item.summary && (
              <p className="citation-summary text-xs text-slate-700 mt-1">
                {item.summary}
              </p>
            )}

            {item.snippet && (
              <blockquote className="citation-snippet text-xs text-slate-600 border-l-2 border-indigo-300 pl-2.5 my-1.5 italic bg-slate-50/70 py-1">
                "{item.snippet}"
              </blockquote>
            )}

            <div className="citation-footer flex items-center justify-between mt-2 pt-1 border-t border-slate-100 text-xs">
              {item.publicationDate ? (
                <span className="flex items-center gap-1 text-slate-400">
                  <Calendar size={12} aria-hidden="true" />
                  {item.publicationDate}
                </span>
              ) : (
                <span />
              )}

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-link flex items-center gap-1 text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  <span>View Label / Guideline</span>
                  <ExternalLink size={12} aria-hidden="true" />
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
