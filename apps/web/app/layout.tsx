import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fromage: French Language Assessment Prep",
  description:
    "Original, exam-format French speaking mock exams with an AI examiner.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>
        <header>
          <Link href="/">Fromage: French Language Assessment Prep</Link>
        </header>
        <main>{children}</main>
        <footer>Not affiliated with France Éducation international.</footer>
      </body>
    </html>
  );
}
