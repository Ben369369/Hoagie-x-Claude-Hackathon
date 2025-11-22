#!/usr/bin/env python3
"""
MCP Security Scanner
Scans MCP configuration files for security vulnerabilities
"""

import json
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scanner.detection_rules import (
    DETECTION_RULES, 
    Severity, 
    get_severity_score, 
    get_severity_color,
    get_severity_emoji,
    check_description_length
)

console = Console()


class ScanResult:
    """Results from scanning a single tool"""
    
    def __init__(self, server_name: str, tool_name: str, description: str):
        self.server_name = server_name
        self.tool_name = tool_name
        self.description = description
        self.vulnerabilities = []
        self.risk_score = 0
        self.risk_level = "SAFE"
    
    def add_vulnerability(self, rule_name: str, severity: Severity, 
                         description: str, evidence: List[str], recommendation: str):
        """Add a detected vulnerability"""
        self.vulnerabilities.append({
            "rule": rule_name,
            "severity": severity,
            "description": description,
            "evidence": evidence,
            "recommendation": recommendation
        })
        
        # Update risk score
        self.risk_score += get_severity_score(severity)
        
        # Update risk level
        if severity == Severity.CRITICAL:
            self.risk_level = "CRITICAL"
        elif severity == Severity.HIGH and self.risk_level != "CRITICAL":
            self.risk_level = "HIGH"
        elif severity == Severity.MEDIUM and self.risk_level not in ["CRITICAL", "HIGH"]:
            self.risk_level = "MEDIUM"
        elif severity == Severity.LOW and self.risk_level == "SAFE":
            self.risk_level = "LOW"
    
    def is_safe(self) -> bool:
        """Check if tool is safe"""
        return len(self.vulnerabilities) == 0


