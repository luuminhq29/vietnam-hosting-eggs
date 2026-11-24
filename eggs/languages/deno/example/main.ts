const port = Number(Deno.env.get("SERVER_PORT") ?? "8080");
Deno.serve({ hostname: "0.0.0.0", port }, () => new Response("Hello Deno!\n"));
