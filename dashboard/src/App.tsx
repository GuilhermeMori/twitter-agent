import { useSquadSocket } from "@/hooks/useSquadSocket";
import { SquadSelector } from "@/components/SquadSelector";
import { PhaserGame } from "@/office/PhaserGame";
import { StatusBar } from "@/components/StatusBar";
import { useSquadStore } from "@/store/useSquadStore";
import { TwitterPanel } from "@/components/TwitterPanel";

export function App() {
  useSquadSocket();
  const selectedSquad = useSquadStore((s) => s.selectedSquad);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "var(--bg-app)",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          height: 40,
          minHeight: 40,
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-sidebar)",
          fontSize: 13,
          fontWeight: 600,
          letterSpacing: 0.5,
          color: "var(--text-sidebar)",
        }}
      >
        opensquad Dashboard
      </header>

      {/* Main content */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", position: "relative" }}>
        <SquadSelector />
        <PhaserGame />

        {/* Overlay Panel for specific squads */}
        {selectedSquad === "twitter-engagement-squad" && (
          <div style={{
            position: "absolute",
            top: 20,
            right: 20,
            bottom: 20,
            width: "500px",
            zIndex: 1000,
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
            borderRadius: "12px",
            overflow: "hidden"
          }}>
            <TwitterPanel squadCode={selectedSquad} />
          </div>
        )}
      </div>

      {/* Footer */}
      <StatusBar />
    </div>
  );
}
