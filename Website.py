from flask import Flask, render_template
from nmap import PortScanner
from ScannerInfo import scan_document
import os

app = Flask(__name__)

def scan_network():
    scanner = PortScanner()
    scanner.scan("192.168.2.115/24", ports="80,8000", arguments="--open")
    devices = []
    for ip in scanner.all_hosts():
        host = scanner[ip]
        hostname = host.hostname()
        if hostname == "HP29B84D":
            os.environ['IP_ADDRESS'] = ip

        for port in host.all_tcp():
            data = {
                "address": f"{ip}:{port}",
                "host": hostname
            }
            devices.append(data)
    return devices

@app.route("/")
def landingpage(target="dashboard"):
    return render_template("loading.html", target=target)

@app.route("/dashboard")
def show_dashboard():
    devices = scan_network()
    return render_template("index.html", modules=devices, scanner=True)

@app.route("/scanner")
def scanning():
    return render_template("scanner.html")

@app.route("/scanner/duplex", methods=["POST"])
def duplex_scan():
    scan_document(duplex=True, verbose=True)
    return scanning()

@app.route("/scanner/simplex", methods=["POST"])
def simplex_scan():
    scan_document(duplex=False, verbose=True)
    return scanning()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
