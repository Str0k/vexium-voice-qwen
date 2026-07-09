import "./globals.css";

export const metadata = {
  title: "Vexium AI — Bilingual AI voice receptionist",
  description:
    "AI voice agent that answers calls and books appointments, in Spanish and English. Try the live demo.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover", // extend under the notch; we pad with safe-area insets
  themeColor: "#0a0614",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Finlandica+Headline:ital,wght@0,100..900;1,100..900&family=Stack+Sans+Notch:wght@200..700&display=swap"
          rel="stylesheet"
        />
        {/* No-JS / hydration-failure fallback: never leave reveal content hidden */}
        <noscript>
          <style>{`.reveal{opacity:1!important;transform:none!important}`}</style>
        </noscript>
      </head>
      <body>
        <div className="aurora" aria-hidden="true"><span /><span /></div>
        <div className="grain" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
