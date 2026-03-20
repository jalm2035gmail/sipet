from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from sqlalchemy.orm import joinedload, subqueryload

from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyAssignment,
    SurveyInstance,
    SurveyResponse,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
    _dt,
    _evaluation_360_dict,
    _instance_dict,
    get_db,
    list_results,
)


def _response_table_row(response: SurveyResponse) -> Dict[str, Any]:
    return {
        "response_id": response.id,
        "assignment_id": response.assignment_id,
        "respondent_key": response.respondent_key,
        "respondent_name": response.respondent_name_snapshot or "Sin identificar",
        "role": response.respondent_role_snapshot or "",
        "department": response.respondent_area_snapshot or "",
        "position": response.respondent_position_snapshot or "",
        "company": response.respondent_company_snapshot or "",
        "channel": response.submission_channel,
        "status": response.status,
        "completion_pct": response.completion_pct,
        "total_score": response.total_score,
        "started_at": _dt(response.started_at),
        "submitted_at": _dt(response.submitted_at),
        "last_saved_at": _dt(response.last_saved_at),
        "answers_json": response.answers_json or {},
        "metrics_json": response.metrics_json or {},
    }


_CHOICE_TYPES = {
    "single_choice", "live_poll_single_choice", "multiple_choice", "yes_no", "true_false",
    "quiz_single_choice", "scale_1_5", "live_scale_1_5", "nps_0_10", "dropdown", "image_choice",
}


def _question_report(instance: SurveyInstance, responses: List[SurveyResponse]) -> List[Dict[str, Any]]:
    # Flatten all response items into a DataFrame for vectorized aggregations
    records = []
    for response in responses:
        for item in response.items or []:
            records.append({
                "response_id": item.response_id,
                "question_id": item.question_id,
                "answer_value": str(item.answer_value or ""),
                "answer_text": str(item.answer_text or ""),
                "answer_json": item.answer_json or {},
                "score_value": float(item.score_value) if item.score_value is not None else None,
                "item_index": item.item_index,
            })

    if records:
        items_df = pd.DataFrame(records)
        # Per-question: unique respondents count and avg score
        agg_by_qid = (
            items_df.groupby("question_id")
            .agg(responses_count=("response_id", "nunique"), avg_score=("score_value", "mean"))
            .to_dict("index")
        )
        # Option counts: groupby (question_id, answer_value)
        option_counts_by_qid: Dict[int, Dict[str, int]] = {}
        ov = items_df[items_df["answer_value"].str.strip() != ""]
        for (qid, val), cnt in ov.groupby(["question_id", "answer_value"]).size().items():
            option_counts_by_qid.setdefault(int(qid), {})[str(val)] = int(cnt)
        # Items grouped by question_id for text/ranking/word_cloud processing
        items_by_qid: Dict[int, pd.DataFrame] = {qid: grp for qid, grp in items_df.groupby("question_id")}
    else:
        agg_by_qid = {}
        option_counts_by_qid = {}
        items_by_qid = {}

    report: List[Dict[str, Any]] = []
    for section in instance.sections or []:
        for question in section.questions or []:
            qid = question.id
            agg = agg_by_qid.get(qid)
            entry: Dict[str, Any] = {
                "question_id": qid,
                "section_id": section.id,
                "section_title": section.titulo,
                "question_title": question.titulo,
                "question_type": question.question_type,
                "responses_count": int(agg["responses_count"]) if agg else 0,
                "avg_score": round(float(agg["avg_score"]), 2) if agg and pd.notna(agg["avg_score"]) else None,
                "options": [],
                "sample_answers": [],
            }
            qtype = question.question_type
            q_df = items_by_qid.get(qid, pd.DataFrame())
            counts_map = option_counts_by_qid.get(qid, {})

            if qtype in _CHOICE_TYPES:
                entry["options"] = [
                    {"value": opt.value, "label": opt.label, "count": counts_map.get(str(opt.value), 0)}
                    for opt in (question.options or [])
                ]
            elif qtype == "ranking":
                samples = []
                if not q_df.empty:
                    for _resp_id, grp in q_df.groupby("response_id"):
                        ranked = grp.sort_values("item_index").apply(
                            lambda r: str(r["answer_text"] or r["answer_value"]).strip(), axis=1
                        ).tolist()
                        text = " > ".join(v for v in ranked if v)
                        if text:
                            samples.append(text)
                        if len(samples) >= 5:
                            break
                entry["sample_answers"] = samples
            elif qtype in {"matrix", "likert_scale", "semantic_differential"}:
                if not q_df.empty:
                    entry["sample_answers"] = (
                        q_df["answer_text"].loc[q_df["answer_text"].str.strip() != ""].head(5).tolist()
                    )
            elif qtype == "word_cloud":
                if not q_df.empty:
                    texts = q_df.apply(
                        lambda r: str(r["answer_text"] or r["answer_value"]).strip(), axis=1
                    ).loc[lambda s: s != ""]
                    tokens = (
                        texts.str.lower()
                        .str.replace(r"[,.]", " ", regex=True)
                        .str.split()
                        .explode()
                        .loc[lambda s: s.str.len() >= 2]
                    )
                    cloud_df = (
                        tokens.value_counts()
                        .rename_axis("token")
                        .reset_index(name="count")
                        .sort_values(["count", "token"], ascending=[False, True])
                        .head(20)
                    )
                    entry["word_cloud"] = cloud_df.to_dict("records")
                    entry["sample_answers"] = texts.head(5).tolist()
                else:
                    entry["word_cloud"] = []
            else:
                if not q_df.empty:
                    if qtype == "file_upload":
                        entry["sample_answers"] = (
                            q_df.apply(
                                lambda r: str((r["answer_json"] or {}).get("name") or r["answer_text"] or r["answer_value"]).strip(),
                                axis=1,
                            )
                            .loc[lambda s: s != ""]
                            .head(5)
                            .tolist()
                        )
                    else:
                        entry["sample_answers"] = (
                            q_df.apply(
                                lambda r: str(r["answer_text"] or r["answer_value"]).strip(), axis=1
                            )
                            .loc[lambda s: s != ""]
                            .head(5)
                            .tolist()
                        )
            report.append(entry)
    return report


