export async function onRequest(context) {
  const url = new URL(context.request.url);

  if (url.hostname === "semeia.eulogikon.org") {
    url.hostname = "tekmeria.eulogikon.org";
    return Response.redirect(url.toString(), 301);
  }

  if (url.pathname === "/index.html") {
    url.pathname = "/";
    return Response.redirect(url.toString(), 301);
  }

  return context.next();
}
