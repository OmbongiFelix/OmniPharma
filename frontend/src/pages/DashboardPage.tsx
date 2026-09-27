import React from "react";
import type { PatientSummary } from "../types/patient";
import type { FindingType } from "../types/screening";
import type { PageId } from "../components/AppShell";
import {
  ArrowRight,
  GitCompare,
  AlertOctagon,
  AlertTriangle,
  Baby,
  Activity,
  HeartPulse,
  Droplet,
  Wind,
  Clock,
  Copy,
  HelpCircle,
  Sparkles,
  User,
} from "lucide-react";

export interface DashboardPageProps {
  /** List of synthetic patients available for demo. */
  patients: PatientSummary[];
  /** Currently selected patient ID. */
  selectedPatientId: number | null;
  /** Callback to select a patient. */
  onSelectPatient: (patientId: number) => void;
  /** Navigation callback to switch tabs. */
  onNavigate: (page: PageId) => void;
}

interface FindingCategoryMeta {
  type: FindingType;
  label: string;
  icon: React.ReactElement;
  colorClass: string;
  desc: string;
  samplePatientId: number;
}

const FINDING_CATEGORIES: FindingCategoryMeta[] = [
  {
    type: "DRUG_DRUG_INTERACTION",
    label: "Drug-Drug Interaction",
    icon: <GitCompare size={18} aria-hidden="true" />,
    colorClass: "card-cat-blue",
    desc: "Concurrent drug pairs causing pharmacokinetic or pharmacodynamic antagonism/toxicity.",
    samplePatientId: 2,
  },
  {
    type: "PREGNANCY",
    label: "Pregnancy Warnings",
    icon: <Baby size={18} aria-hidden="true" />,
    colorClass: "card-cat-pink",
    desc: "Teratogenic risks, trimester-specific hazards, and fetal toxicity contraindications.",
    samplePatientId: 3,
  },
  {
    type: "RENAL_CONTRAINDICATION",
    label: "Renal Impairments",
    icon: <Activity size={18} aria-hidden="true" />,
    colorClass: "card-cat-rose",
    desc: "Reduced glomerular clearance, toxic accumulation, and nephrotoxicity cautions.",
    samplePatientId: 6,
  },
  {
    type: "HYPERKALEMIA_RISK",
    label: "Hyperkalemia Risks",
    icon: <AlertTriangle size={18} aria-hidden="true" />,
    colorClass: "card-cat-amber",
    desc: "Serum potassium retention compound risks in chronic kidney disease and ACEi/diuretic therapy.",
    samplePatientId: 6,
  },
  {
    type: "HEPATIC_CONTRAINDICATION",
    label: "Hepatic Impairments",
    icon: <HeartPulse size={18} aria-hidden="true" />,
    colorClass: "card-cat-orange",
    desc: "Impaired liver metabolism, reduced drug clearance, and hepatotoxicity threshold limits.",
    samplePatientId: 4,
  },
  {
    type: "RESPIRATORY_CONTRAINDICATION",
    label: "Respiratory / Asthma",
    icon: <Wind size={18} aria-hidden="true" />,
    colorClass: "card-cat-teal",
    desc: "NSAID and aspirin exacerbated bronchospasm in diagnosed asthma patients.",
    samplePatientId: 5,
  },
  {
    type: "G6PD_CONTRAINDICATION",
    label: "G6PD Deficiency",
    icon: <Droplet size={18} aria-hidden="true" />,
    colorClass: "card-cat-red",
    desc: "Acute hemolytic crisis triggered by sulfonamides, nitrofurantoin, and oxidative agents.",
    samplePatientId: 11,
  },
  {
    type: "AGE_BASED_CAUTION",
    label: "Age-Based / Beers Criteria",
    icon: <Clock size={18} aria-hidden="true" />,
    colorClass: "card-cat-purple",
    desc: "Geriatric fall, cognitive impairment, and sedation hazards with long-acting sedatives.",
    samplePatientId: 12,
  },
  {
    type: "ALLERGY",
    label: "Direct Allergies",
    icon: <AlertOctagon size={18} aria-hidden="true" />,
    colorClass: "card-cat-red",
    desc: "Direct hypersensitivity reaction against documented patient allergens.",
    samplePatientId: 10,
  },
  {
    type: "ALLERGY_CROSS_REACTIVITY",
    label: "Cross-Reactivities",
    icon: <AlertTriangle size={18} aria-hidden="true" />,
    colorClass: "card-cat-violet",
    desc: "Shared structural epitope reactions, such as beta-lactam penicillin/amoxicillin overlaps.",
    samplePatientId: 8,
  },
  {
    type: "DUPLICATE_THERAPY",
    label: "Duplicate Therapies",
    icon: <Copy size={18} aria-hidden="true" />,
    colorClass: "card-cat-slate",
    desc: "Overlapping active ingredients or therapeutic class redundancies causing overdosage.",
    samplePatientId: 1,
  },
  {
    type: "UNRESOLVED_DRUG",
    label: "Unresolved Catalogue",
    icon: <HelpCircle size={18} aria-hidden="true" />,
    colorClass: "card-cat-slate",
    desc: "Medications not found in verified pharmacy registration catalogues.",
    samplePatientId: 1,
  },
];

