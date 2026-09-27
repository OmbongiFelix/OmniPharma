"""LLM-facing agent wrapper.

Converts a list of structured `SafetyFinding` objects into a concise,
pharmacist-facing prose explanation. This module must not invent safety
facts, change a severity, add an interaction that isn't in the input
findings, or suggest a prescription — it summarizes what the
deterministic layer already decided.

Imports/dependencies: an LLM SDK (provider-agnostic via
`app.core.config.Settings.llm_provider`), app.schemas.screening,
app.agents.prompts.

Public outputs: `PharmacistAgent` (see below).
"""

import json
import logging

from app.agents.prompts import build_explanation_prompt
from app.core.config import get_settings
from app.schemas.screening import SafetyFinding

logger = logging.getLogger(__name__)


class PharmacistAgent:
    """Summarizes structured safety findings into pharmacist-readable prose.

    Attributes:
        client: The configured LLM SDK client. `None` when no provider
            is configured; in that case `explain()` returns `None`
            immediately rather than raising, so callers do not need to
            branch on configuration state.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.client = None
        self._provider = settings.llm_provider

        if self._provider == "openai":
            try:
                import openai  # type: ignore[import]

                self.client = openai.OpenAI(api_key=settings.llm_api_key)
                self._model = "gpt-4o-mini"
            except ImportError:
                logger.warning(
                    "openai package not installed; PharmacistAgent will return explanation=None."
                )
        elif self._provider == "google":
            try:
                import google.generativeai as genai  # type: ignore[import]

                genai.configure(api_key=settings.llm_api_key)
                self.client = genai
                self._model = "gemini-2.0-flash"
            except ImportError:
                logger.warning(
                    "google-generativeai package not installed; explanation=None."
                )
        elif self._provider is not None:
            logger.warning(
                "Unknown LLM_PROVIDER '%s'; PharmacistAgent will return explanation=None.",
                self._provider,
            )

    def explain(self, findings: list[SafetyFinding], patient_name: str = "the patient") -> str | None:
        """Produce a short natural-language explanation of findings.

        Args:
            findings: Structured findings already produced by the
                deterministic rule engine, in final severity order.
            patient_name: Patient display name for personalising the
                explanation; not logged or stored.

        Returns:
            A concise explanation string, or `None` if no LLM provider
            is configured or the call fails for any reason (timeout,
            malformed response, provider error). A `None` return is not
            an error state for the caller — the orchestrator always has
            a complete deterministic result regardless.

        Raises:
            This method intentionally raises nothing. Every failure mode
            degrades to `None` so a flaky LLM provider can never block a
            safety-critical response.

        Notes:
            The prompt built from `app.agents.prompts` explicitly
            instructs the model to restate only what is present in
            `findings` and never to add a new interaction, drug, or
            severity level.
        """
        if self.client is None or not findings:
            return None

        try:
            findings_json = json.dumps(
                [f.model_dump() for f in findings], indent=2, default=str
            )
            system_prompt, user_prompt = build_explanation_prompt(findings_json, patient_name)

            if self._provider == "openai":
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=512,
                    temperature=0.0,
                )
                return response.choices[0].message.content

            if self._provider == "google":
                model_obj = self.client.GenerativeModel(
                    self._model,
                    system_instruction=system_prompt,
                )
                response = model_obj.generate_content(user_prompt)
                return response.text

        except Exception as exc:  # noqa: BLE001
            logger.warning("PharmacistAgent.explain() failed: %s", exc)
            return None

        return None
