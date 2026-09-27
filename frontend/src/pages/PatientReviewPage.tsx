import React from "react";
import type { PatientContext } from "../types/patient";
import type { PageId } from "../components/AppShell";
import { PatientSummary } from "../components/PatientSummary";
import { ConditionsList } from "../components/ConditionsList";
import { AllergyList } from "../components/AllergyList";
import { MedicationTable } from "../components/MedicationTable";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import {
  ShieldAlert,
  ArrowRight,
  FileHeart,
  AlertOctagon,
  Pill,
} from "lucide-react";

export interface PatientReviewPageProps {
  /** Full clinical context for the active patient. */
  patient: PatientContext | null;
  /** Whether patient context is loading. */
  isLoading: boolean;
  /** Any error encountered while fetching patient context. */
  error: Error | null;
  /** Retry callback. */
  onRetry?: () => void;
  /** Navigation callback to switch screens. */
  onNavigate: (page: PageId) => void;
  /** Callback to launch screening with a specific medication. */
  onSelectMedicationForReview?: (medicationName: string) => void;
}

/**
 * Patient Review Screen displaying comprehensive clinical background:
 * demographics, explicit organ & enzyme statuses, active conditions,
 * recorded allergies, and active & past medication regimens.
 *
 * @param props - {@link PatientReviewPageProps}
 */
export const PatientReviewPage: React.FC<PatientReviewPageProps> = ({
  patient,
  isLoading,
  error,
  onRetry,
  onNavigate,
  onSelectMedicationForReview,
}) => {
  if (isLoading) {
    return (
      <div className="page-loading-box">
        <LoadingState size="lg" message="Retrieving patient clinical context and medication history..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-error-box">
        <ErrorState
          message="Failed to load patient clinical profile."
          detail={error.message}
          retry={onRetry}
        />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="page-empty-selection">
        <ShieldAlert size={40} className="text-slate-400" aria-hidden="true" />
        <h3 className="text-lg font-bold text-slate-700 mt-3">No Patient Selected</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md text-center">
          Please select a demo patient from the selector in the top bar to review their clinical context and medication regimen.
        </p>
      </div>
    );
  }

  const activePrescriptions = patient.currentPrescriptions || [];
  const medHistory = patient.medicationHistory || [];

  return (
    <div className="patient-review-container" aria-label="Patient Review Dossier">
      {/* Page Header and Quick CTA */}
      <div className="review-page-header">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Patient Clinical Dossier</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Review documented clinical history, organ function statuses, and baseline therapies before screening.
          </p>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={() => onNavigate("safety-review")}
        >
          <ShieldAlert size={16} aria-hidden="true" />
          <span>Proceed to Safety Review</span>
          <ArrowRight size={16} aria-hidden="true" />
        </button>
      </div>

      {/* Demographics & Explicit Clinical Statuses */}
      <div className="mt-4">
        <PatientSummary patient={patient} />
      </div>

      {/* Two-Column Layout for Conditions and Allergies */}
      <div className="clinical-records-grid mt-6">
        {/* Conditions List */}
        <section className="record-panel-card" aria-labelledby="conditions-heading">
          <div className="panel-card-header">
            <div className="flex items-center gap-2">
              <FileHeart size={18} className="text-teal-600" aria-hidden="true" />
              <h3 id="conditions-heading" className="panel-title">
                Diagnosed Conditions ({patient.conditions.length})
              </h3>
            </div>
            <span className="panel-subtitle-tag">ICD-10 / Active Diagnoses</span>
          </div>

          <div className="panel-card-body">
            <ConditionsList items={patient.conditions} />
          </div>
        </section>

        {/* Allergy List */}
        <section className="record-panel-card" aria-labelledby="allergies-heading">
          <div className="panel-card-header">
            <div className="flex items-center gap-2">
              <AlertOctagon size={18} className="text-rose-600" aria-hidden="true" />
              <h3 id="allergies-heading" className="panel-title">
                Documented Allergies ({patient.allergies.length})
              </h3>
            </div>
            <span className="panel-subtitle-tag">Hypersensitivities</span>
          </div>

          <div className="panel-card-body">
            <AllergyList items={patient.allergies} />
          </div>
        </section>
      </div>

      {/* Current Prescriptions and Medication History Table */}
      <section className="medications-section-card mt-6" aria-labelledby="medications-heading">
        <div className="section-card-header">
          <div className="flex items-center gap-2">
            <Pill size={20} className="text-teal-600" aria-hidden="true" />
            <div>
              <h3 id="medications-heading" className="text-base font-bold text-slate-800">
                Prescribed & Historical Medications ({activePrescriptions.length + medHistory.length})
              </h3>
              <p className="text-xs text-slate-500">
                Active prescriptions are loaded into the safety screening engine by default.
              </p>
            </div>
          </div>
        </div>

        <div className="section-card-body">
          <MedicationTable
            prescriptions={activePrescriptions}
            history={medHistory}
            mode="both"
            onSelectMedication={onSelectMedicationForReview}
          />
        </div>
      </section>
    </div>
  );
};
