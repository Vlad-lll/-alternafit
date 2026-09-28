import React from "react";
import { cores } from "../styles/theme";

export default function SearchBar({ valor, onChange, onSubmit }) {
  return (
    <form
      onSubmit={onSubmit}
      style={{
        display: "flex",
        gap: 10,
        maxWidth: 480,
        margin: "28px auto 0",
        flexWrap: "wrap",
      }}
    >
      <input
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ex: Supino Reto, Agachamento Livre, Puxada Alta"
        style={{
          flex: "1 1 220px",
          background: cores.cardFundo,
          border: `1px solid ${cores.borda}`,
          borderRadius: 14,
          padding: "14px 18px",
          minHeight: 48,
          color: cores.texto,
          fontSize: 15,
          outline: "none",
        }}
      />
      <button
        type="submit"
        style={{
          background: cores.navy,
          color: cores.navyTexto,
          border: "none",
          borderRadius: 14,
          padding: "14px 24px",
          minHeight: 48,
          fontWeight: 800,
          fontSize: 15,
          cursor: "pointer",
        }}
      >
        Buscar
      </button>
    </form>
  );
}
