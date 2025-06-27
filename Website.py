from flask import Flask, render_template_string
import subprocess
import re
from nmap import PortScanner
from nmap import PortScannerHostDict

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Command Output</title></head>
<body>
  <h1>Command Output</h1>
  <pre>{{ output }}</pre>
</body>
</html>
"""

def get_module(ip, hostname, port):
    return f"I found {hostname} at {ip}:{port}"

@app.route("/")
def run_command():
    # Replace this with any command you want
    scanner = PortScanner()
    scanner.scan("192.168.2.115/24", ports="80,8000", arguments="--open")
    website = []
    for ip in scanner.all_hosts():
        host = scanner[ip]
        hostname = host.hostname()
        for port in host.all_tcp():
            module = get_module(ip=ip, port=port, hostname=hostname)

            website.append(module)

    return render_template_string(HTML_TEMPLATE, output="\n".join(website))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