def _quiz_ranking(instance: SurveyInstance) -> List[Dict[str, Any]]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_responses import (
        _best_attempt_payload,
        _quiz_settings,
    )

    quiz = _quiz_settings(instance)
    if not quiz["is_quiz"]:
        return []
    ranking: List[Dict[str, Any]] = []
    for assignment in instance.assignments or []:
        attempts = [attempt for attempt in (assignment.attempts or []) if attempt.status == "submitted"]
        best_attempt = _best_attempt_payload(attempts, quiz["attempt_strategy"])
        if not best_attempt:
            continue
        evaluation_status = (best_attempt.get("result_json") or {}).get("evaluation_status")
        ranking.append(
            {
                "assignee_key": assignment.assignee_key,
                "assignee_name": assignment.assignee_name_snapshot or assignment.assignee_key,
                "score_value": best_attempt["score_value"],
                "attempt_number": best_attempt["attempt_number"],
                "elapsed_seconds": best_attempt["elapsed_seconds"],
                "submitted_at": best_attempt["submitted_at"],
                "evaluation_status": evaluation_status,
            }
        )
    ranking.sort(
        key=lambda item: (
            -float(item.get("score_value") or 0),
            float(item.get("elapsed_seconds") or 10**9),
            item.get("assignee_name") or "",
        )
    )
    for index, item in enumerate(ranking, start=1):
        item["rank"] = index
    return ranking


