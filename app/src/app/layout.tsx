import "./globals.css";
import type { ReactNode } from "react";
import Providers from "./providers";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { Footer } from "@/components/Footer";

export const metadata = {
  title: "Siraj",
  description: "Siraj — Local-First Study Companion"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Providers>
          <div className="grid grid-cols-[260px_1fr] grid-rows-[64px_1fr_48px] min-h-screen">
            <div className="row-span-3">
              <Sidebar />
            </div>
            <div className="col-start-2">
              <Topbar />
            </div>
            <main className="col-start-2 p-6">{children}</main>
            <div className="col-start-2">
              <Footer />
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
