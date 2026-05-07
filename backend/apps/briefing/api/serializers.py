"""DRF serializers para a API pública de briefing."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.briefing.models import BriefingSessao, RespostaPergunta
from apps.methodology.models import (
    Ato,
    OpcaoDePergunta,
    Pergunta,
    RoteiroIdentidade,
)

# =============================================================================
#  Output
# =============================================================================


class OpcaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcaoDePergunta
        fields = ("codigo_interno", "ordem", "texto_publico", "descricao_publica", "icone")


class PerguntaSerializer(serializers.ModelSerializer):
    opcoes = OpcaoSerializer(many=True, read_only=True)

    class Meta:
        model = Pergunta
        fields = (
            "id",
            "codigo",
            "ordem",
            "tipo",
            "arquetipo",
            "texto_publico",
            "placeholder",
            "helper_text",
            "obrigatoria",
            "tipo_config",
            "opcoes",
        )


class AtoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ato
        fields = (
            "slug",
            "ordem",
            "titulo_publico",
            "subtitulo_publico",
            "introducao_publica",
        )


class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespostaPergunta
        fields = (
            "pergunta_codigo",
            "valor",
            "pulada",
            "versao",
            "created_at",
        )


class BriefingSessaoSerializer(serializers.ModelSerializer):
    """Visão compacta da sessão para retorno em endpoints."""

    progresso_perguntas = serializers.IntegerField(
        source="total_perguntas_respondidas", read_only=True
    )
    sinais_capturados = serializers.IntegerField(source="total_sinais_capturados", read_only=True)

    class Meta:
        model = BriefingSessao
        fields = (
            "token",
            "status",
            "perfil_calculado",
            "ato_atual",
            "nome_empresa",
            "nome_respondente",
            "email_respondente",
            "iniciada_em",
            "concluida_em",
            "ultima_atividade_em",
            "progresso_perguntas",
            "sinais_capturados",
        )
        read_only_fields = fields


class EstadoBriefingSerializer(serializers.Serializer):
    """Snapshot completo do estado atual: sessão + próxima pergunta + ato atual."""

    sessao = BriefingSessaoSerializer()
    ato_atual = AtoSerializer(allow_null=True)
    proxima_pergunta = PerguntaSerializer(allow_null=True)
    concluido = serializers.BooleanField()
    total_perguntas_visiveis = serializers.IntegerField()
    total_respondidas = serializers.IntegerField()


# =============================================================================
#  Input
# =============================================================================


class IniciarBriefingInputSerializer(serializers.Serializer):
    """Payload do POST /iniciar/."""

    roteiro_slug = serializers.SlugField(
        required=False,
        default="roteiro-universal-ferzion",
        help_text="Slug da identidade do roteiro. Default: roteiro universal.",
    )
    origem = serializers.CharField(required=False, allow_blank=True, max_length=80)
    nome_empresa = serializers.CharField(required=False, allow_blank=True, max_length=200)
    nome_respondente = serializers.CharField(required=False, allow_blank=True, max_length=160)
    email_respondente = serializers.EmailField(required=False, allow_blank=True)

    def validate_roteiro_slug(self, value: str) -> str:
        try:
            identidade = RoteiroIdentidade.objects.get(slug=value, is_active=True)
        except RoteiroIdentidade.DoesNotExist as e:
            raise serializers.ValidationError(
                f"Roteiro '{value}' não existe ou não está ativo."
            ) from e

        # Precisa ter alguma versão usável
        if not (identidade.versao_publicada or identidade.versao_em_draft):
            raise serializers.ValidationError(f"Roteiro '{value}' não tem versão disponível.")
        return value


class ResponderInputSerializer(serializers.Serializer):
    """Payload do POST /responder/."""

    pergunta_codigo = serializers.CharField(max_length=16)
    valor = serializers.JSONField(required=False, allow_null=True)
    pulada = serializers.BooleanField(default=False)
    tempo_ate_responder_ms = serializers.IntegerField(required=False, min_value=0)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs.get("pulada") and attrs.get("valor") in (None, ""):
            raise serializers.ValidationError("Resposta requer 'valor' quando 'pulada' é False.")
        return attrs


class AtualizarIdentificacaoSerializer(serializers.Serializer):
    """Payload do PATCH /identificar/."""

    nome_empresa = serializers.CharField(required=False, allow_blank=True, max_length=200)
    nome_respondente = serializers.CharField(required=False, allow_blank=True, max_length=160)
    email_respondente = serializers.EmailField(required=False, allow_blank=True)