def _report_360(instance: SurveyInstance) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_responses import _is_360_instance

    if not _is_360_instance(instance):
        return {"enabled": False, "links": [], "by_relationship": [], "by_competency": [], "by_evaluatee": []}
    submitted_responses = [
        response for response in (instance.responses or [])
        if response.status == "submitted" and str(response.external_entity_type or "") == "evaluation_360"
    ]
    links = [_evaluation_360_dict(row) for assignment in (instance.assignments or []) for row in (assignment.evaluations_360 or [])]
    relationship_buckets: Dict[str, Dict[str, Any]] = {}
    competency_buckets: Dict[str, Dict[str, Any]] = {}
    evaluatee_buckets: Dict[str, Dict[str, Any]] = {}
    for response in submitted_responses:
        evaluation_id = str(response.external_entity_id or "").strip()
        evaluation = next((row for row in links if str(row["id"]) == evaluation_id), None)
        if not evaluation:
            continue
        rel_key = str(evaluation.get("relationship_type") or "unknown")
        rel_bucket = relationship_buckets.setdefault(rel_key, {"relationship_type": rel_key, "responses": 0, "scores": []})
        rel_bucket["responses"] += 1
        if response.total_score is not None:
            rel_bucket["scores"].append(float(response.total_score))

        evaluatee_key = str(evaluation.get("evaluatee_key") or "unknown")
        eval_bucket = evaluatee_buckets.setdefault(
            evaluatee_key,
            {
                "evaluatee_key": evaluatee_key,
                "evaluatee_name": evaluation.get("evaluatee_name_snapshot") or evaluatee_key,
                "responses": 0,
                "scores": [],
            },
        )
        eval_bucket["responses"] += 1
        if response.total_score is not None:
            eval_bucket["scores"].append(float(response.total_score))

        for competency in (response.metrics_json or {}).get("competency_scores", {}).values():
            comp_key = str(competency.get("competency_key") or "general")
            comp_bucket = competency_buckets.setdefault(
                comp_key,
                {
                    "competency_key": comp_key,
                    "competency_label": competency.get("competency_label") or comp_key,
                    "responses": 0,
                    "scores": [],
                },
            )
            comp_bucket["responses"] += 1
            if competency.get("score_avg") is not None:
                comp_bucket["scores"].append(float(competency["score_avg"]))
    return {
        "enabled": True,
        "links": links,
        "by_relationship": [
            {
                "relationship_type": key,
                "responses": payload["responses"],
                "score_avg": round(sum(payload["scores"]) / len(payload["scores"]), 2) if payload["scores"] else None,
            }
            for key, payload in sorted(relationship_buckets.items())
        ],
        "by_competency": [
            {
                "competency_key": key,
                "competency_label": payload["competency_label"],
                "responses": payload["responses"],
                "score_avg": round(sum(payload["scores"]) / len(payload["scores"]), 2) if payload["scores"] else None,
            }
            for key, payload in sorted(competency_buckets.items())
        ],
        "by_evaluatee": [
            {
                "evaluatee_key": key,
                "evaluatee_name": payload["evaluatee_name"],
                "responses": payload["responses"],
                "score_avg": round(sum(payload["scores"]) / len(payload["scores"]), 2) if payload["scores"] else None,
            }
            for key, payload in sorted(evaluatee_buckets.items(), key=lambda item: item[1]["evaluatee_name"])
        ],
    }


