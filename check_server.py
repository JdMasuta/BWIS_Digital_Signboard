import os
from .project_paths import paths
import requests
import logging
from pathlib import Path
from typing import List, Dict
import mimetypes
from urllib.parse import urljoin
import socket
from contextlib import closing

class ServerCheck:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.logger = self._setup_logging()
        self.results: Dict[str, List[Dict]] = {
            "static": [],
            "assets": []
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('server-check')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('server-check.log')
        
        # Create formatters
        log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

    def find_port(self) -> int:
        """Find the port the web server is running on"""
        common_ports = [80, 8080, 3000, 5000, 8000]
        
        for port in common_ports:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                if sock.connect_ex(('localhost', port)) == 0:
                    return port
        return -1

    def check_directory(self, directory: str, files: List[str]) -> List[Dict]:
        """Check if files in a directory are accessible"""
        results = []
        
        for file in files:
            url = urljoin(f"{self.base_url}/{directory}/", file)
            try:
                response = requests.head(url, timeout=5)
                
                result = {
                    "file": file,
                    "url": url,
                    "status": response.status_code,
                    "content_type": response.headers.get('content-type', 'unknown'),
                    "accessible": response.status_code == 200
                }
                
                if not result["accessible"]:
                    self.logger.warning(f"File not accessible: {url} (Status: {response.status_code})")
                else:
                    self.logger.info(f"File accessible: {url}")
                    
                results.append(result)
                
            except requests.RequestException as e:
                self.logger.error(f"Error checking {url}: {str(e)}")
                results.append({
                    "file": file,
                    "url": url,
                    "status": "error",
                    "content_type": "unknown",
                    "accessible": False,
                    "error": str(e)
                })
                
        return results

    def scan_directories(self):
        """Scan project directories for files to check"""
        base_dir = Path(os.getcwd())
        
        # Check static files
        static_dir = base_dir / 'static'
        if static_dir.exists():
            css_files = list(static_dir.glob('css/*.css'))
            js_files = list(static_dir.glob('js/*.js'))
            
            self.results["static"].extend(self.check_directory(
                paths.static / "css", 
                [f.name for f in css_files]
            ))
            self.results["static"].extend(self.check_directory(
                paths.static / "js", 
                [f.name for f in js_files]
            ))
        else:
            self.logger.error("Static directory not found")

        # Check asset files
        assets_dir = base_dir / 'assets'
        if assets_dir.exists():
            card_images = list(assets_dir.glob('cards/*.*'))
            self.results["assets"].extend(self.check_directory(
                paths.cards, 
                [f.name for f in card_images]
            ))
        else:
            self.logger.error("Assets directory not found")

    def generate_report(self):
        """Generate a detailed report of the checks"""
        report = []
        report.append("Server Configuration Check Report")
        report.append("=" * 40)
        report.append(f"Base URL: {self.base_url}")
        report.append("")

        # Static Files Report
        report.append("Static Files Check:")
        report.append("-" * 20)
        for result in self.results["static"]:
            status = "✓" if result["accessible"] else "✗"
            report.append(f"{status} {result['file']}")
            report.append(f"  URL: {result['url']}")
            report.append(f"  Status: {result['status']}")
            report.append(f"  Content-Type: {result['content_type']}")
            if not result["accessible"]:
                report.append(f"  Error: {result.get('error', 'Not accessible')}")
            report.append("")

        # Assets Files Report
        report.append("Assets Files Check:")
        report.append("-" * 20)
        for result in self.results["assets"]:
            status = "✓" if result["accessible"] else "✗"
            report.append(f"{status} {result['file']}")
            report.append(f"  URL: {result['url']}")
            report.append(f"  Status: {result['status']}")
            report.append(f"  Content-Type: {result['content_type']}")
            if not result["accessible"]:
                report.append(f"  Error: {result.get('error', 'Not accessible')}")
            report.append("")

        # Save report
        report_path = "server_check_report.txt"
        with open(report_path, "w") as f:
            f.write("\n".join(report))
        
        self.logger.info(f"Report generated: {report_path}")
        return "\n".join(report)

def main():
    # Try to find the server port
    checker = ServerCheck()
    port = checker.find_port()
    
    if port == -1:
        print("Could not find active web server port")
        return
    
    print(f"Found web server on port {port}")
    checker.base_url = f"http://localhost:{port}"
    
    # Run checks
    checker.scan_directories()
    
    # Generate and print report
    report = checker.generate_report()
    print("\nCheck Report:")
    print(report)

if __name__ == "__main__":
    main()
