import React from "react";
import { cores } from "../styles/theme";

export default function Header({ totalFavoritos }) {
  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "22px 18px",
        borderBottom: `1px solid ${cores.borda}`,
        maxWidth: 480,
        margin: "0 auto",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 34,
            height: 34,
            background: cores.navy,
            clipPath:
              "polygon(25% 5%, 75% 5%, 100% 50%, 75% 95%, 25% 95%, 0% 50%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="5" cy="17" r="2" />
            <circle cx="12" cy="8" r="2" />
            <circle cx="19" cy="12" r="2" />
            <path d="M6.5 15.5L10.5 9.5M13.5 9L17.5 11" />
          </svg>
        </div>
        <span style={{ fontWeight: 800, fontSize: 17 }}>
          alterna<span style={{ color: cores.orange }}>fit</span>
        </span>
      </div>
      <div style={{ fontSize: 12.5, color: cores.textoSecundario, fontWeight: 600 }}>
        {totalFavoritos} favorito{totalFavoritos !== 1 ? "s" : ""}
      </div>
    </header>
  );
}
