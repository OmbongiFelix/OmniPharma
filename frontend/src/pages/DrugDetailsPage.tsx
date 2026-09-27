import React, { useState, useEffect } from "react";
import type { DrugDetail } from "../types/medication";
import type { PageId } from "../components/AppShell";
import { getMedicationDetail } from "../api/medications";
import { DrugSearch } from "../components/DrugSearch";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import {
  Pill,
  Building2,
  Package,
  Layers,
  ArrowRight,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export interface DrugDetailsPageProps {
  /** Initial medication ID if preselected. */
  initialDrugId?: number | null;
  /** Navigation callback to switch screens. */
  onNavigate: (page: PageId) => void;
  /** Callback to add drug to active safety review regimen. */
  onAddDrugToReview?: (drugName: string) => void;
}

/**
 * Drug Details Screen:
 * Inspects canonical drug entries from the local pharmacy catalogue,
 * including INN, registered trade names, dosage form, strength,
 * provenance registration source, and inventory warehouse status.
 *
 * @param props - {@link DrugDetailsPageProps}
 */
export const DrugDetailsPage: React.FC<DrugDetailsPageProps> = ({
  initialDrugId = 1,
  onNavigate,
  onAddDrugToReview,
}) => {
  const [selectedDrugId, setSelectedDrugId] = useState<number | null>(initialDrugId || 1);
  const [drugDetail, setDrugDetail] = useState<DrugDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!selectedDrugId) return;

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getMedicationDetail(selectedDrugId)
      .then((data) => {
        if (!cancelled) {
          setDrugDetail(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedDrugId]);

  const handleSelectDrugFromSearch = (drugId: number) => {
    setSelectedDrugId(drugId);
  };

  const handleAddToReview = () => {
    if (drugDetail && onAddDrugToReview) {
      onAddDrugToReview(drugDetail.canonicalName);
      onNavigate("safety-review");
    }
  };

  return (
    <div className="drug-details-page-container" aria-label="Drug Catalogue Details">
      {/* Header and Search Autocomplete */}
      <div className="drug-details-header">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Drug Catalogue & Provenance</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Search verified pharmacy catalogue entries, active ingredients, and local facility inventory.
          </p>
        </div>

        <div className="w-full md:w-80">
          <DrugSearch
            onSelect={handleSelectDrugFromSearch}
            placeholder="Search catalogue..."
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="page-loading-box mt-6">
          <LoadingState size="lg" message="Loading drug catalogue specification and inventory status..." />
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <div className="mt-6">
          <ErrorState
            message="Failed to retrieve catalogue medication details."
            detail={error.message}
            retry={() => setSelectedDrugId(selectedDrugId)}
          />
        </div>
      )}

      {/* Drug Specification Profile Card */}
      {!isLoading && drugDetail && (
        <div className="drug-spec-card mt-6 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
                <Pill size={24} aria-hidden="true" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900 capitalize">
                    {drugDetail.canonicalName}
                  </h3>
                  {drugDetail.strength && (
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                      {drugDetail.strength}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                  <span>Catalogue ID: #{drugDetail.id}</span>
                  {drugDetail.inn && <span>• INN: {drugDetail.inn}</span>}
                </div>
              </div>
            </div>

            {onAddDrugToReview && (
              <button
                type="button"
                className="btn-primary"
                onClick={handleAddToReview}
              >
                <span>Add to Active Safety Review</span>
                <ArrowRight size={15} aria-hidden="true" />
              </button>
            )}
          </div>

          {/* Details Specifications Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            {/* Trade Name */}
            <div className="spec-metric-box p-4 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 block mb-1">
                Registered Trade Name (Brand)
              </span>
              <span className="text-base font-bold text-slate-800">
                {drugDetail.tradeName || "Generic / Non-proprietary"}
              </span>
            </div>

            {/* Dosage Form */}
            <div className="spec-metric-box p-4 rounded-lg bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-1.5 mb-1">
                <Layers size={14} className="text-slate-500" aria-hidden="true" />
                <span className="text-xs font-semibold text-slate-500">Dosage Form</span>
              </div>
              <span className="text-base font-bold text-slate-800">
                {drugDetail.dosageForm || "Standard Oral"}
              </span>
            </div>

            {/* Provenance / Source */}
            <div className="spec-metric-box p-4 rounded-lg bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-1.5 mb-1">
                <Building2 size={14} className="text-slate-500" aria-hidden="true" />
                <span className="text-xs font-semibold text-slate-500">Catalogue Provenance</span>
              </div>
              <span className="text-base font-bold text-slate-800">
                {drugDetail.source || "PPB Kenya Pharmacopoeia"}
              </span>
            </div>
          </div>

          {/* Inventory & Supply Status */}
          <div className="inventory-status-banner mt-6 p-4 rounded-xl border flex items-center justify-between bg-slate-50/80 border-slate-200">
            <div className="flex items-center gap-3">
              <Package size={22} className={drugDetail.inStock ? "text-emerald-600" : "text-amber-600"} aria-hidden="true" />
              <div>
                <span className="text-sm font-bold text-slate-800 block">
                  Inventory & Local Facility Availability
                </span>
                <span className="text-xs text-slate-500">
                  Total aggregated units across registered hospital pharmacy storehouses:{" "}
                  <strong>{drugDetail.totalQuantity} units</strong>
                </span>
              </div>
            </div>

            <div>
              {drugDetail.inStock ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  <CheckCircle2 size={14} aria-hidden="true" />
                  In Stock & Available
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                  <XCircle size={14} aria-hidden="true" />
                  Low / Out of Stock
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
