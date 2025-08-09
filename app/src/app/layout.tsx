import "./globals.css";
import type { ReactNode } from "react";
import Providers from "./providers"; // <-- client wrapper
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Providers>
          <div className="grid grid-cols-[260px_1fr] grid-rows-[64px_1fr] min-h-screen">
            <div className="row-span-2"><Sidebar/></div>
            <div className="col-start-2"><Topbar/></div>
            <main className="col-start-2 p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
