import React, { useState } from "react";
import type { PatientContext } from "../types/patient";
import type { PageId } from "../components/AppShell";
import { SafetyReviewPanel } from "../components/SafetyReviewPanel";
import { DrugSearch } from "../components/DrugSearch";
import { Pill, Plus, X, ShieldAlert, Sparkles, RotateCcw, AlertTriangle } from "lucide-react";

export interface SafetyReviewPageProps {
  /** Active patient clinical context. */
  patient: PatientContext | null;
  /** Currently selected medication list being reviewed. */
  medications: string[];
  /** Callback to update medications array. */
  onUpdateMedications: (meds: string[]) => void;
  /** Navigation callback to switch screens. */
  onNavigate: (page: PageId) => void;
  /** Callback to explore alternatives for a flagged drug. */
  onFindAlternatives: (medicationName: string) => void;
}

/**
 * Medication Safety Review Screen:
 * Configures the active screening regimen, adds/removes medicines via
 * catalogue search or quick presets, runs deterministic safety screening,
 * and renders structured findings with expandable rationale and evidence.
 *
 * @param props - {@link SafetyReviewPageProps}
 */
export const SafetyReviewPage: React.FC<SafetyReviewPageProps> = ({
  patient,
  medications,
  onUpdateMedications,
  onNavigate,
  onFindAlternatives,
}) => {
  const [showAddForm, setShowAddForm] = useState<boolean>(false);

  const handleRemoveMed = (medToRemove: string) => {
    onUpdateMedications(medications.filter((m) => m.toLowerCase() !== medToRemove.toLowerCase()));
  };

  const handleAddMed = (_drugId: number, drugName?: string) => {
    if (!drugName) return;
    const trimmed = drugName.trim().toLowerCase();
    if (!medications.some((m) => m.toLowerCase() === trimmed)) {
      onUpdateMedications([...medications, trimmed]);
    }
    setShowAddForm(false);
  };

  const handleResetToPatientMeds = () => {
    if (!patient?.currentPrescriptions) return;
    const defaultMeds = patient.currentPrescriptions.map((p) => p.medicationName.toLowerCase());
    onUpdateMedications(defaultMeds);
  };

  if (!patient) {
    return (
      <div className="page-empty-selection">
        <ShieldAlert size={40} className="text-slate-400" aria-hidden="true" />
        <h3 className="text-lg font-bold text-slate-700 mt-3">Select a Patient to Begin Safety Review</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md text-center">
          Choose a synthetic demo patient from the top bar dropdown or from the Dashboard to load their baseline prescriptions.
        </p>
      </div>
    );
  }

  return (
    <div className="safety-review-page-container" aria-label="Medication Safety Review">
      {/* Header and Regimen Controls */}
      <div className="safety-page-header">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Medication Safety Review</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure the proposed medication regimen and run deterministic clinical safety rules against{" "}
            <strong>{patient.name}</strong>'s active conditions, allergies, and organ parameters.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={handleResetToPatientMeds}
            title="Reset to patient's active prescriptions"
          >
            <RotateCcw size={14} aria-hidden="true" />
            <span>Reset to Active Prescriptions</span>
          </button>
        </div>
      </div>

      {/* Regimen Medicines Management Card */}
      <section className="regimen-selector-card mt-4" aria-label="Medication Regimen Under Evaluation">
        <div className="regimen-header-line flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Pill size={18} className="text-teal-600" aria-hidden="true" />
            <h3 className="font-semibold text-slate-800 text-sm">
              Regimen Under Evaluation ({medications.length} Medicines)
            </h3>
          </div>

          <button
            type="button"
            className="action-btn-sm"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <Plus size={14} aria-hidden="true" />
            <span>{showAddForm ? "Close Search" : "Add Medication from Catalogue"}</span>
          </button>
        </div>

        {/* Autocomplete Drug Search for Adding Medicines */}
        {showAddForm && (
          <div className="add-drug-search-panel mt-3 p-3 bg-teal-50/60 rounded-lg border border-teal-200">
            <label className="block text-xs font-semibold text-teal-950 mb-1.5">
              Search catalogue to add an additional medicine or candidate:
            </label>
            <DrugSearch onSelect={handleAddMed} placeholder="Search by INN or brand name (e.g. ibuprofen, amoxicillin, diazepam)..." />
          </div>
        )}

        {/* Medication Chips List */}
        <div className="medication-chips-stack mt-3">
          {medications.length === 0 ? (
            <div className="empty-sublist text-xs text-amber-700 bg-amber-50 border border-amber-200 p-2.5 rounded-lg flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-600 shrink-0" aria-hidden="true" />
              <span>No medications in regimen. Add at least one medication above to run safety review.</span>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {medications.map((med, idx) => (
                <div key={idx} className="regimen-med-chip">
                  <Pill size={14} className="text-teal-700" aria-hidden="true" />
                  <span className="med-name-text font-medium text-slate-900">{med}</span>
                  <button
                    type="button"
                    className="remove-med-btn"
                    onClick={() => handleRemoveMed(med)}
                    title={`Remove ${med} from review`}
                    aria-label={`Remove ${med}`}
                  >
                    <X size={14} aria-hidden="true" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Common Clinical Demo Test Triggers */}
        <div className="quick-test-triggers mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-slate-500 flex items-center gap-1">
            <Sparkles size={13} className="text-teal-600" aria-hidden="true" />
            <span>Add test triggers:</span>
          </span>
          {[
            "warfarin",
            "ibuprofen",
            "metformin",
            "lisinopril",
            "amoxicillin",
            "sulfamethoxazole-trimethoprim",
            "diazepam",
            "spironolactone",
            "atorvastatin",
          ].map((drug) => {
            const alreadyIn = medications.some((m) => m.toLowerCase() === drug);
            return (
              <button
                key={drug}
                type="button"
                className={`trigger-badge-btn ${alreadyIn ? "opacity-40 cursor-not-allowed" : ""}`}
                disabled={alreadyIn}
                onClick={() => handleAddMed(0, drug)}
                title={`Add ${drug} to review`}
              >
                + {drug}
              </button>
            );
          })}
        </div>
      </section>

      {/* Safety Review Action & Findings Stack */}
      <section className="mt-6">
        <SafetyReviewPanel
          patientId={patient.id}
          medicationNames={medications}
          onFindAlternatives={(med) => {
            onFindAlternatives(med);
            onNavigate("alternatives");
          }}
        />
      </section>
    </div>
  );
};
