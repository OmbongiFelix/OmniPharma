import React, { useState, useEffect, useRef } from "react";
import { searchMedications } from "../api/medications";
import type { DrugSummary } from "../types/medication";
import { Search, Pill, Building2, X } from "lucide-react";
import { LoadingState } from "./LoadingState";

export interface DrugSearchProps {
  /** Called with the chosen drug's catalogue id. */
  onSelect: (drugId: number, drugName?: string) => void;
  /** Optional placeholder text. */
  placeholder?: string;
  /** Optional auto-clear on selection. Defaults to true. */
  clearOnSelect?: boolean;
}

/**
 * Autocomplete search box over `GET /api/v1/medications/search`.
 * Debounces input and shows {@link LoadingState} inline while a search
 * is in flight.
 *
 * @param props - {@link DrugSearchProps}
 */
export const DrugSearch: React.FC<DrugSearchProps> = ({
  onSelect,
  placeholder = "Search catalogue by INN, brand name, or active ingredient...",
  clearOnSelect = true,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [results, setResults] = useState<DrugSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Debounced search
  useEffect(() => {
    const trimmed = searchTerm.trim();
    if (!trimmed) {
      setResults([]);
      setIsLoading(false);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setIsOpen(true);

    const timer = setTimeout(async () => {
      try {
        const data = await searchMedications(trimmed);
        setResults(data || []);
      } catch (err) {
        setErrorMsg("Failed to query drug catalogue.");
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSelect = (drug: DrugSummary) => {
    onSelect(drug.id, drug.canonicalName);
    if (clearOnSelect) {
      setSearchTerm("");
    } else {
      setSearchTerm(drug.canonicalName);
    }
    setIsOpen(false);
  };

  return (
    <div className="drug-search-container" ref={containerRef}>
      <div className="drug-search-input-box">
        <Search size={18} className="search-icon" aria-hidden="true" />
        <input
          type="text"
          className="drug-search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder={placeholder}
          aria-label="Search drug catalogue"
          autoComplete="off"
        />
        {searchTerm && (
          <button
            type="button"
            className="clear-search-btn"
            onClick={() => {
              setSearchTerm("");
              setResults([]);
              setIsOpen(false);
            }}
            aria-label="Clear search input"
          >
            <X size={16} aria-hidden="true" />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="drug-search-dropdown" role="listbox">
          {isLoading && (
            <div className="dropdown-loading-box">
              <LoadingState size="sm" message="Querying catalogue..." />
            </div>
          )}

          {!isLoading && errorMsg && (
            <div className="dropdown-message-box text-rose-600">{errorMsg}</div>
          )}

          {!isLoading && !errorMsg && results.length === 0 && searchTerm.trim() && (
            <div className="dropdown-message-box text-slate-500">
              No matching drugs found in catalogue for "{searchTerm}".
            </div>
          )}

          {!isLoading &&
            results.map((drug) => (
              <div
                key={drug.id}
                role="option"
                aria-selected={false}
                className="dropdown-item"
                onClick={() => handleSelect(drug)}
              >
                <div className="item-icon-box">
                  <Pill size={16} className="text-teal-600" aria-hidden="true" />
                </div>
                <div className="item-info">
                  <div className="item-title-row">
                    <span className="item-canonical-name">{drug.canonicalName}</span>
                    {drug.strength && (
                      <span className="item-strength-badge">{drug.strength}</span>
                    )}
                  </div>
                  <div className="item-subtitle-row">
                    {drug.tradeName && (
                      <span className="item-trade-name">Brand: {drug.tradeName}</span>
                    )}
                    {drug.dosageForm && (
                      <span className="item-form">• {drug.dosageForm}</span>
                    )}
                    {drug.source && (
                      <span className="item-source">
                        <Building2 size={11} className="inline mr-0.5" />
                        {drug.source}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};
