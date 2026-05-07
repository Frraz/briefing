"""URLs da API pública de briefing."""

from django.urls import path

from .views import (
    ConcluirView,
    DevolutivaView,
    EstadoBriefingView,
    IdentificarView,
    IniciarBriefingView,
    ResponderView,
)

app_name = "briefing_api"

urlpatterns = [
    path("iniciar/", IniciarBriefingView.as_view(), name="iniciar"),
    path("<str:token>/estado/", EstadoBriefingView.as_view(), name="estado"),
    path("<str:token>/responder/", ResponderView.as_view(), name="responder"),
    path("<str:token>/concluir/", ConcluirView.as_view(), name="concluir"),
    path("<str:token>/devolutiva/", DevolutivaView.as_view(), name="devolutiva"),
    path("<str:token>/identificar/", IdentificarView.as_view(), name="identificar"),
]