class MCPScanner:
    """MCP Security Scanner"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.servers = {}
        self.results = []
        self.scan_time = None
    
    def load_config(self) -> bool:
        """Load MCP configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.servers = config.get('mcpServers', {})
                return True
        except FileNotFoundError:
            console.print(f"[red]Error: Config file not found: {self.config_path}[/red]")
            return False
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in config file: {e}[/red]")
            return False
    
    def scan_tool(self, server_name: str, tool_name: str, tool_data: Dict) -> ScanResult:
        """Scan a single tool for vulnerabilities"""
        description = tool_data.get('description', '')
        result = ScanResult(server_name, tool_name, description)
        
        # Run all detection rules
        for rule in DETECTION_RULES:
            matched, evidence = rule.check(description)
            
            if matched:
                result.add_vulnerability(
                    rule_name=rule.name,
                    severity=rule.severity,
                    description=rule.description,
                    evidence=evidence,
                    recommendation=rule.recommendation
                )
        
        # Check description length
        is_long, length = check_description_length(description)
        if is_long:
            result.add_vulnerability(
                rule_name="UNUSUAL_COMPLEXITY",
                severity=Severity.LOW,
                description=f"Tool description is unusually long ({length} characters)",
                evidence=[f"Description length: {length} chars (normal is < 1000)"],
                recommendation="Review this tool. Overly complex descriptions may hide malicious behavior."
            )
        
        return result
    
    def scan(self) -> bool:
        """Scan all servers and tools"""
        if not self.servers:
            console.print("[yellow]No servers found in configuration[/yellow]")
            return False
        
        self.scan_time = datetime.now()
        
        # Count total tools
        total_tools = sum(
            len(server.get('tools', [])) 
            for server in self.servers.values()
        )
        
        console.print(f"\n[cyan]Found {len(self.servers)} servers with {total_tools} tools[/cyan]\n")
        
        # Scan each server and tool
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for server_name, server_config in self.servers.items():
                task = progress.add_task(f"[cyan]Scanning {server_name}...", total=None)
                
                tools = server_config.get('tools', [])
                
                for tool in tools:
                    tool_name = tool.get('name', 'unnamed')
                    result = self.scan_tool(server_name, tool_name, tool)
                    self.results.append(result)
                    time.sleep(0.1)  # Simulate scanning time
                
                progress.update(task, completed=True)
        
        return True
    
    def get_summary(self) -> Dict:
        """Get scan summary statistics"""
        total_servers = len(self.servers)
        total_tools = len(self.results)
        
        critical = sum(1 for r in self.results if r.risk_level == "CRITICAL")
        high = sum(1 for r in self.results if r.risk_level == "HIGH")
        medium = sum(1 for r in self.results if r.risk_level == "MEDIUM")
        low = sum(1 for r in self.results if r.risk_level == "LOW")
        safe = sum(1 for r in self.results if r.risk_level == "SAFE")
        
        return {
            "total_servers": total_servers,
            "total_tools": total_tools,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "safe": safe,
            "scan_time": self.scan_time
        }
    
    def print_summary(self):
        """Print scan summary"""
        summary = self.get_summary()
        
        console.print("\n")
        console.print("=" * 60)
        console.print("[bold cyan]SCAN SUMMARY[/bold cyan]")
        console.print("=" * 60)
        
        # Summary table
        table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="white", justify="right")
        
        table.add_row("Total Servers", str(summary['total_servers']))
        table.add_row("Total Tools Scanned", str(summary['total_tools']))
        table.add_row("", "")
        table.add_row("🔴 CRITICAL Issues", f"[bold red]{summary['critical']}[/bold red]")
        table.add_row("🟠 HIGH Issues", f"[red]{summary['high']}[/red]")
        table.add_row("🟡 MEDIUM Issues", f"[yellow]{summary['medium']}[/yellow]")
        table.add_row("🔵 LOW Issues", f"[cyan]{summary['low']}[/cyan]")
        table.add_row("✅ SAFE Tools", f"[green]{summary['safe']}[/green]")
        
        console.print(table)
        console.print()
    
    def print_detailed_results(self):
        """Print detailed scan results"""
        console.print("\n[bold cyan]DETAILED RESULTS[/bold cyan]\n")
        
        # Group results by server
        by_server = {}
        for result in self.results:
            if result.server_name not in by_server:
                by_server[result.server_name] = []
            by_server[result.server_name].append(result)
        
        # Print each server
        for server_name, server_results in by_server.items():
            
            # Determine server risk level (highest of its tools)
            server_risk = "SAFE"
            for result in server_results:
                if result.risk_level == "CRITICAL":
                    server_risk = "CRITICAL"
                    break
                elif result.risk_level == "HIGH" and server_risk != "CRITICAL":
                    server_risk = "HIGH"
                elif result.risk_level == "MEDIUM" and server_risk not in ["CRITICAL", "HIGH"]:
                    server_risk = "MEDIUM"
                elif result.risk_level == "LOW" and server_risk == "SAFE":
                    server_risk = "LOW"
            
            # Color based on risk
            if server_risk == "SAFE":
                color = "green"
                icon = "✅"
            elif server_risk == "LOW":
                color = "cyan"
                icon = "🔵"
            elif server_risk == "MEDIUM":
                color = "yellow"
                icon = "🟡"
            elif server_risk == "HIGH":
                color = "red"
                icon = "🟠"
            else:  # CRITICAL
                color = "bold red"
                icon = "🔴"
            
            console.print(f"\n{icon} [{color}]Server: {server_name}[/{color}]")
            console.print(f"   Risk Level: [{color}]{server_risk}[/{color}]")
            console.print(f"   Tools: {len(server_results)}\n")
            
            # Print each tool
            for result in server_results:
                if result.is_safe():
                    console.print(f"   ✓ [green]{result.tool_name}[/green] - Safe")
                else:
                    console.print(f"   ✗ [{get_severity_color(Severity[result.risk_level])}]{result.tool_name}[/{get_severity_color(Severity[result.risk_level])}] - {result.risk_level}")
                    
                    # Print vulnerabilities
                    for vuln in result.vulnerabilities:
                        emoji = get_severity_emoji(vuln['severity'])
                        color = get_severity_color(vuln['severity'])
                        
                        console.print(f"      {emoji} [{color}]{vuln['description']}[/{color}]")
                        
                        # Print evidence (first 2 items only)
                        for evidence in vuln['evidence'][:2]:
                            console.print(f"         [dim]Evidence: {evidence[:100]}...[/dim]")
                        
                        if len(vuln['evidence']) > 2:
                            console.print(f"         [dim]... and {len(vuln['evidence']) - 2} more[/dim]")
                        
                        console.print(f"         [yellow]→ {vuln['recommendation']}[/yellow]")
                        console.print()
    
    def print_recommendations(self):
        """Print security recommendations"""
        critical_servers = set()
        high_servers = set()
        
        for result in self.results:
            if result.risk_level == "CRITICAL":
                critical_servers.add(result.server_name)
            elif result.risk_level == "HIGH":
                high_servers.add(result.server_name)
        
        if critical_servers or high_servers:
            console.print("\n[bold red]⚠️  SECURITY RECOMMENDATIONS[/bold red]\n")
            
            if critical_servers:
                console.print(Panel(
                    f"[bold red]IMMEDIATE ACTION REQUIRED[/bold red]\n\n"
                    f"The following servers have CRITICAL vulnerabilities:\n"
                    + "\n".join(f"  • {s}" for s in critical_servers) +
                    "\n\n[bold]RECOMMENDATION: Remove these servers immediately![/bold]\n"
                    "These servers pose an active security threat and should not be used.",
                    title="🔴 Critical Threats",
                    border_style="red",
                    box=box.HEAVY
                ))
            
            if high_servers:
                console.print(Panel(
                    f"[bold yellow]HIGH PRIORITY[/bold yellow]\n\n"
                    f"The following servers have HIGH risk issues:\n"
                    + "\n".join(f"  • {s}" for s in high_servers) +
                    "\n\n[bold]RECOMMENDATION: Review and fix immediately[/bold]\n"
                    "These servers should be audited before continued use.",
                    title="🟠 High Risk",
                    border_style="yellow",
                    box=box.ROUNDED
                ))
        else:
            console.print("\n[bold green]✅ No critical or high-risk issues found![/bold green]\n")
    
    def export_json(self, output_path: str):
        """Export results as JSON"""
        export_data = {
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "config_file": self.config_path,
            "summary": self.get_summary(),
            "results": []
        }
        
        for result in self.results:
            export_data["results"].append({
                "server": result.server_name,
                "tool": result.tool_name,
                "risk_level": result.risk_level,
                "risk_score": result.risk_score,
                "vulnerabilities": result.vulnerabilities
            })
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        console.print(f"\n[green]Results exported to: {output_path}[/green]\n")


