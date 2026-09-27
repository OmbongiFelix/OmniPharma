import React from "react";
import { AlertCircle, AlertTriangle, RefreshCw } from "lucide-react";

export interface ErrorStateProps {
  /** The error description to show. */
  message?: string;
  /** Detailed error message or stack/code. */
  detail?: string;
  /** Optional retry callback. */
  retry?: () => void;
  /** Visual type: "error" (destructive red) or "warning" (amber, e.g. for incomplete context). */
  severity?: "error" | "warning";
}

/**
 * Shared error placeholder used by every data-fetching component,
 * so error states are communicated consistently and accessibly app-wide.
 *
 * @param props - {@link ErrorStateProps}
 * @returns Accessible error card with descriptive text and optional retry action.
 */
export const ErrorState: React.FC<ErrorStateProps> = ({
  message = "An unexpected error occurred while fetching clinical data.",
  detail,
  retry,
  severity = "error",
}) => {
  const isWarning = severity === "warning";

  return (
    <div
      role="alert"
      className={`error-state-card ${isWarning ? "error-warning" : "error-danger"}`}
    >
      <div className="error-state-icon-box">
        {isWarning ? (
          <AlertTriangle className="error-state-icon" aria-hidden="true" size={24} />
        ) : (
          <AlertCircle className="error-state-icon" aria-hidden="true" size={24} />
        )}
      </div>

      <div className="error-state-content">
        <h4 className="error-state-title">
          {isWarning ? "Clinical Review Notice" : "System Error"}
        </h4>
        <p className="error-state-message">{message}</p>
        {detail && <p className="error-state-detail">{detail}</p>}

        {retry && (
          <button
            type="button"
            onClick={retry}
            className="error-state-retry-btn"
          >
            <RefreshCw size={15} className="mr-1.5" aria-hidden="true" />
            Try again
          </button>
        )}
      </div>
    </div>
  );
};
