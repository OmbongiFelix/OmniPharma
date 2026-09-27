import React, { useState } from "react";
import type { FindingType, SafetyFinding, Severity } from "../types/screening";
import { EvidencePanel } from "./EvidencePanel";
import {
  Ban,
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Pill,
  Baby,
  Activity,
  HeartPulse,
  Droplet,
  Wind,
  Clock,
  Copy,
  HelpCircle,
  GitCompare,
  ArrowRight,
} from "lucide-react";

export interface FindingCardProps {
  /** The finding to render. */
  finding: SafetyFinding;
  /** Whether the technical detail (rule id, rationale, evidence) starts expanded. */
  expanded?: boolean;
  /** Optional callback to explore alternative medicines for an affected drug. */
  onFindAlternatives?: (medicationName: string) => void;
}

/**
 * Returns the exact label, icon, and description for a FindingType via an exhaustive switch.
 * NOTE: Per the architecture specification, this switch contains NO default case.
 * A missing FindingType will result in a TypeScript compilation error.
 */
function getFindingTypeDescriptor(type: FindingType): {
  label: string;
  icon: React.ReactElement;
  badgeClass: string;
} {
  switch (type) {
    case "DRUG_DRUG_INTERACTION":
      return {
        label: "Drug-Drug Interaction",
        icon: <GitCompare size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-ddi",
      };
    case "ALLERGY":
      return {
        label: "Known Allergy Contraindication",
        icon: <AlertOctagon size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-allergy",
      };
    case "ALLERGY_CROSS_REACTIVITY":
      return {
        label: "Allergy Cross-Reactivity Risk",
        icon: <AlertTriangle size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-cross-react",
      };
    case "PREGNANCY":
      return {
        label: "Pregnancy Safety Warning",
        icon: <Baby size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-pregnancy",
      };
    case "RENAL_CONTRAINDICATION":
      return {
        label: "Renal Impairment Contraindication",
        icon: <Activity size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-renal",
      };
    case "HEPATIC_CONTRAINDICATION":
      return {
        label: "Hepatic Impairment Contraindication",
        icon: <HeartPulse size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-hepatic",
      };
    case "HYPERKALEMIA_RISK":
      return {
        label: "Hyperkalemia Risk",
        icon: <AlertCircle size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-hyperkalemia",
      };
    case "G6PD_CONTRAINDICATION":
      return {
        label: "G6PD Deficiency Contraindication",
        icon: <Droplet size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-g6pd",
      };
    case "RESPIRATORY_CONTRAINDICATION":
      return {
        label: "Respiratory / Bronchospasm Contraindication",
        icon: <Wind size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-respiratory",
      };
    case "AGE_BASED_CAUTION":
      return {
        label: "Age-Based / Geriatric Caution",
        icon: <Clock size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-age",
      };
    case "DUPLICATE_THERAPY":
      return {
        label: "Duplicate Therapy Alert",
        icon: <Copy size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-duplicate",
      };
    case "UNRESOLVED_DRUG":
      return {
        label: "Unresolved / Unrecognized Drug",
        icon: <HelpCircle size={16} aria-hidden="true" />,
        badgeClass: "badge-finding-unresolved",
      };
  }
}

/**
 * Returns textual label and icon for severity rating to ensure severity
 * is NEVER communicated via color alone.
 */
function getSeverityDescriptor(sev: Severity): {
  label: string;
  icon: React.ReactElement;
  containerClass: string;
  badgeClass: string;
} {
  switch (sev) {
    case "CONTRAINDICATED":
      return {
        label: "CONTRAINDICATED",
        icon: <Ban size={15} className="severity-icon" aria-hidden="true" />,
        containerClass: "finding-card-contraindicated",
        badgeClass: "severity-badge-contraindicated",
      };
    case "HIGH":
      return {
        label: "HIGH RISK",
        icon: <AlertOctagon size={15} className="severity-icon" aria-hidden="true" />,
        containerClass: "finding-card-high",
        badgeClass: "severity-badge-high",
      };
    case "MODERATE":
      return {
        label: "MODERATE RISK",
        icon: <AlertTriangle size={15} className="severity-icon" aria-hidden="true" />,
        containerClass: "finding-card-moderate",
        badgeClass: "severity-badge-moderate",
      };
    case "LOW":
      return {
        label: "LOW RISK",
        icon: <AlertCircle size={15} className="severity-icon" aria-hidden="true" />,
        containerClass: "finding-card-low",
        badgeClass: "severity-badge-low",
      };
    case "INFO":
      return {
        label: "INFORMATIONAL",
        icon: <Info size={15} className="severity-icon" aria-hidden="true" />,
        containerClass: "finding-card-info",
        badgeClass: "severity-badge-info",
      };
  }
}

