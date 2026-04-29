"""
Ferzion Discovery — Briefing / Models.

Modelagem da SESSÃO de briefing do cliente.

Diferente do app `methodology` (que é a metodologia VERSIONADA), este app
modela a EXECUÇÃO de uma metodologia por um cliente real.

Hierarquia:
    BriefingSessao (1 cliente, 1 versão de roteiro pinada)
        ├── RespostaPergunta  (uma por pergunta respondida)
        ├── SinalCapturado    (extraídos pelas engines a partir das respostas)
        └── EventoBriefing    (log append-only do que aconteceu)

Princípios:
    - Snapshot de pergunta na resposta: editar metodologia não corrompe histórico.
    - Token público separado de PK: URL não expõe ID interno.
    - Append-only: respostas não são deletadas, são versionadas.
    - Sinais como entidade: query/filtro longitudinal entre clientes.
"""

from __future__ import annotations

import secrets
from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.methodology.models import (
    CatalogoSinal,
    PerfilProfundidade,
    Pergunta,
    RoteiroVersao,
)
from shared.domain.base_entity import BaseEntity
from shared.exceptions import InvalidStateTransition

TOKEN_LENGTH = 32  # bytes → ~43 chars urlsafe


# =============================================================================
#  ENUMS
# =============================================================================


class StatusBriefing(models.TextChoices):
    INICIADA = "iniciada", "Iniciada"
    EM_ANDAMENTO = "em_andamento", "Em andamento"
    CONCLUIDA = "concluida", "Concluída"
    ABANDONADA = "abandonada", "Abandonada"


class TipoEventoBriefing(models.TextChoices):
    SESSAO_INICIADA = "sessao_iniciada", "Sessão iniciada"
    PERFIL_CALCULADO = "perfil_calculado", "Perfil calculado"
    PERGUNTA_RESPONDIDA = "pergunta_respondida", "Pergunta respondida"
    PERGUNTA_PULADA = "pergunta_pulada", "Pergunta pulada"
    ATO_CONCLUIDO = "ato_concluido", "Ato concluído"
    INSIGHT_DISPARADO = "insight_disparado", "Insight disparado"
    SINTESE_GERADA = "sintese_gerada", "Síntese gerada"
    SESSAO_CONCLUIDA = "sessao_concluida", "Sessão concluída"
    SESSAO_RETOMADA = "sessao_retomada", "Sessão retomada"


# =============================================================================
#  BRIEFING SESSAO
# =============================================================================


def _gerar_token() -> str:
    return secrets.token_urlsafe(TOKEN_LENGTH)


