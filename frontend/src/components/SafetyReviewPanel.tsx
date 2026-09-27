import React, { useState, useEffect, useRef } from "react";
import { useScreening } from "../hooks/useScreening";
import type { SafetyFinding, Severity } from "../types/screening";
import { FindingCard } from "./FindingCard";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";
import { AuditMeta } from "./AuditMeta";
import {
  Play,
  CheckCircle,
  AlertTriangle,
  Ban,
  HelpCircle,
  Sparkles,
  FileText,
  ShieldCheck,
} from "lucide-react";

export interface SafetyReviewPanelProps {
  /** Patient ID being reviewed. */
  patientId: number;
  /** Exact medicine list being evaluated; changing this list invalidates any previous result. */
  medicationNames: string[];
  /** Optional callback when user clicks to find alternatives for an affected drug. */
  onFindAlternatives?: (medicationName: string) => void;
}

const SEVERITY_ORDER: Record<Severity, number> = {
  CONTRAINDICATED: 1,
  HIGH: 2,
  MODERATE: 3,
  LOW: 4,
  INFO: 5,
};

/**
 * Owns the "Run Safety Review" action and renders the resulting
 * findings grouped by severity (CONTRAINDICATED and HIGH first). Uses
 * {@link useScreening} for the mutation and shows {@link LoadingState}
 * while a review is in flight and {@link ErrorState} on failure,
 * including a distinct message for `status: "INCOMPLETE_CONTEXT"`
 * versus a network/API error.
 *
 * @param props.patientId - Patient being reviewed.
 * @param props.medicationNames - Exact medicine list being evaluated;
 *   changing this list invalidates any previous result (see Section 6).
 */
