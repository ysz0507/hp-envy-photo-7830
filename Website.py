from flask import Flask, render_template, send_from_directory
from nmap import PortScanner

app = Flask(__name__)

printer_ip = ""

def scan_network():
    scanner = PortScanner()
    scanner.scan("192.168.2.115/24", ports="80,8000", arguments="--open")
    devices = []
    for ip in scanner.all_hosts():
        host = scanner[ip]
        hostname = host.hostname()
        for port in host.all_tcp():
            data = {
                "address": f"{ip}:{port}",
                "host": hostname
            }
            devices.append(data)
    return devices


@app.route("/")
def landingpage():
    return render_template("loading.html", target="dashboard")

@app.route("/dashboard")
def show_dashboard():
    devices = scan_network()
    return render_template("index.html", modules=devices)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
