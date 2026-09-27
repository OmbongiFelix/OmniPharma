import React from "react";
import type { AllergyRecord } from "../types/patient";
import { ShieldCheck, AlertOctagon, AlertTriangle } from "lucide-react";

export interface AllergyListProps {
  /** Array of recorded allergies. */
  items: AllergyRecord[];
}

/**
 * Renders a patient's recorded allergies as a scannable list.
 * AllergyList renders `allergen: "none"` rows as a single "No known allergies" line,
 * not as an empty-looking allergy chip.
 *
 * @param props - {@link AllergyListProps}
 */
export const AllergyList: React.FC<AllergyListProps> = ({ items }) => {
  // Check if allergies list is empty or explicitly "none"
  const hasNoKnownAllergies =
    !items ||
    items.length === 0 ||
    (items.length === 1 &&
      (items[0].allergen.toLowerCase() === "none" ||
        items[0].severity.toUpperCase() === "NONE"));

  if (hasNoKnownAllergies) {
    return (
      <div className="empty-sublist no-allergies-callout" role="status">
        <ShieldCheck size={18} className="text-emerald-600" aria-hidden="true" />
        <span className="font-medium text-emerald-800">No known drug allergies (NKDA)</span>
      </div>
    );
  }

  // Filter out any entries that might just be "none" if multiple exist
  const activeAllergies = items.filter(
    (a) => a.allergen.toLowerCase() !== "none" && a.severity.toUpperCase() !== "NONE"
  );

  return (
    <div className="allergies-list-container" aria-label="Known Allergies">
      <ul className="allergies-grid">
        {activeAllergies.map((allergy, idx) => {
          const sev = allergy.severity.toUpperCase();
          const isHigh = sev === "HIGH" || sev === "SEVERE" || sev === "LIFE_THREATENING";
          return (
            <li
              key={`${allergy.allergen}-${idx}`}
              className={`allergy-card-item ${isHigh ? "allergy-high-risk" : "allergy-moderate-risk"}`}
            >
              <div className="allergy-header-row">
                <div className="flex items-center gap-2">
                  {isHigh ? (
                    <AlertOctagon size={16} className="text-rose-600 shrink-0" aria-hidden="true" />
                  ) : (
                    <AlertTriangle size={16} className="text-amber-600 shrink-0" aria-hidden="true" />
                  )}
                  <span className="allergy-substance">{allergy.allergen}</span>
                </div>
                <span className={`allergy-severity-badge ${isHigh ? "badge-danger" : "badge-warning"}`}>
                  {allergy.severity}
                </span>
              </div>
              {allergy.reaction && (
                <div className="allergy-reaction-row">
                  <span className="reaction-label">Reaction:</span>
                  <span className="reaction-text">{allergy.reaction}</span>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
};
