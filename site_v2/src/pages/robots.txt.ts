// robots.txt, emitted as a real static file at build time (#844).
//
// Reads the single indexability switch rather than hardcoding a rule, so robots.txt and every
// page's <meta name="robots"> can never disagree. The audit re-checks the EMITTED file against the
// same switch, so editing one without the other fails the build.
//
// Note `noindex` is NOT access control and is NOT the mitigation for the imprint question (#799).
// It keeps the site out of search results; it does not keep anyone out of the site.
import type { APIRoute } from "astro";
import { INDEXABLE } from "../config/indexability.mjs";

export const GET: APIRoute = ({ site }) => {
  // While the site is a preview: refuse everything, and do NOT advertise the sitemap. A sitemap of
  // noindex URLs is a contradiction Search Console reports back as an error ("submitted URL marked
  // noindex"). The sitemap is still GENERATED so its 50k-cap splitting gets exercised on every
  // build (#844) -- it is simply not pointed at.
  const body = INDEXABLE
    ? ["User-agent: *", "Allow: /", "", `Sitemap: ${new URL("sitemap-index.xml", site).href}`, ""].join("\n")
    : ["User-agent: *", "Disallow: /", ""].join("\n");

  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
