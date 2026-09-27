import React from "react";
import type { ConditionRecord } from "../types/patient";
import { CheckCircle2 } from "lucide-react";

export interface ConditionsListProps {
  /** Array of active or historical condition records. */
  items: ConditionRecord[];
}

/**
 * Renders a patient's active and documented conditions as a scannable list.
 *
 * @param props - {@link ConditionsListProps}
 */
export const ConditionsList: React.FC<ConditionsListProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="empty-sublist">
        <CheckCircle2 size={16} className="text-emerald-500" aria-hidden="true" />
        <span>No diagnosed conditions recorded</span>
      </div>
    );
  }

  return (
    <div className="conditions-list-container" aria-label="Diagnosed Conditions">
      <ul className="conditions-grid">
        {items.map((cond, idx) => {
          const isActive = cond.status === "ACTIVE" || cond.status === "CHRONIC";
          return (
            <li key={`${cond.conditionCode}-${idx}`} className="condition-card-item">
              <div className="condition-header-row">
                <span className="condition-name">{cond.conditionName}</span>
                <span className="condition-code-badge">{cond.conditionCode}</span>
              </div>
              <div className="condition-meta-row">
                <span className={`status-pill ${isActive ? "pill-active" : "pill-resolved"}`}>
                  {cond.status}
                </span>
                {cond.onsetDate && (
                  <span className="condition-onset">
                    Onset: {cond.onsetDate}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
