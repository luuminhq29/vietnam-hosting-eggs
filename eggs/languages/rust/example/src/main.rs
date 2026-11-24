use std::net::TcpListener;
use std::io::Write;
fn main() {
    let port = std::env::var("SERVER_PORT").unwrap_or_else(|_| "8080".into());
    let listener = TcpListener::bind(format!("0.0.0.0:{port}")).unwrap();
    println!("Listening on 0.0.0.0:{port}");
    for stream in listener.incoming().flatten() {
        let mut s = stream;
        let _ = s.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 23\r\n\r\nVietnam Hosting Rust!\n");
    }
}
