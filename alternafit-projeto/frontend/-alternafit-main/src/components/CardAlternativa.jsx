import React from "react";
import Badge from "./Badge";
import { cores } from "../styles/theme";
import { rotuloEquipamento, nomeDificuldade } from "../data/exercicios";

export default function CardAlternativa({ exercicio, favoritos, onToggleFavorito, onVerVideo }) {
  const id = exercicio.codigo || exercicio.nome;
  const favoritado = favoritos.includes(id);
  const dificuldadeTexto = exercicio.dificuldade
    ? nomeDificuldade(exercicio.dificuldade)
    : "A definir";
  const dicaTexto =
    exercicio.dica || "Dica ainda não cadastrada pelo time de Educação Física.";

  return (
    <div
      style={{
        background: cores.cardFundo,
        border: `1px solid ${cores.borda}`,
        borderRadius: 18,
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 12,
        boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
        transition: "transform 0.15s ease",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-3px)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <Badge texto={rotuloEquipamento(exercicio)} semEquipamento={exercicio.semEquipamento} />
        <button
          onClick={() => onToggleFavorito(id)}
          aria-label="Favoritar exercício"
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 22,
            lineHeight: 1,
            padding: 8,
            minWidth: 44,
            minHeight: 44,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: favoritado ? cores.orange : cores.textoSecundario,
            transition: "color 0.15s ease, transform 0.15s ease",
            transform: favoritado ? "scale(1.15)" : "scale(1)",
          }}
        >
          {favoritado ? "♥" : "♡"}
        </button>
      </div>

      <h3 style={{ fontSize: 18, fontWeight: 800, color: cores.texto, margin: 0 }}>
        {exercicio.nome}
      </h3>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: cores.textoSecundario }}>
          Nível:
        </span>
        <span style={{ fontSize: 12, fontWeight: 700, color: cores.texto }}>
          {dificuldadeTexto}
        </span>
      </div>

      <p style={{ fontSize: 13, color: cores.textoSecundario, margin: 0, lineHeight: 1.5 }}>
        {dicaTexto}
      </p>

      <button
        onClick={() => onVerVideo({ nome: exercicio.nome, url: exercicio.videoUrl || null })}
        style={{
          marginTop: 4,
          background: cores.cardFundoAlt,
          border: `1px solid ${cores.borda}`,
          borderRadius: 12,
          padding: "12px 14px",
          minHeight: 44,
          color: cores.texto,
          fontWeight: 700,
          fontSize: 13,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        ▶ Ver vídeo
      </button>
    </div>
  );
}
