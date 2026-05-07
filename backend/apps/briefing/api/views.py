"""
DRF views da API pública de briefing.

Endpoints sem autenticação — protegidos por token público (UUID).
Frontend Next.js consome.

Engines (discovery, signals, profiling, synthesis) ainda não existem.
Esta versão da API faz o BÁSICO funcional para destravar frontend:
    - Cria sessão e retorna primeira pergunta (na ordem do banco).
    - Aceita resposta e avança para próxima pergunta.
    - Conclui sessão sem síntese real ainda.

Quando engines forem implementadas, refatoramos para chamar:
    apps.discovery_engine.proximo_passo(...)
    apps.signals_engine.extrair(...)
    apps.profiling.calcular_perfil(...)
    apps.synthesis.gerar_devolutiva(...)
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.briefing.models import (
    BriefingSessao,
    EventoBriefing,
    RespostaPergunta,
    StatusBriefing,
    TipoEventoBriefing,
)
from apps.methodology.models import Pergunta, RoteiroIdentidade

from .serializers import (
    AtualizarIdentificacaoSerializer,
    BriefingSessaoSerializer,
    EstadoBriefingSerializer,
    IniciarBriefingInputSerializer,
    ResponderInputSerializer,
)

# =============================================================================
#  Helpers
# =============================================================================


def _construir_estado(sessao: BriefingSessao) -> dict[str, Any]:
    """Monta o snapshot retornado em /iniciar e /estado."""
    versao = sessao.roteiro_versao
    perguntas_qs = (
        Pergunta.objects.filter(ato__versao=versao)
        .select_related("ato")
        .prefetch_related("opcoes")
        .order_by("ato__ordem", "ordem")
    )

    total_visiveis = perguntas_qs.count()

    # IDs já respondidos (qualquer versão de resposta)
    respondidas_ids = set(
        RespostaPergunta.objects.filter(sessao=sessao).values_list("pergunta_id", flat=True)
    )
    total_respondidas = len(respondidas_ids)

    # Próxima pergunta = primeira que ainda não tem resposta
    proxima = next(
        (p for p in perguntas_qs if p.id not in respondidas_ids),
        None,
    )
    concluido = proxima is None

    ato_atual = proxima.ato if proxima else None

    payload = {
        "sessao": sessao,
        "ato_atual": ato_atual,
        "proxima_pergunta": proxima,
        "concluido": concluido,
        "total_perguntas_visiveis": total_visiveis,
        "total_respondidas": total_respondidas,
    }
    return EstadoBriefingSerializer(payload).data


# =============================================================================
#  Views
# =============================================================================


class IniciarBriefingView(APIView):
    """
    POST /api/v1/briefing/iniciar/

    Cria nova sessão de briefing.
    Retorna token público + primeiro estado.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = IniciarBriefingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        identidade = RoteiroIdentidade.objects.get(slug=data["roteiro_slug"])
        versao = identidade.versao_publicada or identidade.versao_em_draft

        sessao = BriefingSessao.objects.create(
            roteiro_versao=versao,
            origem=data.get("origem", ""),
            nome_empresa=data.get("nome_empresa", ""),
            nome_respondente=data.get("nome_respondente", ""),
            email_respondente=data.get("email_respondente", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:400],
            ip_address=_extract_ip(request),
        )

        EventoBriefing.registrar(
            sessao,
            TipoEventoBriefing.SESSAO_INICIADA,
            roteiro_slug=data["roteiro_slug"],
            roteiro_versao=versao.version,
        )

        return Response(_construir_estado(sessao), status=status.HTTP_201_CREATED)


class EstadoBriefingView(APIView):
    """
    GET /api/v1/briefing/{token}/estado/

    Retorna estado atual + próxima pergunta. Usado pelo frontend para
    refresh, retomada de sessão, etc.
    """

    permission_classes = [AllowAny]

    def get(self, request: Any, token: str, *args: Any, **kwargs: Any) -> Response:
        sessao = get_object_or_404(BriefingSessao, token=token)
        return Response(_construir_estado(sessao))


