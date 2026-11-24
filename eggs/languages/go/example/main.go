package main
import ("fmt"; "net/http"; "os")
func main() { p := os.Getenv("SERVER_PORT"); if p == "" { p = "8080" }; http.HandleFunc("/", func(w http.ResponseWriter, _ *http.Request) { fmt.Fprintln(w, "Hello Go!") }); fmt.Println("Listening on :" + p); _ = http.ListenAndServe("0.0.0.0:"+p, nil) }
