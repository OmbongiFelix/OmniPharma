import React, { Component, type ReactNode } from "react";
import { ErrorState } from "./ErrorState";
import { PatientSelector } from "./PatientSelector";
import { PatientSummary } from "./PatientSummary";
import type { PatientContext } from "../types/patient";
import {
  ShieldAlert,
  LayoutDashboard,
  UserCheck,
  ShieldCheck,
  Sparkles,
  Pill,
} from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Shell-level React Error Boundary so any uncaught component crash
 * renders an ErrorState rather than blanking the whole app.
 */
class ShellErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught render error inside AppShell:", error, errorInfo);
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-4xl mx-auto">
          <ErrorState
            message="An unexpected rendering error occurred in this view."
            detail={this.state.error?.message || "Internal React component exception"}
            retry={() => this.setState({ hasError: false, error: null })}
          />
        </div>
      );
    }
    return this.props.children;
  }
}

export type PageId = "dashboard" | "patient-review" | "safety-review" | "alternatives" | "drug-details";

export interface AppShellProps {
  /** The currently routed page. */
  children: ReactNode;
  /** Active page ID for navigation highlighting. */
  activePage: PageId;
  /** Callback to navigate between screens. */
  onNavigate: (page: PageId) => void;
  /** Currently selected patient ID. */
  selectedPatientId: number | null;
  /** Callback when patient is selected. */
  onSelectPatient: (patientId: number) => void;
  /** Full clinical context of selected patient if loaded. */
  activePatient?: PatientContext | null;
}

/**
 * Top-level layout: header, patient context bar, and routed page body.
 * Renders {@link ErrorState} at the shell level for any uncaught render
 * error in a page, so one broken page never blanks the whole app.
 *
 * @param props.children - The currently routed page.
 */
export const AppShell: React.FC<AppShellProps> = ({
  children,
  activePage,
  onNavigate,
  selectedPatientId,
  onSelectPatient,
  activePatient,
}) => {
  return (
    <div className="app-shell-root">
      {/* Top Header Bar */}
      <header className="app-header" role="banner">
        <div className="header-left">
          <div className="brand-logo" onClick={() => onNavigate("dashboard")} role="button" tabIndex={0}>
            <div className="brand-icon-wrap">
              <ShieldCheck size={24} className="text-teal-400" aria-hidden="true" />
            </div>
            <div>
              <h1 className="brand-title">
                Omni<span className="text-teal-400">Pharma</span>
              </h1>
              <span className="brand-subtitle">Clinical Decision Support</span>
            </div>
          </div>

          <nav className="header-nav" aria-label="Main Navigation">
            <button
              type="button"
              className={`nav-tab ${activePage === "dashboard" ? "nav-tab-active" : ""}`}
              onClick={() => onNavigate("dashboard")}
            >
              <LayoutDashboard size={16} aria-hidden="true" />
              <span>Dashboard</span>
            </button>

            <button
              type="button"
              className={`nav-tab ${activePage === "patient-review" ? "nav-tab-active" : ""}`}
              onClick={() => onNavigate("patient-review")}
            >
              <UserCheck size={16} aria-hidden="true" />
              <span>Patient Profile</span>
            </button>

            <button
              type="button"
              className={`nav-tab ${activePage === "safety-review" ? "nav-tab-active" : ""}`}
              onClick={() => onNavigate("safety-review")}
            >
              <ShieldAlert size={16} aria-hidden="true" />
              <span>Safety Review</span>
            </button>

            <button
              type="button"
              className={`nav-tab ${activePage === "alternatives" ? "nav-tab-active" : ""}`}
              onClick={() => onNavigate("alternatives")}
            >
              <Sparkles size={16} aria-hidden="true" />
              <span>Alternative Medicines</span>
            </button>

            <button
              type="button"
              className={`nav-tab ${activePage === "drug-details" ? "nav-tab-active" : ""}`}
              onClick={() => onNavigate("drug-details")}
            >
              <Pill size={16} aria-hidden="true" />
              <span>Catalogue</span>
            </button>
          </nav>
        </div>

        <div className="header-right">
          <PatientSelector
            selectedPatientId={selectedPatientId}
            onSelect={onSelectPatient}
          />
        </div>
      </header>

      {/* Patient Context Sticky Subheader Bar */}
      {activePatient && (
        <aside className="patient-context-bar" aria-label="Active Patient Context">
          <div className="context-bar-inner">
            <PatientSummary patient={activePatient} compact />
          </div>
        </aside>
      )}

      {/* Routed Page Body Wrapped in Shell Error Boundary */}
      <main className="app-main-content" role="main">
        <ShellErrorBoundary>{children}</ShellErrorBoundary>
      </main>
    </div>
  );
};