/**
 * Dashboard screen providing an overview of clinical alert categories,
 * fast demo patient navigation, and direct access to safety workflows.
 *
 * @param props - {@link DashboardPageProps}
 */
export const DashboardPage: React.FC<DashboardPageProps> = ({
  patients,
  selectedPatientId,
  onSelectPatient,
  onNavigate,
}) => {
  const handleLaunchPatient = (id: number) => {
    onSelectPatient(id);
    onNavigate("safety-review");
  };

  return (
    <div className="dashboard-container" aria-label="Pharmacist CDS Dashboard">
      {/* Hero Welcome & Clinical Context Banner */}
      <section className="dashboard-hero-card">
        <div className="hero-content-left">
          <div className="flex items-center gap-2 text-teal-400 font-semibold text-xs tracking-wider uppercase">
            <Sparkles size={15} aria-hidden="true" />
            <span>Agentic Clinical Decision Support</span>
          </div>
          <h2 className="hero-heading">
            Medication Safety & Contraindication Surveillance
          </h2>
          <p className="hero-subtext">
            OmniPharma evaluates patient-specific organ impairments, genetic enzyme deficiencies,
            gestational status, and drug interactions across 12 distinct clinical safety dimensions.
          </p>

          <div className="hero-actions-row">
            {selectedPatientId ? (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigate("safety-review")}
              >
                <span>Review Active Patient</span>
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            ) : (
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleLaunchPatient(3)}
              >
                <span>Launch Demo (Cynthia Wanjiku)</span>
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            )}

            <button
              type="button"
              className="btn-secondary"
              onClick={() => onNavigate("patient-review")}
            >
              <span>View Full Patient Profile</span>
            </button>
          </div>
        </div>

        <div className="hero-stats-badge-grid">
          <div className="hero-stat-card">
            <span className="stat-number">12</span>
            <span className="stat-label">Safety Finding Categories</span>
          </div>
          <div className="hero-stat-card">
            <span className="stat-number">100%</span>
            <span className="stat-label">Explicit State Transparency</span>
          </div>
        </div>
      </section>

      {/* Safety Categories Grid: 12 Distinct Rule Finding Types */}
      <section className="dashboard-categories-section">
        <div className="section-header-row">
          <div>
            <h3 className="section-title">Safety Surveillance Categories (12 Dimensions)</h3>
            <p className="section-subtitle">
              Every backend rule maps to a dedicated finding category with its own label, icon, and clinical mechanism.
            </p>
          </div>
        </div>

        <div className="category-cards-grid">
          {FINDING_CATEGORIES.map((cat) => (
            <div key={cat.type} className={`category-metric-card ${cat.colorClass}`}>
              <div className="cat-card-header">
                <div className="cat-icon-wrap">{cat.icon}</div>
                <span className="cat-type-badge font-mono text-[10px]">
                  {cat.type}
                </span>
              </div>
              <h4 className="cat-title">{cat.label}</h4>
              <p className="cat-desc">{cat.desc}</p>

              <div className="cat-footer">
                <button
                  type="button"
                  className="cat-test-btn"
                  onClick={() => handleLaunchPatient(cat.samplePatientId)}
                  title={`Load demo patient #${cat.samplePatientId} for ${cat.label}`}
                >
                  <span>Test with Demo Patient #{cat.samplePatientId}</span>
                  <ArrowRight size={13} aria-hidden="true" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Synthetic Patient Directory Quick Selection */}
      <section className="dashboard-patients-section">
        <div className="section-header-row">
          <div>
            <h3 className="section-title">Synthetic Patient Cohort (Demo Dataset)</h3>
            <p className="section-subtitle">
              Select any synthetic profile to load conditions, recorded allergies, and active medications.
            </p>
          </div>
        </div>

        <div className="patients-grid-list">
          {patients.map((p) => {
            const isSelected = p.id === selectedPatientId;
            return (
              <div
                key={p.id}
                className={`patient-grid-card ${isSelected ? "card-selected" : ""}`}
                onClick={() => onSelectPatient(p.id)}
              >
                <div className="patient-grid-header">
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-teal-600" aria-hidden="true" />
                    <span className="font-semibold text-slate-900 text-sm">{p.name}</span>
                  </div>
                  <span className="font-mono text-xs text-slate-500">{p.patientCode}</span>
                </div>

                <div className="patient-grid-body text-xs text-slate-600 mt-2 space-y-1">
                  <div>
                    <span className="text-slate-400">Sex:</span> {p.sex} •{" "}
                    <span className="text-slate-400">DOB:</span> {p.dateOfBirth}
                  </div>
                  <div>
                    <span className="text-slate-400">Pregnancy:</span>{" "}
                    <span className="font-medium text-slate-700">{p.pregnancyStatus}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Renal:</span>{" "}
                    <span className="font-medium text-slate-700">{p.renalStatus}</span> •{" "}
                    <span className="text-slate-400">G6PD:</span>{" "}
                    <span className="font-medium text-slate-700">{p.g6pdStatus}</span>
                  </div>
                </div>

                <div className="patient-grid-footer mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="demo-patient-badge">Demo Patient</span>
                  <button
                    type="button"
                    className="text-xs font-semibold text-teal-700 hover:text-teal-900 flex items-center gap-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchPatient(p.id);
                    }}
                  >
                    <span>Run Review</span>
                    <ArrowRight size={12} aria-hidden="true" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
