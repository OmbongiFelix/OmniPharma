import React from "react";
import type { PatientContext } from "../types/patient";
import { User, Calendar, Activity, Baby, ShieldAlert, HeartPulse, Droplet } from "lucide-react";

export interface PatientSummaryProps {
  /** Full clinical context for one patient. */
  patient: PatientContext;
  /** Optional compact mode for header bar. */
  compact?: boolean;
}

/**
 * Calculates current age from ISO-8601 birth date string.
 */
function calculateAge(dateOfBirth: string): number | null {
  try {
    const dob = new Date(dateOfBirth);
    if (isNaN(dob.getTime())) return null;
    const diffMs = Date.now() - dob.getTime();
    const ageDt = new Date(diffMs);
    return Math.abs(ageDt.getUTCFullYear() - 1970);
  } catch {
    return null;
  }
}

/**
 * Formats status chip label and css class for clinical fields.
 * Any missing or "UNKNOWN" value is explicitly labeled "not recorded".
 */
function renderStatusChip(
  field: "pregnancy" | "renal" | "hepatic" | "g6pd",
  rawVal: string | null | undefined
) {
  const normalized = (rawVal || "").trim().toUpperCase();

  if (!normalized || normalized === "UNKNOWN" || normalized === "NOT_RECORDED") {
    return {
      label: "not recorded",
      className: "chip-not-recorded",
      isRecorded: false,
    };
  }

  if (field === "pregnancy") {
    if (normalized === "PREGNANT") {
      return { label: "Pregnant", className: "chip-warning", isRecorded: true };
    }
    if (normalized === "NOT_PREGNANT") {
      return { label: "Not Pregnant", className: "chip-neutral", isRecorded: true };
    }
    if (normalized === "NOT_APPLICABLE") {
      return { label: "Not Applicable", className: "chip-muted", isRecorded: true };
    }
  }

  if (field === "renal") {
    if (normalized === "NORMAL") return { label: "Normal Function", className: "chip-success", isRecorded: true };
    if (normalized.includes("SEVERE")) return { label: "Severe Impairment", className: "chip-danger", isRecorded: true };
    if (normalized.includes("MODERATE")) return { label: "Moderate Impairment", className: "chip-warning", isRecorded: true };
    if (normalized.includes("MILD")) return { label: "Mild Impairment", className: "chip-caution", isRecorded: true };
  }

  if (field === "hepatic") {
    if (normalized === "NORMAL") return { label: "Normal Function", className: "chip-success", isRecorded: true };
    if (normalized.includes("SEVERE")) return { label: "Severe Impairment", className: "chip-danger", isRecorded: true };
    if (normalized.includes("MODERATE")) return { label: "Moderate Impairment", className: "chip-warning", isRecorded: true };
    if (normalized.includes("MILD")) return { label: "Mild Impairment", className: "chip-caution", isRecorded: true };
  }

  if (field === "g6pd") {
    if (normalized === "DEFICIENT") return { label: "G6PD Deficient", className: "chip-danger", isRecorded: true };
    if (normalized === "NORMAL") return { label: "Normal Enzyme Activity", className: "chip-success", isRecorded: true };
  }

  // Fallback if specific string was formatted
  const display = normalized.replace(/_/g, " ").toLowerCase();
  return {
    label: display.charAt(0).toUpperCase() + display.slice(1),
    className: "chip-neutral",
    isRecorded: true,
  };
}

/**
 * Renders demographics, pregnancy status, renal/hepatic/G6PD status for
 * one patient. Any of the four status fields that is `"UNKNOWN"` or
 * missing renders as a visible "not recorded" chip rather than being
 * omitted, per the "make missing context explicit" UX requirement.
 *
 * @param props.patient - Full {@link PatientContext} to summarize.
 */
