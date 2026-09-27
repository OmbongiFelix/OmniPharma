import React from "react";
import type { Recommendation } from "../types/screening";
import { CheckCircle, XCircle, Package, ShieldCheck, AlertOctagon, HelpCircle } from "lucide-react";

export interface AlternativeTableProps {
  /** Full list of candidate recommendations, both included and excluded. */
  recommendations: Recommendation[];
  /** Target medication being considered for replacement. */
  targetMedication?: string;
  /** Optional callback when a candidate is selected for addition to the screening regimen. */
  onSelectCandidate?: (drugName: string) => void;
}

/**
 * Renders {@link Recommendation} candidates. Every row is labeled
 * "candidate for pharmacist review," never "prescription" or
 * "recommended dose." Excluded candidates render in a visually distinct
 * (not hidden) section with their `excludedReason`.
 *
 * @param props - {@link AlternativeTableProps}
 */
export const AlternativeTable: React.FC<AlternativeTableProps> = ({
  recommendations,
  targetMedication,
  onSelectCandidate,
}) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="empty-sublist">
        <HelpCircle size={18} className="text-slate-400" aria-hidden="true" />
        <span>No alternative candidates evaluated yet for this medication.</span>
      </div>
    );
  }

  const included = recommendations.filter((r) => !r.excluded);
  const excluded = recommendations.filter((r) => r.excluded);

  return (
    <div className="alternative-table-container" aria-label="Alternative Medicines Analysis">
      {/* Notice header stating legal / CDS clinical role */}
      <div className="alt-cds-notice">
        <ShieldCheck size={16} className="text-teal-700 shrink-0" aria-hidden="true" />
        <span className="text-xs text-teal-900">
          <strong>Clinical Decision Support Notice:</strong> Every alternative listed below is a{" "}
          <span className="underline decoration-teal-600 font-semibold">candidate for pharmacist review</span>.
          Alternatives are safety-screened against current patient comorbidities and allergies, but do not constitute an automated prescription or recommended dose.
        </span>
      </div>

      {/* INCLUDED CANDIDATES SECTION */}
      <div className="alt-section">
        <div className="alt-section-heading">
          <CheckCircle size={18} className="text-emerald-600" aria-hidden="true" />
          <h4 className="font-semibold text-slate-800 text-sm">
            Viable Candidates {targetMedication ? `for ${targetMedication}` : ""} ({included.length})
          </h4>
        </div>

        {included.length === 0 ? (
          <div className="empty-sublist text-xs text-slate-500">
            No candidates passed all safety and formulary checks without contraindications.
          </div>
        ) : (
          <div className="table-responsive-wrapper">
            <table className="candidate-table" aria-label="Viable Alternative Candidates">
              <thead>
                <tr>
                  <th scope="col">Candidate Medicine</th>
                  <th scope="col">Clinical Role</th>
                  <th scope="col">Clinical Justification</th>
                  <th scope="col">Stock & Availability</th>
                  {onSelectCandidate && <th scope="col">Action</th>}
                </tr>
              </thead>
              <tbody>
                {included.map((cand, idx) => (
                  <tr key={`inc-${idx}`} className="row-candidate-included">
                    <td className="font-semibold text-slate-900">
                      <div className="candidate-name-cell">
                        <span className="candidate-name">{cand.drugName}</span>
                      </div>
                    </td>
                    <td>
                      <span className="candidate-review-badge">
                        candidate for pharmacist review
                      </span>
                    </td>
                    <td className="text-xs text-slate-700">
                      {cand.includedReason || "Clinically compatible alternative with no active contraindications detected."}
                    </td>
                    <td>
                      <span className="flex items-center gap-1.5 text-xs text-slate-700">
                        <Package size={14} className="text-emerald-600" aria-hidden="true" />
                        {cand.availability || "In stock / Available"}
                      </span>
                    </td>
                    {onSelectCandidate && (
                      <td>
                        <button
                          type="button"
                          className="action-btn-sm"
                          onClick={() => onSelectCandidate(cand.drugName)}
                        >
                          Select for Review
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* EXCLUDED CANDIDATES SECTION (Always shown, never hidden) */}
      <div className="alt-section mt-6">
        <div className="alt-section-heading">
          <AlertOctagon size={18} className="text-rose-600" aria-hidden="true" />
          <h4 className="font-semibold text-slate-800 text-sm">
            Disqualified / Excluded Candidates ({excluded.length})
          </h4>
        </div>
        <p className="text-xs text-slate-500 mb-2">
          The following candidates were evaluated from the catalogue but disqualified based on patient-specific contraindications or interaction risks:
        </p>

        {excluded.length === 0 ? (
          <div className="empty-sublist text-xs text-slate-500">
            No candidate alternatives required disqualification.
          </div>
        ) : (
          <div className="table-responsive-wrapper">
            <table className="candidate-table table-excluded" aria-label="Excluded Candidate Medicines">
              <thead>
                <tr>
                  <th scope="col">Disqualified Candidate</th>
                  <th scope="col">Clinical Role</th>
                  <th scope="col">Specific Exclusion Reason (Contraindication / Rule)</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {excluded.map((cand, idx) => (
                  <tr key={`exc-${idx}`} className="row-candidate-excluded">
                    <td className="font-medium text-slate-800 line-through opacity-80">
                      {cand.drugName}
                    </td>
                    <td>
                      <span className="candidate-excluded-badge">
                        candidate for pharmacist review (disqualified)
                      </span>
                    </td>
                    <td className="text-xs font-medium text-rose-800">
                      <div className="flex items-start gap-1.5">
                        <XCircle size={15} className="text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
                        <span>{cand.excludedReason || "Contraindicated for current patient clinical profile."}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-xs font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        Excluded
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
