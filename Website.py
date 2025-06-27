from flask import Flask, render_template
from nmap import PortScanner

app = Flask(__name__)

@app.route("/")
def run_command():
    scanner = PortScanner()
    scanner.scan("192.168.2.115/24", ports="80,8000", arguments="--open")
    modules = []
    for ip in scanner.all_hosts():
        host = scanner[ip]
        hostname = host.hostname()
        for port in host.all_tcp():
            data = {
                "address": f"{ip}:{port}",
                "host": hostname
            }
            modules.append(data)

    return render_template("index.html", modules=modules)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
