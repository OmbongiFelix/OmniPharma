import React from "react";
import { Loader2 } from "lucide-react";

export interface LoadingStateProps {
  /** Optional context-specific text to display while loading. */
  message?: string;
  /** Size variant: "sm" | "md" | "lg". Defaults to "md". */
  size?: "sm" | "md" | "lg";
}

/**
 * Shared loading placeholder used by every data-fetching component,
 * ensuring loading UI is visually consistent across the application.
 *
 * @param props - {@link LoadingStateProps}
 * @returns Accessible spinner and message container.
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading data...",
  size = "md",
}) => {
  const spinnerSize = size === "sm" ? 18 : size === "lg" ? 36 : 24;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`loading-state-container loading-${size}`}
    >
      <Loader2
        size={spinnerSize}
        className="animate-spin text-teal-600"
        aria-hidden="true"
      />
      <span className="loading-message">{message}</span>
    </div>
  );
};