class BriefingSessao(BaseEntity):
    """
    Uma sessão de briefing executada por um cliente.

    Pin de metodologia: aponta para uma RoteiroVersao específica (não para
    a identidade). Mesmo se o roteiro evoluir, esta sessão usa a versão
    com a qual começou.
    """

    # --- Pinning de metodologia ---
    roteiro_versao = models.ForeignKey(
        RoteiroVersao,
        on_delete=models.PROTECT,
        related_name="sessoes",
        verbose_name="Versão do roteiro (pinada)",
    )

    # --- Identificação pública ---
    token = models.CharField(
        max_length=64,
        unique=True,
        default=_gerar_token,
        verbose_name="Token público",
        help_text="URL-safe. Não exibe PK interno.",
    )

    # --- Identificação do cliente (preenchida ao longo do briefing) ---
    nome_empresa = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nome da empresa",
        help_text="Captura quando informado durante o briefing.",
    )
    nome_respondente = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="Nome do respondente",
    )
    email_respondente = models.EmailField(
        blank=True,
        verbose_name="E-mail do respondente",
        help_text="Usado para link mágico de retorno e devolutiva.",
    )

    # --- Estado ---
    status = models.CharField(
        max_length=16,
        choices=StatusBriefing.choices,
        default=StatusBriefing.INICIADA,
        db_index=True,
        verbose_name="Status",
    )
    perfil_calculado = models.CharField(
        max_length=16,
        choices=PerfilProfundidade.choices,
        blank=True,
        verbose_name="Perfil calculado (SCA)",
        help_text="Resultado do Score Composto de Aprofundamento.",
    )

    # --- Posição atual no fluxo ---
    ato_atual = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Slug do ato atual",
    )
    pergunta_atual = models.ForeignKey(
        Pergunta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Pergunta atual",
    )

    # --- Carimbos temporais ---
    iniciada_em = models.DateTimeField(default=timezone.now, verbose_name="Iniciada em")
    concluida_em = models.DateTimeField(null=True, blank=True, verbose_name="Concluída em")
    ultima_atividade_em = models.DateTimeField(
        default=timezone.now,
        verbose_name="Última atividade em",
    )

    # --- Devolutiva (preenchida ao concluir) ---
    devolutiva_json = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Devolutiva (JSON)",
        help_text="Saída da engine de síntese. Preenchido ao concluir.",
    )

    # --- Origem ---
    origem = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="Origem",
        help_text="UTM/canal de origem (campanha, link direto, indicação, etc.).",
    )
    user_agent = models.CharField(max_length=400, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Sessão de briefing"
        verbose_name_plural = "Sessões de briefing"
        ordering: ClassVar[list[str]] = ["-iniciada_em"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["token"]),
            models.Index(fields=["status", "-iniciada_em"]),
            models.Index(fields=["roteiro_versao", "status"]),
            models.Index(fields=["email_respondente"]),
        ]

    def __str__(self) -> str:
        ident = self.nome_empresa or self.nome_respondente or "anônimo"
        return f"Briefing #{self.token[:8]} — {ident} ({self.get_status_display()})"

    # -------------------------------------------------------------------------
    #  Transições de estado
    # -------------------------------------------------------------------------
    def marcar_em_andamento(self) -> None:
        if self.status != StatusBriefing.INICIADA:
            return
        self.status = StatusBriefing.EM_ANDAMENTO
        self.save(update_fields=["status", "updated_at"])

    def concluir(self, devolutiva_json: dict | None = None) -> None:
        if self.status == StatusBriefing.CONCLUIDA:
            return
        if self.status not in (StatusBriefing.INICIADA, StatusBriefing.EM_ANDAMENTO):
            raise InvalidStateTransition(
                f"Não é possível concluir briefing com status {self.get_status_display()}."
            )
        self.status = StatusBriefing.CONCLUIDA
        self.concluida_em = timezone.now()
        if devolutiva_json is not None:
            self.devolutiva_json = devolutiva_json
        self.save(update_fields=["status", "concluida_em", "devolutiva_json", "updated_at"])

    def marcar_abandonada(self) -> None:
        if self.status == StatusBriefing.CONCLUIDA:
            return
        self.status = StatusBriefing.ABANDONADA
        self.save(update_fields=["status", "updated_at"])

    def tocar_atividade(self) -> None:
        """Atualiza ultima_atividade_em sem disparar lógica."""
        self.ultima_atividade_em = timezone.now()
        self.save(update_fields=["ultima_atividade_em"])

    # -------------------------------------------------------------------------
    #  Helpers
    # -------------------------------------------------------------------------
    @property
    def url_publica(self) -> str:
        """Caminho relativo público — frontend monta URL completa."""
        return f"/briefing/{self.token}"

    @property
    def total_perguntas_respondidas(self) -> int:
        return self.respostas.filter(pulada=False).count()

    @property
    def total_sinais_capturados(self) -> int:
        return self.sinais.count()

    def sinais_por_chave(self) -> dict[str, Any]:
        """Mapa {chave: valor_extraido} dos sinais capturados (último por chave)."""
        return {
            s.sinal.chave: s.valor
            for s in self.sinais.select_related("sinal").order_by("created_at")
        }


# =============================================================================
#  RESPOSTA DE PERGUNTA
# =============================================================================


class RespostaPergunta(BaseEntity):
    """
    Resposta atômica a uma pergunta dentro de uma sessão.

    Append-only: edição cria nova versão (versao crescente).
    Snapshot: campos `pergunta_codigo`, `pergunta_texto` preservam o que
    o cliente VIU no momento da resposta. Permite editar metodologia
    sem corromper sessões antigas.
    """

    sessao = models.ForeignKey(
        BriefingSessao,
        on_delete=models.CASCADE,
        related_name="respostas",
        verbose_name="Sessão",
    )
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.PROTECT,
        related_name="respostas",
        verbose_name="Pergunta",
    )

    # --- Snapshot da pergunta no momento da resposta ---
    pergunta_codigo = models.CharField(max_length=16, verbose_name="Código (snapshot)")
    pergunta_texto = models.TextField(verbose_name="Texto público (snapshot)")
    pergunta_tipo = models.CharField(max_length=32, verbose_name="Tipo (snapshot)")

    # --- Valor da resposta ---
    valor = models.JSONField(
        verbose_name="Valor da resposta",
        help_text=(
            "Formato depende do tipo: "
            "escolha_unica → 'codigo_opcao'; "
            "escolha_multipla → ['codigo_opcao_1', ...]; "
            "texto → 'texto livre'; "
            "escala → int."
        ),
    )

    # --- Metadados ---
    pulada = models.BooleanField(
        default=False,
        verbose_name="Pulada",
        help_text="True se cliente optou por pular pergunta opcional.",
    )
    versao = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Versão",
        help_text="Cliente pode revisar e re-responder. Maior versão = mais recente.",
    )
    tempo_ate_responder_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo até responder (ms)",
        help_text="Telemetria: tempo desde apresentação até envio.",
    )

    class Meta:
        verbose_name = "Resposta de pergunta"
        verbose_name_plural = "Respostas de pergunta"
        ordering: ClassVar[list[str]] = ["sessao", "pergunta", "-versao"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["sessao", "pergunta", "versao"],
                name="uniq_resposta_sessao_pergunta_versao",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["sessao", "pergunta"]),
            models.Index(fields=["pergunta_codigo"]),
        ]

    def __str__(self) -> str:
        return f"{self.sessao.token[:8]} · {self.pergunta_codigo} v{self.versao}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Preenche snapshot na criação
        if not self.pk and self.pergunta_id:
            if not self.pergunta_codigo:
                self.pergunta_codigo = self.pergunta.codigo
            if not self.pergunta_texto:
                self.pergunta_texto = self.pergunta.texto_publico
            if not self.pergunta_tipo:
                self.pergunta_tipo = self.pergunta.tipo
        super().save(*args, **kwargs)

    @classmethod
    def proxima_versao(cls, sessao: BriefingSessao, pergunta: Pergunta) -> int:
        ultima = cls.objects.filter(sessao=sessao, pergunta=pergunta).order_by("-versao").first()
        return (ultima.versao + 1) if ultima else 1