/**
 * Renders one {@link SafetyFinding}. Severity is always communicated
 * with a text label and icon, never color alone. Each of the twelve
 * `FindingType` values maps to its own label and icon in a single
 * exhaustive switch — the switch has no `default` case, so adding a
 * new backend finding type without updating this component is a
 * TypeScript compile error, not a silent generic render.
 *
 * @param props.finding - The finding to render.
 * @param props.expanded - Whether the technical detail (rule id,
 *   rationale, evidence) starts expanded; the concise summary always
 *   renders regardless of this flag.
 */
export const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  expanded = false,
  onFindAlternatives,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(expanded);

  const typeDesc = getFindingTypeDescriptor(finding.type);
  const sevDesc = getSeverityDescriptor(finding.severity);

  return (
    <article
      className={`finding-card ${sevDesc.containerClass}`}
      aria-labelledby={`finding-summary-${finding.ruleId}`}
    >
      <div className="finding-card-header">
        <div className="finding-labels-row">
          {/* Finding Category with Icon and explicit Text */}
          <span className={`finding-type-badge ${typeDesc.badgeClass}`}>
            {typeDesc.icon}
            <span className="finding-type-text">{typeDesc.label}</span>
          </span>

          {/* Severity indicator with Icon and explicit Text */}
          <span className={`severity-badge ${sevDesc.badgeClass}`}>
            {sevDesc.icon}
            <span className="severity-text">{sevDesc.label}</span>
          </span>
        </div>

        {/* Affected Medications */}
        {finding.medications && finding.medications.length > 0 && (
          <div className="finding-affected-meds">
            <span className="affected-meds-label">Affected Medicines:</span>
            <div className="meds-pill-group">
              {finding.medications.map((m, idx) => (
                <span key={idx} className="med-pill-item">
                  <Pill size={12} className="inline mr-1" aria-hidden="true" />
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Concise Summary (Always visible) */}
      <div className="finding-summary-section">
        <h4 id={`finding-summary-${finding.ruleId}`} className="finding-summary-text">
          {finding.summary}
        </h4>
      </div>

      {/* Expand/Collapse Toggle Button */}
      <div className="finding-card-footer">
        <button
          type="button"
          className="toggle-detail-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <span>{isExpanded ? "Hide Technical Details" : "View Mechanism & Evidence"}</span>
          {isExpanded ? (
            <ChevronUp size={16} aria-hidden="true" />
          ) : (
            <ChevronDown size={16} aria-hidden="true" />
          )}
        </button>

        {/* Quick link to alternatives for flagged medicines */}
        {onFindAlternatives && finding.medications.length > 0 && (
          <button
            type="button"
            className="find-alts-btn"
            onClick={() => onFindAlternatives(finding.medications[0])}
            title={`Find alternatives for ${finding.medications[0]}`}
          >
            <span>Explore alternatives for {finding.medications[0]}</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Expandable Technical Detail */}
      {isExpanded && (
        <div className="finding-technical-panel">
          {/* Rule ID Metadata */}
          <div className="technical-meta-row">
            <span className="meta-label">Clinical Rule ID:</span>
            <code className="meta-rule-code">{finding.ruleId}</code>
          </div>

          {/* Rationale and Mechanism */}
          <div className="technical-rationale-section">
            <h5 className="rationale-heading">Clinical Mechanism & Pharmacological Rationale:</h5>
            <p className="rationale-text">{finding.rationale}</p>
          </div>

          {/* Evidence Panel */}
          <div className="technical-evidence-section">
            <EvidencePanel finding={finding} />
          </div>
        </div>
      )}
    </article>
  );
};
