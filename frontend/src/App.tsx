import { useState, useEffect } from "react";
import { AppShell, type PageId } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PatientReviewPage } from "./pages/PatientReviewPage";
import { SafetyReviewPage } from "./pages/SafetyReviewPage";
import { AlternativesPage } from "./pages/AlternativesPage";
import { DrugDetailsPage } from "./pages/DrugDetailsPage";
import { usePatients } from "./hooks/usePatients";
import { usePatientContext } from "./hooks/usePatientContext";

/**
 * Top-level application coordinator managing active screen routing,
 * selected demo patient context, and evaluated medication regimen.
 */
export function App() {
  const [activePage, setActivePage] = useState<PageId>("dashboard");
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(3); // Cynthia Wanjiku (Pregnancy demo)
  const [activeMedications, setActiveMedications] = useState<string[]>([]);
  const [targetMedicationForAlt, setTargetMedicationForAlt] = useState<string>("ibuprofen");

  const { patients } = usePatients();
  const {
    patient: activePatient,
    isLoading: isPatientLoading,
    error: patientError,
    refetch: refetchPatient,
  } = usePatientContext(selectedPatientId);

  // Sync active medications whenever the selected patient's prescriptions load or change
  useEffect(() => {
    if (activePatient && activePatient.currentPrescriptions) {
      const medNames = activePatient.currentPrescriptions.map((p) =>
        p.medicationName.toLowerCase()
      );
      // If patient is Cynthia Wanjiku (ID 3), ensure isotretinoin or lisinopril is included for demonstration if not already
      if (activePatient.id === 3 && !medNames.includes("isotretinoin")) {
        medNames.push("isotretinoin");
      }
      setActiveMedications(medNames);
    }
  }, [activePatient]);

  const handleSelectPatient = (id: number) => {
    setSelectedPatientId(id);
  };

  const handleSelectMedicationForReview = (medName: string) => {
    if (!activeMedications.some((m) => m.toLowerCase() === medName.toLowerCase())) {
      setActiveMedications([...activeMedications, medName.toLowerCase()]);
    }
    setActivePage("safety-review");
  };

  const handleAdoptAlternative = (newMed: string, replaceOldMed?: string) => {
    const trimmedNew = newMed.trim().toLowerCase();
    if (replaceOldMed) {
      const trimmedOld = replaceOldMed.trim().toLowerCase();
      setActiveMedications((prev) =>
        prev.map((m) => (m.toLowerCase() === trimmedOld ? trimmedNew : m))
      );
    } else {
      if (!activeMedications.some((m) => m.toLowerCase() === trimmedNew)) {
        setActiveMedications((prev) => [...prev, trimmedNew]);
      }
    }
    setActivePage("safety-review");
  };

  return (
    <AppShell
      activePage={activePage}
      onNavigate={setActivePage}
      selectedPatientId={selectedPatientId}
      onSelectPatient={handleSelectPatient}
      activePatient={activePatient}
    >
      {activePage === "dashboard" && (
        <DashboardPage
          patients={patients}
          selectedPatientId={selectedPatientId}
          onSelectPatient={handleSelectPatient}
          onNavigate={setActivePage}
        />
      )}

      {activePage === "patient-review" && (
        <PatientReviewPage
          patient={activePatient}
          isLoading={isPatientLoading}
          error={patientError}
          onRetry={refetchPatient}
          onNavigate={setActivePage}
          onSelectMedicationForReview={handleSelectMedicationForReview}
        />
      )}

      {activePage === "safety-review" && (
        <SafetyReviewPage
          patient={activePatient}
          medications={activeMedications}
          onUpdateMedications={setActiveMedications}
          onNavigate={setActivePage}
          onFindAlternatives={(med) => {
            setTargetMedicationForAlt(med);
            setActivePage("alternatives");
          }}
        />
      )}

      {activePage === "alternatives" && (
        <AlternativesPage
          patient={activePatient}
          targetMedication={targetMedicationForAlt}
          onSelectTargetMedication={setTargetMedicationForAlt}
          onNavigate={setActivePage}
          onAdoptAlternative={handleAdoptAlternative}
        />
      )}

      {activePage === "drug-details" && (
        <DrugDetailsPage
          onNavigate={setActivePage}
          onAddDrugToReview={(med) => {
            if (!activeMedications.some((m) => m.toLowerCase() === med.toLowerCase())) {
              setActiveMedications([...activeMedications, med.toLowerCase()]);
            }
          }}
        />
      )}
    </AppShell>
  );
}

export default App;
