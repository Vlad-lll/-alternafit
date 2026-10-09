import React from "react";
import { cores } from "../styles/theme";
import { nomeDificuldade } from "../data/exercicios";

export default function CardPrincipal({ exercicio, totalAlternativasVisiveis, onVerVideo }) {
  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${cores.cardFundoAlt}, ${cores.cardFundo})`,
        border: `1px solid ${cores.navy}55`,
        borderRadius: 20,
        padding: "24px 26px",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        boxShadow: "0 10px 30px rgba(76,127,227,0.08)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: cores.navySoft, marginBottom: 6 }}>
            EXERCÍCIO BUSCADO
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 900, color: cores.texto, margin: 0 }}>
            {exercicio.nome}
          </h2>
          <div style={{ fontSize: 13, color: cores.textoSecundario, marginTop: 6 }}>
            {exercicio.gruposMusculares.join(" · ")}
          </div>
        </div>
        <div
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: cores.navyTexto,
            background: cores.navy,
            borderRadius: 999,
            padding: "8px 16px",
            whiteSpace: "nowrap",
          }}
        >
          {totalAlternativasVisiveis} alternativa{totalAlternativasVisiveis !== 1 ? "s" : ""}
        </div>
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", fontSize: 12.5, color: cores.textoSecundario }}>
        <span>
          Nível: <strong style={{ color: cores.texto }}>{nomeDificuldade(exercicio.dificuldade)}</strong>
        </span>
        {exercicio.equipamentos?.length > 0 && (
          <span>
            Equipamento: <strong style={{ color: cores.texto }}>{exercicio.equipamentos.join(", ")}</strong>
          </span>
        )}
      </div>

      {exercicio.dica && (
        <p style={{ fontSize: 13.5, color: cores.textoSecundario, margin: 0, lineHeight: 1.5 }}>
          {exercicio.dica}
        </p>
      )}

      {/* O botão só aparece quando o exercício tem vídeo cadastrado */}
      {exercicio.videoUrl && (
        <button
          onClick={() => onVerVideo({ nome: exercicio.nome, url: exercicio.videoUrl })}
          style={{
            alignSelf: "flex-start",
            background: cores.cardFundoAlt,
            border: `1px solid ${cores.borda}`,
            borderRadius: 12,
            padding: "10px 16px",
            minHeight: 44,
            color: cores.texto,
            fontWeight: 700,
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          ▶ Ver vídeo
        </button>
      )}
    </div>
  );
}
