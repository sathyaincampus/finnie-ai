"""
Finnie AI — Phoenix Evaluation Pipeline

Runs LLM-as-judge evaluations on every chat response and logs results
back to Phoenix for dashboard visualization.

Uses Gemini Flash as the judge model (free tier).

Evaluates ALL available Phoenix metrics:
- Relevance:        Does the response address the user's question?
- Hallucination:    Is the response grounded (not fabricating facts)?
- QA Quality:       Is the response correct and helpful?
- Toxicity:         Is the response free of harmful content?
- Summarization:    Quality of any summarized content
- Human vs AI:      Does the response feel natural?
- User Frustration: Would the user be frustrated by this response?
- RAG Relevancy:    Is the retrieved context relevant?

Results appear in Phoenix under "Evaluations" for each trace span.
"""

from __future__ import annotations

import os
import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


def _get_eval_model():
    """Get the LLM judge model — prefers Gemini (free), falls back to OpenAI."""
    # Load .env so we can find API keys
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Also try to get from Streamlit session state
    google_key = os.getenv("GOOGLE_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if not google_key:
        try:
            import streamlit as st
            google_key = st.session_state.get("llm_api_key", "") if st.session_state.get("llm_provider") == "google" else ""
        except Exception:
            pass

    if not openai_key:
        try:
            import streamlit as st
            openai_key = st.session_state.get("llm_api_key", "") if st.session_state.get("llm_provider") == "openai" else ""
        except Exception:
            pass

    if google_key:
        try:
            from phoenix.evals import GoogleGenAIModel
            return GoogleGenAIModel(
                model="gemini-2.0-flash",
                api_key=google_key,
            )
        except Exception:
            pass

    if openai_key:
        try:
            from phoenix.evals import OpenAIModel
            return OpenAIModel(model="gpt-4o-mini", api_key=openai_key)
        except Exception:
            pass

    return None


def run_evals_on_response(
    user_input: str,
    response: str,
    span_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> dict:
    """
    Run ALL Phoenix LLM-as-judge evaluations on a single response.

    Uses Gemini Flash as judge (free tier). Falls back to GPT-4o-mini.
    Evaluates: relevance, hallucination, QA, toxicity, summarization,
    human vs AI, user frustration, RAG relevancy.

    Automatically finds the most recent span in Phoenix to attach results.
    """
    if os.getenv("PHOENIX_ENABLED", "true").lower() != "true":
        return {}

    eval_model = _get_eval_model()
    if not eval_model:
        logger.debug("No eval model available (set GOOGLE_API_KEY or OPENAI_API_KEY)")
        return {}

    try:
        from phoenix.evals import (
            HallucinationEvaluator,
            QAEvaluator,
            RelevanceEvaluator,
            ToxicityEvaluator,
        )
    except ImportError:
        return {}

    # If no span_id provided, try to find the most recent span in Phoenix
    if not span_id:
        span_id = _find_latest_span_id()

    eval_results = {}

    # Build the record dict that evaluators expect
    record = {
        "input": user_input,
        "output": response,
        "reference": user_input,  # use input as reference context
    }

    # ── Built-in evaluators ──────────────────────────────────────
    evaluators = {
        "Relevance": RelevanceEvaluator,
        "QA Quality": QAEvaluator,
        "Toxicity": ToxicityEvaluator,
        "Hallucination": HallucinationEvaluator,
    }

    for name, evaluator_class in evaluators.items():
        try:
            evaluator = evaluator_class(eval_model)
            label, score, explanation = evaluator.evaluate(
                record, provide_explanation=True
            )
            eval_results[name] = {
                "score": score if score is not None else 0,
                "label": label or "",
                "explanation": explanation or "",
            }
        except Exception as e:
            logger.debug(f"{name} eval failed: {e}")

    # ── Log to Phoenix ───────────────────────────────────────────
    if span_id and eval_results:
        _log_evals_to_phoenix(eval_results, span_id)
        logger.info(f"Logged {len(eval_results)} evals to span {span_id}")

    return eval_results


def _find_latest_span_id() -> Optional[str]:
    """Find the most recent span ID from Phoenix to attach evaluations to."""
    try:
        import phoenix as px
        import time

        client = px.Client()

        # Retry with increasing delays — span may not be flushed yet
        for attempt in range(3):
            time.sleep(3 + attempt * 2)  # 3s, 5s, 7s

            try:
                spans_df = client.get_spans_dataframe(limit=1)
                if spans_df is not None and not spans_df.empty:
                    span_id = str(spans_df.index[0])
                    logger.info(f"Found span {span_id} on attempt {attempt + 1}")
                    return span_id
            except Exception:
                continue

    except Exception as e:
        logger.warning(f"Could not find latest span: {e}")

    return None


def run_evals_on_traces():
    """
    Run batch evaluations on ALL recent Phoenix traces.

    Fetches spans from Phoenix, runs every evaluator, and logs results
    back so they appear on the dashboard. Uses Gemini as judge.
    """
    try:
        import phoenix as px
        from phoenix.evals import (
            HallucinationEvaluator,
            QAEvaluator,
            RelevanceEvaluator,
            ToxicityEvaluator,
            SummarizationEvaluator,
            LLMEvaluator,
            HUMAN_VS_AI_PROMPT_TEMPLATE,
            USER_FRUSTRATION_PROMPT_TEMPLATE,
            RAG_RELEVANCY_PROMPT_TEMPLATE,
            run_evals,
        )
        from phoenix.trace import SpanEvaluations
    except ImportError:
        logger.info("Phoenix evals not available — install arize-phoenix")
        return

    eval_model = _get_eval_model()
    if not eval_model:
        logger.info("No eval model — set GOOGLE_API_KEY or OPENAI_API_KEY")
        return

    try:
        client = px.Client()

        # Get recent spans
        spans_df = client.get_spans_dataframe()
        if spans_df is None or spans_df.empty:
            logger.info("No spans to evaluate")
            return

        # Define all evaluators
        evaluator_configs = [
            ("Relevance", RelevanceEvaluator(eval_model)),
            ("QA Quality", QAEvaluator(eval_model)),
            ("Toxicity", ToxicityEvaluator(eval_model)),
            ("Hallucination", HallucinationEvaluator(eval_model)),
            ("Summarization", SummarizationEvaluator(eval_model)),
        ]

        # Template-based evaluators
        template_configs = [
            ("Human vs AI", HUMAN_VS_AI_PROMPT_TEMPLATE),
            ("User Frustration", USER_FRUSTRATION_PROMPT_TEMPLATE),
            ("RAG Relevancy", RAG_RELEVANCY_PROMPT_TEMPLATE),
        ]
        for name, template in template_configs:
            evaluator_configs.append((name, LLMEvaluator(eval_model, template)))

        # Run each evaluator and log results
        for eval_name, evaluator in evaluator_configs:
            try:
                results = run_evals(
                    dataframe=spans_df,
                    evaluators=[evaluator],
                    provide_explanation=True,
                )
                if results is not None and len(results) > 0:
                    client.log_evaluations(
                        SpanEvaluations(eval_name=eval_name, dataframe=results[0])
                    )
                    logger.info(f"  ✅ {eval_name}: {len(results[0])} spans evaluated")
            except Exception as e:
                logger.warning(f"  ❌ {eval_name} failed: {e}")

        logger.info(f"Batch evals completed on {len(spans_df)} spans")

    except Exception as e:
        logger.warning(f"Batch eval error: {e}")


def _log_evals_to_phoenix(
    eval_results: dict,
    span_id: str,
):
    """Log evaluation results to Phoenix as annotations on the span."""
    if not eval_results or not span_id:
        return

    try:
        import phoenix as px
        from phoenix.trace import SpanEvaluations

        client = px.Client()

        for eval_name, result in eval_results.items():
            eval_df = pd.DataFrame([{
                "context.span_id": span_id,
                "score": result.get("score", 0),
                "label": result.get("label", ""),
                "explanation": result.get("explanation", ""),
            }]).set_index("context.span_id")

            client.log_evaluations(
                SpanEvaluations(eval_name=eval_name, dataframe=eval_df)
            )

    except Exception as e:
        logger.debug(f"Failed to log evals to Phoenix: {e}")
