import React from "react";
import { cores } from "../styles/theme";

export default function FiltroChips({ titulo, opcoes, selecionado, onSelecionar }) {
  return (
    <div style={{ marginBottom: 18 }}>
      {titulo && (
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: cores.textoSecundario,
            marginBottom: 8,
          }}
        >
          {titulo}
        </div>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {opcoes.map((opcao) => {
          const ativo = opcao === selecionado;
          return (
            <button
              key={opcao}
              onClick={() => onSelecionar(opcao)}
              style={{
                border: `1px solid ${ativo ? cores.orange : cores.borda}`,
                background: ativo ? cores.orangeTint : "transparent",
                color: ativo ? cores.orange : cores.textoSecundario,
                borderRadius: 999,
                padding: "10px 16px",
                minHeight: 40,
                fontSize: 12.5,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              {opcao}
            </button>
          );
        })}
      </div>
    </div>
  );
}
