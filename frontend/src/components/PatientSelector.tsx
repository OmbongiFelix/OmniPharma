import React, { useState, useMemo } from "react";
import { usePatients } from "../hooks/usePatients";
import { User, ChevronDown, Check, Sparkles, Search } from "lucide-react";
import { LoadingState } from "./LoadingState";

export interface PatientSelectorProps {
  /** Called with the selected patient's id. */
  onSelect: (patientId: number) => void;
  /** Currently selected id, for highlighting; null when no patient is selected yet. */
  selectedPatientId: number | null;
}

/**
 * Mapping of demo patients to the clinical comorbidity category they illustrate,
 * per 10_Mock_Data_Expansion_Spec.md.
 */
const DEMO_CATEGORY_MAP: Record<number, { tag: string; color: string; desc: string }> = {
  1: { tag: "Clear / Baseline", color: "tag-emerald", desc: "No critical interactions flagged" },
  2: { tag: "Drug-Drug Interaction", color: "tag-blue", desc: "Warfarin + NSAID interaction" },
  3: { tag: "Pregnancy Warning", color: "tag-pink", desc: "Pregnancy + teratogen risk" },
  4: { tag: "Hepatic Impairment", color: "tag-amber", desc: "Hepatic contraindication (statin)" },
  5: { tag: "Respiratory / Asthma", color: "tag-indigo", desc: "Asthma + NSAID bronchospasm" },
  6: { tag: "Renal & Hyperkalemia", color: "tag-rose", desc: "CKD + Metformin & Lisinopril" },
  7: { tag: "Hypertension Review", color: "tag-slate", desc: "Cardiovascular management" },
  8: { tag: "Allergy Cross-Reactivity", color: "tag-purple", desc: "Penicillin -> Amoxicillin cross-reactivity" },
  9: { tag: "Diabetes Monitoring", color: "tag-slate", desc: "Metformin therapy review" },
  10: { tag: "Known Drug Allergy", color: "tag-purple", desc: "Documented penicillin allergy" },
  11: { tag: "G6PD Deficiency", color: "tag-red", desc: "G6PD deficiency + co-trimoxazole hemolysis" },
  12: { tag: "Age-Based Caution", color: "tag-orange", desc: "Geriatric caution: diazepam fall risk" },
};

/**
 * Dropdown/search control for choosing the active demo patient.
 * Fetches the patient list via {@link usePatients} and calls
 * `onSelect` with the chosen patient's id. Renders a "Demo Patient"
 * badge next to every entry, since this dataset is synthetic only.
 *
 * @param props.onSelect - Called with the selected patient's id.
 * @param props.selectedPatientId - Currently selected id, for
 *   highlighting; null when no patient is selected yet.
 */