def _responses_metrics_frame(response_rows: List[Dict[str, Any]]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for row in response_rows:
        metrics = row.get("metrics_json") or {}
        records.append(
            {
                "response_id": row.get("response_id"),
                "department": row.get("department") or "Sin dato",
                "role": row.get("role") or "Sin dato",
                "company": row.get("company") or "Sin dato",
                "status": row.get("status") or "",
                "completion_pct": float(row.get("completion_pct") or 0),
                "total_score": float(row["total_score"]) if row.get("total_score") is not None else None,
                "quiz_approval_pct": float(metrics.get("quiz_approval_pct") or 0),
                "nps_score": float(metrics.get("nps_score") or 0),
                "csat_score": float(metrics.get("csat_score") or 0),
                "ces_score": float(metrics.get("ces_score") or 0),
                "evaluation_status": str(metrics.get("evaluation_status") or ""),
            }
        )
    return pd.DataFrame(
        records,
        columns=[
            "response_id",
            "department",
            "role",
            "company",
            "status",
            "completion_pct",
            "total_score",
            "quiz_approval_pct",
            "nps_score",
            "csat_score",
            "ces_score",
            "evaluation_status",
        ],
    )


def _filter_options_from_frame(frame: pd.DataFrame) -> Dict[str, List[str]]:
    if frame.empty:
        return {"departments": [], "roles": [], "companies": []}
    return {
        "departments": sorted({str(value).strip() for value in frame["department"].dropna().tolist() if str(value).strip()}),
        "roles": sorted({str(value).strip() for value in frame["role"].dropna().tolist() if str(value).strip()}),
        "companies": sorted({str(value).strip() for value in frame["company"].dropna().tolist() if str(value).strip()}),
    }


def _apply_dashboard_filters(frame: pd.DataFrame, filters: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    filtered = frame.copy()
    criteria = filters or {}
    for key in ("department", "role", "company"):
        value = str(criteria.get(key) or "").strip()
        if value and not filtered.empty:
            filtered = filtered[filtered[key].fillna("Sin dato") == value]
    return filtered


def _summary_from_frame(frame: pd.DataFrame) -> Dict[str, Any]:
    if frame.empty:
        return {
            "responses_count": 0,
            "completion_pct_avg": 0,
            "total_score_avg": None,
            "quiz_approval_pct": 0,
            "approved_count": 0,
            "failed_count": 0,
            "nps_score": 0,
            "csat_score": 0,
            "ces_score": 0,
        }
    approved = int((frame["evaluation_status"] == "approved").sum()) if "evaluation_status" in frame else 0
    failed = int((frame["evaluation_status"] == "failed").sum()) if "evaluation_status" in frame else 0
    return {
        "responses_count": int(len(frame.index)),
        "completion_pct_avg": round(float(frame["completion_pct"].fillna(0).mean()), 2),
        "total_score_avg": round(float(frame["total_score"].dropna().mean()), 2) if frame["total_score"].dropna().size else None,
        "quiz_approval_pct": round(float(frame["quiz_approval_pct"].fillna(0).mean()), 2),
        "approved_count": approved,
        "failed_count": failed,
        "nps_score": round(float(frame["nps_score"].fillna(0).mean()), 2),
        "csat_score": round(float(frame["csat_score"].fillna(0).mean()), 2),
        "ces_score": round(float(frame["ces_score"].fillna(0).mean()), 2),
    }


def _segment_report_from_frame(frame: pd.DataFrame, field_name: str, label: str) -> List[Dict[str, Any]]:
    if frame.empty:
        return []
    grouped = (
        frame.assign(**{field_name: frame[field_name].fillna("Sin dato")})
        .groupby(field_name, dropna=False)
        .agg(
            responses=("response_id", "count"),
            completion_pct_avg=("completion_pct", "mean"),
            score_avg=("total_score", "mean"),
        )
        .reset_index()
        .sort_values(by=["responses", field_name], ascending=[False, True])
    )
    rows: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "segment": str(row[field_name] or "Sin dato"),
                "label": label,
                "responses": int(row["responses"]),
                "completion_pct_avg": round(float(row["completion_pct_avg"]), 2) if pd.notna(row["completion_pct_avg"]) else None,
                "score_avg": round(float(row["score_avg"]), 2) if pd.notna(row["score_avg"]) else None,
            }
        )
    return rows


