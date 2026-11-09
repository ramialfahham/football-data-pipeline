// Every page leaves the build with its hyphen-joined words kept whole (lib/wholeWords.mjs).
import { defineMiddleware } from "astro:middleware";
import { keepHyphenWords } from "./lib/wholeWords.mjs";

export const onRequest = defineMiddleware(async (_context, next) => {
  const response = await next();
  if (!(response.headers.get("content-type") ?? "").includes("text/html")) return response;
  const html = keepHyphenWords(await response.text());
  return new Response(html, { status: response.status, statusText: response.statusText, headers: response.headers });
});
