import React, { useState, useEffect } from "react";
import type { PatientContext } from "../types/patient";
import type { PageId } from "../components/AppShell";
import { useRecommendations } from "../hooks/useRecommendations";
import { AlternativeTable } from "../components/AlternativeTable";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import { Sparkles, Search, Pill, ArrowLeft, ShieldAlert } from "lucide-react";

export interface AlternativesPageProps {
  /** Active patient context. */
  patient: PatientContext | null;
  /** Currently selected target medication to evaluate alternatives for. */
  targetMedication: string;
  /** Callback to update target medication. */
  onSelectTargetMedication: (med: string) => void;
  /** Navigation callback to switch screens. */
  onNavigate: (page: PageId) => void;
  /** Callback to replace or add candidate to active screening regimen. */
  onAdoptAlternative: (newMed: string, replaceOldMed?: string) => void;
}

/**
 * Alternative Medicines Screen:
 * Generates safety-filtered alternative candidates from the local formulary
 * catalogue for a target medicine, clearly displaying clinical justifications
 * for viable candidates and explicit exclusion reasons for disqualified options.
 *
 * @param props - {@link AlternativesPageProps}
 */
export const AlternativesPage: React.FC<AlternativesPageProps> = ({
  patient,
  targetMedication,
  onSelectTargetMedication,
  onNavigate,
  onAdoptAlternative,
}) => {
  const [inputMed, setInputMed] = useState<string>(targetMedication || "");
  const [indication, setIndication] = useState<string>("");

  const { fetchRecommendations, recommendations, isLoading, error } = useRecommendations();

  useEffect(() => {
    if (targetMedication && targetMedication !== inputMed) {
      setInputMed(targetMedication);
      if (patient) {
        fetchRecommendations({
          patientId: patient.id,
          targetMedication: targetMedication,
          indication: indication.trim() || "a",
        });
      }
    }
  }, [targetMedication, patient, fetchRecommendations]);

  const handleSearchAlternatives = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = inputMed.trim();
    if (!trimmed || !patient) return;
    onSelectTargetMedication(trimmed);
    fetchRecommendations({
      patientId: patient.id,
      targetMedication: trimmed,
      indication: indication.trim() || "a",
    });
  };

  const handleAdopt = (candidateName: string) => {
    onAdoptAlternative(candidateName, targetMedication);
    onNavigate("safety-review");
  };

  if (!patient) {
    return (
      <div className="page-empty-selection">
        <ShieldAlert size={40} className="text-slate-400" aria-hidden="true" />
        <h3 className="text-lg font-bold text-slate-700 mt-3">Select a Patient to Evaluate Alternatives</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md text-center">
          Alternative medicine recommendations require the patient's comorbidity and allergy context for safety filtering.
        </p>
      </div>
    );
  }

  return (
    <div className="alternatives-page-container" aria-label="Alternative Medicines Analysis">
      {/* Top Header & Breadcrumb */}
      <div className="alternatives-header flex items-center justify-between">
        <div>
          <button
            type="button"
            className="back-nav-btn mb-1 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800"
            onClick={() => onNavigate("safety-review")}
          >
            <ArrowLeft size={13} aria-hidden="true" />
            <span>Return to Safety Review</span>
          </button>
          <h2 className="text-xl font-bold text-slate-900">Alternative Medicine Evaluation</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Formulary substitutions safety-screened against{" "}
            <strong>{patient.name}</strong>'s specific medical profile.
          </p>
        </div>
      </div>

      {/* Target Drug & Indication Query Form */}
      <section className="alt-query-card mt-4 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
        <form onSubmit={handleSearchAlternatives} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="target-med-input" className="block text-xs font-semibold text-slate-700 mb-1">
                Target Medicine Being Reconsidered / Replaced:
              </label>
              <div className="relative">
                <Pill size={16} className="absolute left-3 top-3 text-teal-600" aria-hidden="true" />
                <input
                  id="target-med-input"
                  type="text"
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="e.g. ibuprofen, warfarin, metformin..."
                  value={inputMed}
                  onChange={(e) => setInputMed(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="indication-input" className="block text-xs font-semibold text-slate-700 mb-1">
                Clinical Indication (Optional narrowing):
              </label>
              <input
                id="indication-input"
                type="text"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="e.g. pain relief, anticoagulation, glucose control..."
                value={indication}
                onChange={(e) => setIndication(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-medium text-slate-600">Quick target presets:</span>
              {["ibuprofen", "warfarin", "metformin", "lisinopril"].map((t) => (
                <button
                  key={t}
                  type="button"
                  className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs"
                  onClick={() => {
                    setInputMed(t);
                    onSelectTargetMedication(t);
                    fetchRecommendations({
                      patientId: patient.id,
                      targetMedication: t,
                    });
                  }}
                >
                  {t}
                </button>
              ))}
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || !inputMed.trim()}
            >
              <Search size={15} aria-hidden="true" />
              <span>Evaluate Alternatives</span>
            </button>
          </div>
        </form>
      </section>

      {/* Loading state */}
      {isLoading && (
        <div className="page-loading-box mt-6">
          <LoadingState
            size="lg"
            message={`Searching formulary and screening candidate alternatives for ${inputMed}...`}
          />
        </div>
      )}

      {/* Error state */}
      {!isLoading && error && (
        <div className="mt-6">
          <ErrorState
            message={`Failed to retrieve candidate alternatives for ${inputMed}.`}
            detail={error.message}
            retry={handleSearchAlternatives}
          />
        </div>
      )}

      {/* Results Table */}
      {!isLoading && recommendations.length > 0 && (
        <div className="mt-6">
          <AlternativeTable
            recommendations={recommendations}
            targetMedication={inputMed}
            onSelectCandidate={handleAdopt}
          />
        </div>
      )}

      {/* Empty Initial State */}
      {!isLoading && !error && recommendations.length === 0 && (
        <div className="page-empty-selection mt-8">
          <Sparkles size={36} className="text-teal-600" aria-hidden="true" />
          <h4 className="font-semibold text-slate-800 text-sm mt-2">
            No Alternatives Evaluated Yet
          </h4>
          <p className="text-xs text-slate-500 mt-1 max-w-md text-center">
            Specify a target medication above and click "Evaluate Alternatives" to screen candidate substitutes against {patient.name}'s active medical record.
          </p>
        </div>
      )}
    </div>
  );
};
