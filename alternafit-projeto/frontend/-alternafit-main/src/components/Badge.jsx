import React from "react";
import { corBadgeFundo, corBadgeTexto } from "../styles/theme";

export default function Badge({ texto, semEquipamento }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 11px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: 0.2,
        color: corBadgeTexto(semEquipamento),
        background: corBadgeFundo(semEquipamento),
        whiteSpace: "nowrap",
      }}
    >
      {texto}
    </span>
  );
}
