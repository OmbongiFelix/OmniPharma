import React, { useState, useMemo } from "react";
import type { PrescriptionRecord, MedicationHistoryRecord } from "../types/patient";
import { Pill, ArrowUpDown, Clock, CheckCircle2, XCircle } from "lucide-react";

export interface MedicationTableProps {
  /** Current prescriptions for the patient. */
  prescriptions?: PrescriptionRecord[];
  /** Past medication history entries. */
  history?: MedicationHistoryRecord[];
  /** "current" | "history" | "both" — controls which rows render; defaults to "both". */
  mode?: "current" | "history" | "both";
  /** Optional callback when a drug is clicked to inspect details or alternatives. */
  onSelectMedication?: (medicationName: string) => void;
}

interface UnifiedMedRow {
  id: string;
  source: "current" | "history";
  medicationName: string;
  dose: string;
  frequency: string;
  route: string;
  dates: string;
  status: string;
  details: string;
}

/**
 * Renders current prescriptions and/or medication history in a single
 * sortable table, with a status column distinguishing ACTIVE, COMPLETED
 * and STOPPED entries.
 *
 * @param props.prescriptions - Current prescriptions.
 * @param props.history - Past medication history entries.
 * @param props.mode - "current" | "history" | "both" — controls which
 *   rows render; defaults to "both".
 */
export const MedicationTable: React.FC<MedicationTableProps> = ({
  prescriptions = [],
  history = [],
  mode = "both",
  onSelectMedication,
}) => {
  const [sortField, setSortField] = useState<keyof UnifiedMedRow>("medicationName");
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  // Combine rows according to mode
  const rows = useMemo(() => {
    const list: UnifiedMedRow[] = [];

    if (mode === "current" || mode === "both") {
      prescriptions.forEach((p, idx) => {
        const dateRange = p.startDate
          ? p.endDate
            ? `${p.startDate} to ${p.endDate}`
            : `Since ${p.startDate}`
          : "—";

        list.push({
          id: `curr-${p.medicationId}-${idx}`,
          source: "current",
          medicationName: p.medicationName,
          dose: p.dose || "—",
          frequency: p.frequency || "—",
          route: p.route || "oral",
          dates: dateRange,
          status: p.status || "ACTIVE",
          details: p.route ? `Route: ${p.route}` : "",
        });
      });
    }

    if (mode === "history" || mode === "both") {
      history.forEach((h, idx) => {
        const dateRange = h.startDate
          ? h.endDate
            ? `${h.startDate} to ${h.endDate}`
            : `Started ${h.startDate}`
          : "—";

        list.push({
          id: `hist-${h.medicationId}-${idx}`,
          source: "history",
          medicationName: h.medicationName,
          dose: h.dose || "—",
          frequency: h.frequency || "—",
          route: "—",
          dates: dateRange,
          status: "COMPLETED",
          details: h.outcome || h.notes || "Completed course",
        });
      });
    }

    return list.sort((a, b) => {
      const valA = String(a[sortField]).toLowerCase();
      const valB = String(b[sortField]).toLowerCase();
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [prescriptions, history, mode, sortField, sortAsc]);

  const handleSort = (field: keyof UnifiedMedRow) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const getStatusBadge = (status: string) => {
    const st = status.toUpperCase();
    if (st === "ACTIVE") {
      return (
        <span className="badge-status-active">
          <Clock size={12} className="mr-1" aria-hidden="true" />
          Active
        </span>
      );
    }
    if (st === "DISCONTINUED" || st === "STOPPED") {
      return (
        <span className="badge-status-stopped">
          <XCircle size={12} className="mr-1" aria-hidden="true" />
          Stopped
        </span>
      );
    }
    return (
      <span className="badge-status-completed">
        <CheckCircle2 size={12} className="mr-1" aria-hidden="true" />
        Completed
      </span>
    );
  };

  if (rows.length === 0) {
    return (
      <div className="empty-sublist">
        <Pill size={18} className="text-slate-400" aria-hidden="true" />
        <span>No medication records found for selected filter.</span>
      </div>
    );
  }

  return (
    <div className="table-responsive-wrapper">
      <table className="medication-table" aria-label="Patient Medications List">
        <thead>
          <tr>
            <th scope="col" onClick={() => handleSort("medicationName")} className="sortable-th">
              <span className="th-content">
                Medicine Name
                <ArrowUpDown size={13} className="ml-1 opacity-60" aria-hidden="true" />
              </span>
            </th>
            <th scope="col">Dose & Frequency</th>
            <th scope="col">Route</th>
            <th scope="col" onClick={() => handleSort("status")} className="sortable-th">
              <span className="th-content">
                Status
                <ArrowUpDown size={13} className="ml-1 opacity-60" aria-hidden="true" />
              </span>
            </th>
            <th scope="col">Timeline</th>
            <th scope="col">Clinical Notes</th>
            {onSelectMedication && <th scope="col">Action</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={row.source === "current" ? "row-current" : "row-history"}>
              <td className="font-semibold text-slate-900">
                <div className="flex items-center gap-2">
                  <Pill size={15} className={row.source === "current" ? "text-teal-600" : "text-slate-400"} aria-hidden="true" />
                  <span>{row.medicationName}</span>
                </div>
              </td>
              <td>
                <span className="font-medium text-slate-800">{row.dose}</span>
                <span className="text-xs text-slate-500 block">{row.frequency}</span>
              </td>
              <td className="text-slate-600">{row.route}</td>
              <td>{getStatusBadge(row.status)}</td>
              <td className="text-xs text-slate-600">{row.dates}</td>
              <td className="text-xs text-slate-600">{row.details || "—"}</td>
              {onSelectMedication && (
                <td>
                  <button
                    type="button"
                    onClick={() => onSelectMedication(row.medicationName)}
                    className="action-btn-sm"
                    title={`Review ${row.medicationName}`}
                  >
                    Review
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
