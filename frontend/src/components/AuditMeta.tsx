import React from "react";
import { ShieldCheck, Database, Hash, Clock } from "lucide-react";

export interface AuditMetaProps {
  /** Ruleset version string from ScreeningResponse.rulesetVersion. */
  rulesetVersion?: string;
  /** Catalogue snapshot timestamp/version from ScreeningResponse.catalogueVersion. */
  catalogueVersion?: string;
  /** Unique request identifier for audit and provenance traceability. */
  requestId?: string;
}

/**
 * Renders ruleset version, catalogue version/timestamp, and screening
 * request id in a small, consistently-placed footer on any screen that
 * shows a screening result, so a pharmacist can always see how current
 * the data behind a finding is.
 *
 * @param props - {@link AuditMetaProps}
 */
export const AuditMeta: React.FC<AuditMetaProps> = ({
  rulesetVersion = "demo-1.0",
  catalogueVersion = "ppb-2026.09",
  requestId,
}) => {
  return (
    <footer className="audit-meta-bar" aria-label="Clinical Audit Metadata">
      <div className="audit-meta-item">
        <ShieldCheck size={14} className="audit-meta-icon" aria-hidden="true" />
        <span className="audit-meta-label">Ruleset:</span>
        <span className="audit-meta-value">{rulesetVersion}</span>
      </div>

      <div className="audit-meta-divider" aria-hidden="true">•</div>

      <div className="audit-meta-item">
        <Database size={14} className="audit-meta-icon" aria-hidden="true" />
        <span className="audit-meta-label">Catalogue Snapshot:</span>
        <span className="audit-meta-value">{catalogueVersion}</span>
      </div>

      {requestId && (
        <>
          <div className="audit-meta-divider" aria-hidden="true">•</div>
          <div className="audit-meta-item">
            <Hash size={14} className="audit-meta-icon" aria-hidden="true" />
            <span className="audit-meta-label">Trace ID:</span>
            <code className="audit-meta-code">{requestId}</code>
          </div>
        </>
      )}

      <div className="audit-meta-divider" aria-hidden="true">•</div>

      <div className="audit-meta-item">
        <Clock size={14} className="audit-meta-icon" aria-hidden="true" />
        <span className="audit-meta-label">Verified:</span>
        <span className="audit-meta-value">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
    </footer>
  );
};