export const PatientSummary: React.FC<PatientSummaryProps> = ({
  patient,
  compact = false,
}) => {
  const age = calculateAge(patient.dateOfBirth);
  const pregChip = renderStatusChip("pregnancy", patient.pregnancyStatus);
  const renalChip = renderStatusChip("renal", patient.renalStatus);
  const hepaticChip = renderStatusChip("hepatic", patient.hepaticStatus);
  const g6pdChip = renderStatusChip("g6pd", patient.g6pdStatus);

  if (compact) {
    return (
      <div className="patient-summary-compact">
        <div className="patient-demographics-row">
          <span className="patient-name-title">{patient.name}</span>
          <span className="patient-badge-code">{patient.patientCode}</span>
          <span className="demographics-text">
            {patient.sex === "M" ? "Male" : patient.sex === "F" ? "Female" : patient.sex}
            {age !== null ? `, ${age} yrs` : ""}
          </span>
        </div>
        <div className="patient-chips-row">
          <span className={`status-chip ${pregChip.className}`} title="Pregnancy Status">
            <Baby size={13} className="chip-icon" aria-hidden="true" />
            <span className="chip-prefix">Pregnancy:</span> {pregChip.label}
          </span>
          <span className={`status-chip ${renalChip.className}`} title="Renal Status">
            <Activity size={13} className="chip-icon" aria-hidden="true" />
            <span className="chip-prefix">Renal:</span> {renalChip.label}
          </span>
          <span className={`status-chip ${hepaticChip.className}`} title="Hepatic Status">
            <HeartPulse size={13} className="chip-icon" aria-hidden="true" />
            <span className="chip-prefix">Hepatic:</span> {hepaticChip.label}
          </span>
          <span className={`status-chip ${g6pdChip.className}`} title="G6PD Status">
            <Droplet size={13} className="chip-icon" aria-hidden="true" />
            <span className="chip-prefix">G6PD:</span> {g6pdChip.label}
          </span>
        </div>
      </div>
    );
  }

  return (
    <section className="patient-summary-card" aria-label="Patient Clinical Profile">
      <div className="patient-card-header">
        <div className="patient-avatar-box">
          <User size={28} className="text-teal-700" aria-hidden="true" />
        </div>
        <div className="patient-title-group">
          <div className="flex items-center gap-3">
            <h2 className="patient-primary-name">{patient.name}</h2>
            <span className="patient-code-badge">{patient.patientCode}</span>
          </div>
          <div className="patient-demographics-sub">
            <span className="flex items-center gap-1.5">
              <Calendar size={14} className="text-slate-400" aria-hidden="true" />
              DOB: {patient.dateOfBirth} {age !== null && `(${age} years old)`}
            </span>
            <span className="dot-sep">•</span>
            <span>Sex: {patient.sex === "M" ? "Male" : patient.sex === "F" ? "Female" : patient.sex}</span>
          </div>
        </div>
      </div>

      <div className="clinical-status-grid">
        {/* Pregnancy Status */}
        <div className="status-metric-card">
          <div className="metric-header">
            <Baby size={16} className="text-pink-600" aria-hidden="true" />
            <span className="metric-label">Pregnancy Status</span>
          </div>
          <div className="metric-value-container">
            <span className={`status-chip ${pregChip.className}`}>
              {pregChip.label}
            </span>
          </div>
        </div>

        {/* Renal Status */}
        <div className="status-metric-card">
          <div className="metric-header">
            <Activity size={16} className="text-blue-600" aria-hidden="true" />
            <span className="metric-label">Renal Function</span>
          </div>
          <div className="metric-value-container">
            <span className={`status-chip ${renalChip.className}`}>
              {renalChip.label}
            </span>
          </div>
        </div>

        {/* Hepatic Status */}
        <div className="status-metric-card">
          <div className="metric-header">
            <HeartPulse size={16} className="text-amber-600" aria-hidden="true" />
            <span className="metric-label">Hepatic Function</span>
          </div>
          <div className="metric-value-container">
            <span className={`status-chip ${hepaticChip.className}`}>
              {hepaticChip.label}
            </span>
          </div>
        </div>

        {/* G6PD Status */}
        <div className="status-metric-card">
          <div className="metric-header">
            <Droplet size={16} className="text-purple-600" aria-hidden="true" />
            <span className="metric-label">G6PD Status</span>
          </div>
          <div className="metric-value-container">
            <span className={`status-chip ${g6pdChip.className}`}>
              {g6pdChip.label}
            </span>
          </div>
        </div>
      </div>

      {(!renalChip.isRecorded || !hepaticChip.isRecorded || !g6pdChip.isRecorded) && (
        <div className="missing-context-callout">
          <ShieldAlert size={16} className="text-amber-600 shrink-0" aria-hidden="true" />
          <p className="missing-context-text">
            <strong>Clinical Safety Notice:</strong> One or more organ function or enzyme profiles are
            marked <span className="underline decoration-amber-500 font-semibold">not recorded</span>. The safety review engine evaluates risk based on documented indicators and will flag caution if an unrecorded status creates clinical ambiguity.
          </p>
        </div>
      )}
    </section>
  );
};
