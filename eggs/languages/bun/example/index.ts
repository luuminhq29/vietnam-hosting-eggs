const port = Number(process.env.SERVER_PORT || 8080);
Bun.serve({ hostname: "0.0.0.0", port, fetch: () => new Response("Hello Bun!\n") });
console.log(`Listening on ${port}`);