class ResponderView(APIView):
    """
    POST /api/v1/briefing/{token}/responder/

    Submete resposta a uma pergunta. Cria nova versão se já existir resposta
    anterior. Avança para próxima pergunta.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request: Any, token: str, *args: Any, **kwargs: Any) -> Response:
        sessao = get_object_or_404(BriefingSessao, token=token)

        if sessao.status == StatusBriefing.CONCLUIDA:
            return Response(
                {"detail": "Briefing já concluído. Não aceita novas respostas."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ResponderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pergunta = get_object_or_404(
            Pergunta,
            ato__versao=sessao.roteiro_versao,
            codigo=data["pergunta_codigo"],
        )

        proxima_versao = RespostaPergunta.proxima_versao(sessao, pergunta)

        resposta = RespostaPergunta.objects.create(
            sessao=sessao,
            pergunta=pergunta,
            valor=data.get("valor"),
            pulada=data.get("pulada", False),
            versao=proxima_versao,
            tempo_ate_responder_ms=data.get("tempo_ate_responder_ms"),
        )

        # Auto-promote: iniciada -> em_andamento na primeira resposta
        sessao.marcar_em_andamento()

        EventoBriefing.registrar(
            sessao,
            TipoEventoBriefing.PERGUNTA_PULADA
            if resposta.pulada
            else TipoEventoBriefing.PERGUNTA_RESPONDIDA,
            pergunta_codigo=pergunta.codigo,
            versao_resposta=proxima_versao,
        )

        # TODO(Frente C): chamar engine de sinais aqui para extrair sinais
        # da resposta e persistir em SinalCapturado.

        return Response(_construir_estado(sessao))


class ConcluirView(APIView):
    """
    POST /api/v1/briefing/{token}/concluir/

    Marca sessão como concluída. Aciona engine de síntese (futuro).
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request: Any, token: str, *args: Any, **kwargs: Any) -> Response:
        sessao = get_object_or_404(BriefingSessao, token=token)

        if sessao.status == StatusBriefing.CONCLUIDA:
            return Response(BriefingSessaoSerializer(sessao).data)

        # TODO(Frente C): chamar apps.synthesis.gerar_devolutiva(sessao)
        # Por enquanto, devolutiva placeholder mostra que infraestrutura funciona.
        devolutiva_placeholder = {
            "status": "preliminar",
            "mensagem": (
                "Devolutiva ainda em construção — a engine de síntese "
                "será implementada na próxima frente."
            ),
            "sinais_capturados": sessao.sinais_por_chave(),
            "respostas_recebidas": sessao.total_perguntas_respondidas,
        }
        sessao.concluir(devolutiva_json=devolutiva_placeholder)

        EventoBriefing.registrar(
            sessao,
            TipoEventoBriefing.SESSAO_CONCLUIDA,
            total_respostas=sessao.total_perguntas_respondidas,
        )

        return Response(BriefingSessaoSerializer(sessao).data)


class DevolutivaView(APIView):
    """
    GET /api/v1/briefing/{token}/devolutiva/

    Retorna devolutiva da sessão (após concluir).
    """

    permission_classes = [AllowAny]

    def get(self, request: Any, token: str, *args: Any, **kwargs: Any) -> Response:
        sessao = get_object_or_404(BriefingSessao, token=token)

        if sessao.status != StatusBriefing.CONCLUIDA:
            return Response(
                {
                    "detail": "Devolutiva ainda não disponível. Conclua o briefing primeiro.",
                    "status_atual": sessao.status,
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "sessao": BriefingSessaoSerializer(sessao).data,
                "devolutiva": sessao.devolutiva_json or {},
            }
        )


class IdentificarView(APIView):
    """
    PATCH /api/v1/briefing/{token}/identificar/

    Atualiza nome/empresa/email da sessão (durante o fluxo).
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def patch(self, request: Any, token: str, *args: Any, **kwargs: Any) -> Response:
        sessao = get_object_or_404(BriefingSessao, token=token)

        if sessao.status == StatusBriefing.CONCLUIDA:
            return Response(
                {"detail": "Briefing concluído não aceita atualização de identificação."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = AtualizarIdentificacaoSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for campo, valor in data.items():
            setattr(sessao, campo, valor)
        sessao.save()
        sessao.tocar_atividade()

        return Response(BriefingSessaoSerializer(sessao).data)


# =============================================================================
#  Util
# =============================================================================


def _extract_ip(request: Any) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
