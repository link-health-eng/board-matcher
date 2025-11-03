import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <main className="bg-gray-50 min-h-screen w-full">
    <StrictMode>
      <App />
    </StrictMode>
  </main>
);