def _comparison_report_from_frame(frame: pd.DataFrame, segment_by: str) -> List[Dict[str, Any]]:
    if frame.empty or segment_by not in {"department", "role", "company"}:
        return []
    grouped = (
        frame.assign(**{segment_by: frame[segment_by].fillna("Sin dato")})
        .groupby(segment_by, dropna=False)
        .agg(
            responses=("response_id", "count"),
            completion_pct_avg=("completion_pct", "mean"),
            total_score_avg=("total_score", "mean"),
            nps_score=("nps_score", "mean"),
            csat_score=("csat_score", "mean"),
            ces_score=("ces_score", "mean"),
        )
        .reset_index()
        .sort_values(by=["responses", segment_by], ascending=[False, True])
    )
    output: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        output.append(
            {
                "segment_by": segment_by,
                "segment": str(row[segment_by] or "Sin dato"),
                "responses": int(row["responses"]),
                "completion_pct_avg": round(float(row["completion_pct_avg"]), 2) if pd.notna(row["completion_pct_avg"]) else None,
                "total_score_avg": round(float(row["total_score_avg"]), 2) if pd.notna(row["total_score_avg"]) else None,
                "nps_score": round(float(row["nps_score"]), 2) if pd.notna(row["nps_score"]) else None,
                "csat_score": round(float(row["csat_score"]), 2) if pd.notna(row["csat_score"]) else None,
                "ces_score": round(float(row["ces_score"]), 2) if pd.notna(row["ces_score"]) else None,
            }
        )
    return output


def get_results_dashboard(
    instance_id: int,
    tenant_id: str,
    filters: Optional[Dict[str, str]] = None,
    segment_by: str = "department",
) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_responses import (
        _quiz_settings,
    )

    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .options(
                subqueryload(SurveyInstance.responses).joinedload(SurveyResponse.items),
                subqueryload(SurveyInstance.assignments).subqueryload(SurveyAssignment.attempts),
                subqueryload(SurveyInstance.assignments).subqueryload(SurveyAssignment.evaluations_360),
            )
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        submitted_responses = [
            response for response in (instance.responses or [])
            if response.status == "submitted"
        ]
        all_response_rows = [_response_table_row(response) for response in submitted_responses]
        metrics_frame = _responses_metrics_frame(all_response_rows)
        filtered_frame = _apply_dashboard_filters(metrics_frame, filters=filters)
        selected_ids = {int(value) for value in filtered_frame["response_id"].tolist()} if not filtered_frame.empty else set()
        filtered_responses = [response for response in submitted_responses if response.id in selected_ids] if filters else submitted_responses
        response_rows = [row for row in all_response_rows if row["response_id"] in selected_ids] if filters else all_response_rows
        general_results = list_results(instance_id, tenant_id)
        ranking = _quiz_ranking(instance)
        report_360 = _report_360(instance)
        return {
            "instance": _instance_dict(instance),
            "summary": _summary_from_frame(filtered_frame if filters else metrics_frame),
            "quiz": {
                "settings": _quiz_settings(instance),
                "ranking": ranking[:20],
            },
            "report_360": report_360,
            "question_report": _question_report(instance, filtered_responses),
            "segment_report": {
                "department": _segment_report_from_frame(filtered_frame if filters else metrics_frame, "department", "Departamento"),
                "role": _segment_report_from_frame(filtered_frame if filters else metrics_frame, "role", "Rol"),
                "company": _segment_report_from_frame(filtered_frame if filters else metrics_frame, "company", "Empresa"),
            },
            "comparison_report": _comparison_report_from_frame(filtered_frame if filters else metrics_frame, segment_by),
            "available_filters": _filter_options_from_frame(metrics_frame),
            "applied_filters": {
                "department": str((filters or {}).get("department") or "").strip(),
                "role": str((filters or {}).get("role") or "").strip(),
                "company": str((filters or {}).get("company") or "").strip(),
                "segment_by": segment_by,
            },
            "responses_table": response_rows,
            "results": general_results,
        }
    finally:
        db.close()
