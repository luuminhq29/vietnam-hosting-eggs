const http = require("http");
const port = Number(process.env.SERVER_PORT || 8080);
http.createServer((_q, s) => s.end("Hello from Vietnam Hosting Node.js\n")).listen(port, "0.0.0.0", () => console.log(`Listening on ${port}`));
