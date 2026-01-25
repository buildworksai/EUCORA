# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store URL configuration.
"""
from django.urls import path

from . import api_views_p5_5, views

app_name = "evidence_store"

urlpatterns = [
    # Evidence pack endpoints
    path("", views.upload_evidence_pack, name="upload"),
    path("<uuid:correlation_id>/", views.get_evidence_pack, name="get"),
    # P5.5: Incident management endpoints
    path("incidents/", api_views_p5_5.list_incidents, name="list_incidents"),
    path("incidents/create/", api_views_p5_5.create_incident, name="create_incident"),
    path("incidents/<uuid:incident_id>/", api_views_p5_5.get_incident, name="get_incident"),
    path("incidents/<uuid:incident_id>/update/", api_views_p5_5.update_incident, name="update_incident"),
    # P5.5: Trust maturity endpoints
    path("maturity/status/", api_views_p5_5.get_maturity_status, name="maturity_status"),
    path("maturity/evaluate/", api_views_p5_5.evaluate_maturity_progression, name="maturity_evaluate"),
    path("maturity/evaluations/", api_views_p5_5.list_maturity_evaluations, name="maturity_evaluations"),
    # P5.5: Blast radius classification endpoints
    path("blast-radius/classify/", api_views_p5_5.classify_deployment, name="classify_deployment"),
    path("blast-radius/classes/", api_views_p5_5.list_blast_radius_classes, name="list_blast_radius_classes"),
    # P5.5: Risk model version endpoints
    path("risk-models/", api_views_p5_5.list_risk_model_versions, name="list_risk_models"),
    path("risk-models/active/", api_views_p5_5.get_active_risk_model, name="get_active_risk_model"),
    path("risk-models/<str:version>/activate/", api_views_p5_5.activate_risk_model_version, name="activate_risk_model"),
]