export const PatientSelector: React.FC<PatientSelectorProps> = ({
  onSelect,
  selectedPatientId,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const { patients, isLoading, error } = usePatients(searchTerm);

  const selectedPatient = useMemo(() => {
    return patients.find((p) => p.id === selectedPatientId) || null;
  }, [patients, selectedPatientId]);

  const handleSelect = (id: number) => {
    onSelect(id);
    setIsOpen(false);
  };

  return (
    <div className="patient-selector-wrapper">
      <div className="selector-control-bar">
        {/* Active Patient Trigger Button */}
        <button
          type="button"
          className="active-patient-trigger"
          onClick={() => setIsOpen(!isOpen)}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="trigger-icon-box">
              <User size={18} className="text-teal-700" aria-hidden="true" />
            </div>

            {selectedPatient ? (
              <div className="trigger-text-group text-left">
                <div className="flex items-center gap-2">
                  <span className="trigger-patient-name font-semibold text-slate-900">
                    {selectedPatient.name}
                  </span>
                  <span className="demo-patient-badge">Demo Patient</span>
                  <span className="trigger-patient-code font-mono text-xs text-slate-500">
                    {selectedPatient.patientCode}
                  </span>
                </div>
                {DEMO_CATEGORY_MAP[selectedPatient.id] && (
                  <span className={`category-mini-tag ${DEMO_CATEGORY_MAP[selectedPatient.id].color}`}>
                    {DEMO_CATEGORY_MAP[selectedPatient.id].tag}
                  </span>
                )}
              </div>
            ) : (
              <span className="text-slate-500 font-medium">Select a patient for review...</span>
            )}
          </div>

          <ChevronDown
            size={18}
            className={`trigger-chevron transition-transform ${isOpen ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </button>
      </div>

      {/* Dropdown Menu Modal */}
      {isOpen && (
        <div className="patient-selector-dropdown" role="listbox">
          {/* Quick Demo Category Shortcuts */}
          <div className="demo-shortcuts-panel">
            <div className="shortcuts-header">
              <Sparkles size={14} className="text-teal-600" aria-hidden="true" />
              <span className="text-xs font-semibold text-slate-700">Quick Comorbidity Presets (Demo Mode)</span>
            </div>
            <div className="shortcuts-buttons-wrap">
              {[
                { id: 3, label: "Pregnancy" },
                { id: 6, label: "Renal & Hyperkalemia" },
                { id: 4, label: "Hepatic" },
                { id: 11, label: "G6PD Deficiency" },
                { id: 5, label: "Respiratory" },
                { id: 12, label: "Age-Based" },
                { id: 8, label: "Allergy Cross-Reactivity" },
                { id: 2, label: "Drug-Drug Interaction" },
              ].map((btn) => (
                <button
                  key={btn.id}
                  type="button"
                  className={`shortcut-chip ${selectedPatientId === btn.id ? "shortcut-chip-active" : ""}`}
                  onClick={() => handleSelect(btn.id)}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {/* Search bar inside dropdown */}
          <div className="dropdown-search-box">
            <Search size={15} className="text-slate-400 shrink-0" aria-hidden="true" />
            <input
              type="text"
              className="dropdown-search-input"
              placeholder="Filter patients by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>

          {/* Patient Options List */}
          <div className="patient-options-scroll">
            {isLoading && (
              <div className="p-4">
                <LoadingState size="sm" message="Loading synthetic patients..." />
              </div>
            )}

            {!isLoading && error && (
              <div className="p-4 text-xs text-rose-600">
                Failed to load patient records: {error.message}
              </div>
            )}

            {!isLoading && !error && patients.length === 0 && (
              <div className="p-4 text-xs text-slate-500 text-center">
                No matching patients found in synthetic database.
              </div>
            )}

            {!isLoading &&
              patients.map((p) => {
                const isSelected = p.id === selectedPatientId;
                const category = DEMO_CATEGORY_MAP[p.id];
                return (
                  <div
                    key={p.id}
                    role="option"
                    aria-selected={isSelected}
                    className={`patient-option-item ${isSelected ? "option-selected" : ""}`}
                    onClick={() => handleSelect(p.id)}
                  >
                    <div className="option-info-left">
                      <div className="flex items-center gap-2">
                        <span className="option-patient-name font-semibold text-slate-900 text-sm">
                          {p.name}
                        </span>
                        <span className="demo-patient-badge">Demo Patient</span>
                        <span className="option-code font-mono text-xs text-slate-500">
                          {p.patientCode}
                        </span>
                      </div>

                      <div className="option-demographics-row text-xs text-slate-500 mt-0.5">
                        <span>Sex: {p.sex}</span>
                        <span>•</span>
                        <span>DOB: {p.dateOfBirth}</span>
                        {category && (
                          <>
                            <span>•</span>
                            <span className={`category-tag-inline ${category.color}`}>
                              {category.tag}: {category.desc}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {isSelected && (
                      <div className="option-check-icon">
                        <Check size={18} className="text-teal-600" aria-hidden="true" />
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};