# =============================================================================
#  SINAL CAPTURADO
# =============================================================================


class SinalCapturado(BaseEntity):
    """
    Sinal extraído de respostas pela engine de sinais.

    Entidade separada (não JSON em BriefingSessao) para:
        - Query/filtro longitudinal entre clientes.
        - Auditoria de origem (qual resposta gerou qual sinal).
        - Versionamento se a engine reprocessar respostas.
    """

    sessao = models.ForeignKey(
        BriefingSessao,
        on_delete=models.CASCADE,
        related_name="sinais",
        verbose_name="Sessão",
    )
    sinal = models.ForeignKey(
        CatalogoSinal,
        on_delete=models.PROTECT,
        related_name="capturas",
        verbose_name="Sinal (catálogo)",
    )
    valor = models.JSONField(verbose_name="Valor capturado")
    origem_resposta = models.ForeignKey(
        RespostaPergunta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sinais_gerados",
        verbose_name="Resposta de origem",
    )
    peso = models.FloatField(
        default=1.0,
        verbose_name="Peso aplicado",
        help_text="Cópia do peso do mapeamento, para auditoria.",
    )

    class Meta:
        verbose_name = "Sinal capturado"
        verbose_name_plural = "Sinais capturados"
        ordering: ClassVar[list[str]] = ["sessao", "sinal"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["sessao", "sinal"]),
            models.Index(fields=["sinal"]),
        ]

    def __str__(self) -> str:
        return f"{self.sessao.token[:8]} · {self.sinal.chave}={self.valor}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Validação de domínio (mesma lógica de MapeamentoDeSinal)
        if self.sinal_id and not self.sinal.valor_eh_valido(self.valor):
            raise ValidationError(
                {
                    "valor": (
                        f"Valor {self.valor!r} não é válido para o sinal "
                        f"{self.sinal.chave} (tipo {self.sinal.get_tipo_valor_display()})."
                    )
                }
            )
        super().save(*args, **kwargs)


# =============================================================================
#  EVENTO DO BRIEFING
# =============================================================================


class EventoBriefing(BaseEntity):
    """
    Log append-only de eventos da sessão.

    Permite reconstituir o briefing inteiro: replay temporal,
    debugging, auditoria, analytics futuros.
    """

    sessao = models.ForeignKey(
        BriefingSessao,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Sessão",
    )
    tipo = models.CharField(
        max_length=32,
        choices=TipoEventoBriefing.choices,
        verbose_name="Tipo",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Payload",
        help_text="Detalhes do evento.",
    )

    class Meta:
        verbose_name = "Evento de briefing"
        verbose_name_plural = "Eventos de briefing"
        ordering: ClassVar[list[str]] = ["sessao", "created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["sessao", "created_at"]),
            models.Index(fields=["tipo"]),
        ]

    def __str__(self) -> str:
        return f"{self.sessao.token[:8]} · {self.tipo} · {self.created_at:%H:%M:%S}"

    @classmethod
    def registrar(
        cls,
        sessao: BriefingSessao,
        tipo: TipoEventoBriefing,
        **payload: Any,
    ) -> EventoBriefing:
        """Helper: cria evento + atualiza ultima_atividade_em da sessão."""
        evento = cls.objects.create(sessao=sessao, tipo=tipo, payload=payload)
        sessao.tocar_atividade()
        return evento