export const SafetyReviewPanel: React.FC<SafetyReviewPanelProps> = ({
  patientId,
  medicationNames,
  onFindAlternatives,
}) => {
  const { runReview, result, isLoading, error, clearResult } = useScreening();
  const [includeEvidence, setIncludeEvidence] = useState<boolean>(false);

  // Track previous inputs to invalidate stale results
  const prevInputRef = useRef<{ patientId: number; meds: string[] }>({
    patientId,
    meds: medicationNames,
  });

  useEffect(() => {
    const prev = prevInputRef.current;
    const medsChanged =
      prev.meds.length !== medicationNames.length ||
      prev.meds.some((m, idx) => m !== medicationNames[idx]);

    if (prev.patientId !== patientId || medsChanged) {
      clearResult();
      prevInputRef.current = { patientId, meds: medicationNames };
    }
  }, [patientId, medicationNames, clearResult]);

  const handleRun = async () => {
    if (!medicationNames || medicationNames.length === 0) return;
    await runReview({
      patientId,
      medications: medicationNames,
      includeEvidence,
    });
  };

  // Group findings by severity (CONTRAINDICATED and HIGH first)
  const sortedFindings: SafetyFinding[] = result?.findings
    ? [...result.findings].sort(
        (a, b) => (SEVERITY_ORDER[a.severity] || 99) - (SEVERITY_ORDER[b.severity] || 99)
      )
    : [];

  const isIncompleteContext = result?.status === "INCOMPLETE_CONTEXT";

  return (
    <div className="safety-review-panel" aria-label="Medication Safety Review Engine">
      {/* Top action control bar */}
      <div className="review-action-bar">
        <div className="action-bar-left">
          <button
            type="button"
            className="run-review-btn"
            onClick={handleRun}
            disabled={isLoading || medicationNames.length === 0}
          >
            <Play size={16} className="fill-current" aria-hidden="true" />
            <span>Run Safety Review</span>
          </button>

          <label className="include-evidence-toggle">
            <input
              type="checkbox"
              checked={includeEvidence}
              onChange={(e) => setIncludeEvidence(e.target.checked)}
              disabled={isLoading}
            />
            <span className="toggle-text">Query external clinical evidence</span>
          </label>
        </div>

        <div className="action-bar-right">
          <span className="reviewed-meds-count">
            Evaluating {medicationNames.length} medication{medicationNames.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="panel-loading-wrapper">
          <LoadingState
            size="lg"
            message={`Screening ${medicationNames.length} medications against patient profile and interaction rules...`}
          />
        </div>
      )}

      {/* Error state: Network or 4xx/5xx API failures */}
      {!isLoading && error && (
        <div className="panel-error-wrapper">
          <ErrorState
            message="Medication safety screening failed to complete."
            detail={error.message}
            retry={handleRun}
          />
        </div>
      )}

      {/* INCOMPLETE_CONTEXT State: distinct warning banner per specs */}
      {!isLoading && isIncompleteContext && (
        <div className="incomplete-context-banner" role="alert">
          <div className="banner-header">
            <AlertTriangle size={20} className="text-amber-700" aria-hidden="true" />
            <h4 className="banner-title text-amber-950 font-bold">
              Incomplete Clinical Context (INCOMPLETE_CONTEXT)
            </h4>
          </div>
          <p className="banner-desc text-amber-900 text-sm mt-1">
            The safety review could not rule out potential contraindications because essential patient clinical parameters
            (such as organ function or specific enzyme levels) are marked as <strong>not recorded</strong>.
            Please exercise heightened clinical vigilance and confirm laboratory values before dispensing.
          </p>
        </div>
      )}

      {/* Results view */}
      {!isLoading && result && (
        <div className="screening-results-wrapper">
          {/* Overall Status Banner */}
          <div
            className={`status-header-banner banner-status-${result.status.toLowerCase()}`}
            role="status"
          >
            <div className="flex items-center gap-3">
              {result.status === "CLEAR" && (
                <CheckCircle size={22} className="text-emerald-700" aria-hidden="true" />
              )}
              {result.status === "REVIEW_REQUIRED" && (
                <AlertTriangle size={22} className="text-amber-700" aria-hidden="true" />
              )}
              {result.status === "CONTRAINDICATED" && (
                <Ban size={22} className="text-rose-700" aria-hidden="true" />
              )}
              {result.status === "INCOMPLETE_CONTEXT" && (
                <HelpCircle size={22} className="text-amber-700" aria-hidden="true" />
              )}
              <div>
                <span className="overall-status-label">Overall Safety Evaluation:</span>
                <span className="overall-status-badge">{result.status.replace(/_/g, " ")}</span>
              </div>
            </div>

            <div className="findings-summary-counts">
              <span className="count-badge">{result.findings.length} findings flagged</span>
            </div>
          </div>

          {/* AI Pharmacist Narrative Explanation if present */}
          {result.explanation && (
            <div className="pharmacist-explanation-card">
              <div className="explanation-header">
                <Sparkles size={17} className="text-indigo-600" aria-hidden="true" />
                <h5 className="font-semibold text-indigo-950 text-sm">
                  Clinical Narrative & Pharmacist Synthesis
                </h5>
              </div>
              <p className="explanation-text text-sm text-slate-800 leading-relaxed mt-1">
                {result.explanation}
              </p>
            </div>
          )}

          {/* Findings List grouped by severity */}
          {sortedFindings.length === 0 ? (
            <div className="no-findings-box">
              <ShieldCheck size={36} className="text-emerald-600" aria-hidden="true" />
              <h4 className="font-semibold text-emerald-950 text-base mt-2">
                No Safety Findings Flagged
              </h4>
              <p className="text-xs text-emerald-800 mt-1 max-w-md text-center">
                All {medicationNames.length} evaluated medicines passed deterministic checks for drug-drug interactions,
                pregnancy contraindications, organ impairment, and known allergies with the current ruleset.
              </p>
            </div>
          ) : (
            <div className="findings-list-container">
              <div className="findings-header-row">
                <h4 className="font-bold text-slate-800 text-sm">
                  Clinical Findings ({sortedFindings.length}) — Sorted by Priority
                </h4>
                <span className="text-xs text-slate-500">
                  Contraindicated & High Risk findings listed first
                </span>
              </div>

              <div className="findings-cards-stack">
                {sortedFindings.map((finding, idx) => (
                  <FindingCard
                    key={`${finding.ruleId}-${idx}`}
                    finding={finding}
                    expanded={finding.severity === "CONTRAINDICATED" || finding.severity === "HIGH"}
                    onFindAlternatives={onFindAlternatives}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Audit Metadata Footer */}
          <div className="panel-audit-wrapper">
            <AuditMeta
              rulesetVersion={result.rulesetVersion}
              catalogueVersion={result.catalogueVersion}
              requestId={result.requestId}
            />
          </div>
        </div>
      )}

      {/* Initial state before review is triggered */}
      {!isLoading && !result && !error && (
        <div className="panel-unrun-state">
          <FileText size={32} className="text-slate-400" aria-hidden="true" />
          <h4 className="font-medium text-slate-700 text-sm mt-2">
            Ready to Screen {medicationNames.length} Medication{medicationNames.length !== 1 ? "s" : ""}
          </h4>
          <p className="text-xs text-slate-500 mt-1 max-w-md text-center">
            Click "Run Safety Review" above to evaluate drug-drug interactions, pregnancy warnings, renal/hepatic/G6PD contraindications, and allergy cross-reactivities.
          </p>
        </div>
      )}
    </div>
  );
};
