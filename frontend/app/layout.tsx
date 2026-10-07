import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gold Daily Analysis | Disciplined Accumulation System",
  description:
    "Personal gold accumulation advisory system with transparent multi-factor valuation, PhonePe actual investment tracker, and honest day-by-day backtester.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#0b0d13",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