def main():
    """Main scanner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Security Scanner")
    parser.add_argument(
        "--config",
        "-c",
        default="configs/poisoned_config.json",
        help="Path to MCP configuration file"
    )
    parser.add_argument(
        "--export",
        "-e",
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show summary"
    )
    
    args = parser.parse_args()
    
    # Print header
    console.print("""
[bold cyan]
╔═══════════════════════════════════════════════╗
║                                               ║
║         🔍 MCP SECURITY SCANNER 🔍            ║
║                                               ║
║     Detecting Malicious MCP Configurations    ║
║                                               ║
╚═══════════════════════════════════════════════╝
[/bold cyan]
    """, justify="center")
    
    console.print(f"[cyan]Scanning:[/cyan] {args.config}\n")
    
    # Create scanner
    scanner = MCPScanner(args.config)
    
    # Load configuration
    if not scanner.load_config():
        return 1
    
    # Run scan
    if not scanner.scan():
        return 1
    
    # Print results
    scanner.print_summary()
    
    if not args.quiet:
        scanner.print_detailed_results()
    
    scanner.print_recommendations()
    
    # Export if requested
    if args.export:
        scanner.export_json(args.export)
    
    # Return exit code based on findings
    summary = scanner.get_summary()
    if summary['critical'] > 0:
        return 2  # Critical issues found
    elif summary['high'] > 0:
        return 1  # High-risk issues found
    else:
        return 0  # No major issues


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/yellow]\n")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)