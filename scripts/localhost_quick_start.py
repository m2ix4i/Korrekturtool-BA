#!/usr/bin/env python3
"""
Localhost Quick Start Script
Korrekturtool für Wissenschaftliche Arbeiten

This script provides a complete localhost setup and validation workflow.
It combines environment validation and service startup testing in one command.

Usage:
    python scripts/localhost_quick_start.py [--fix] [--port PORT] [--verbose]
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


def run_script(script_path: str, args: list) -> bool:
    """Run a Python script and return success status"""
    cmd = [sys.executable, script_path] + args
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code {e.returncode}")
        return False


def main():
    """Main entry point for quick start"""
    parser = argparse.ArgumentParser(
        description="Complete localhost environment setup and validation"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix environment issues where possible"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv('PORT', 5000)),
        help="Port for service validation (default: from PORT env var or 5000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output for all validations"
    )
    parser.add_argument(
        "--skip-env",
        action="store_true",
        help="Skip environment validation and go directly to service testing"
    )
    parser.add_argument(
        "--skip-service",
        action="store_true",
        help="Only run environment validation, skip service testing"
    )
    
    args = parser.parse_args()
    
    print("🚀 Localhost Quick Start - Korrekturtool Development Environment")
    print("=" * 70)
    
    success = True
    
    # Step 1: Environment Validation
    if not args.skip_env:
        print("\n📋 STEP 1: Environment Validation")
        print("-" * 40)
        
        env_args = []
        if args.fix:
            env_args.append("--fix")
        if args.verbose:
            env_args.append("--verbose")
        
        if not run_script("scripts/setup_localhost_env.py", env_args):
            success = False
            print("\n❌ Environment validation failed!")
            
            if not args.fix:
                print("💡 Try running with --fix flag to automatically resolve some issues")
                print("💡 Command: python scripts/localhost_quick_start.py --fix --verbose")
            
            if not args.skip_service:
                print("⚠️ Continuing with service validation despite environment issues...")
        else:
            print("\n✅ Environment validation completed successfully!")
    
    # Step 2: Service Validation
    if not args.skip_service:
        print("\n🔧 STEP 2: Service Startup Validation")
        print("-" * 40)
        
        service_args = ["--port", str(args.port)]
        if args.verbose:
            service_args.append("--verbose")
        
        if not run_script("scripts/validate_startup.py", service_args):
            success = False
            print("\n❌ Service validation failed!")
            print("💡 Check the service validation report for details")
            print("💡 Try running the Flask server manually: python web/app.py")
        else:
            print("\n✅ Service validation completed successfully!")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 QUICK START SUMMARY")
    
    if success:
        print("✅ Localhost environment is ready for development!")
        print(f"🌐 Access the application at: http://localhost:{args.port}")
        print("🛠️ All systems operational - you can start coding!")
        
        print("\n📋 Next Steps:")
        print("  1. Start development server: python web/app.py")
        print("  2. Open browser to: http://localhost:5000")
        print("  3. Upload a DOCX file and test the processing workflow")
        print("  4. Check real-time progress updates via WebSocket")
        
        if args.verbose:
            print("\n📄 Reports Generated:")
            print("  - localhost_setup_report.json (environment details)")
            print("  - service_validation_report.json (service test results)")
    
    else:
        print("❌ Localhost environment setup encountered issues")
        print("📋 Troubleshooting Steps:")
        print("  1. Review the error messages above")
        print("  2. Check the generated JSON reports for details")
        print("  3. Run with --verbose flag for more information")
        print("  4. Fix issues and run the quick start again")
        
        print("\n🔧 Common Fixes:")
        print("  - Missing API key: Add GOOGLE_API_KEY to .env file")
        print("  - Port conflict: Use --port 5001 or stop other services")
        print("  - Dependencies: Run 'pip install -r requirements.txt'")
        print("  - Permissions: Check directory write permissions")
    
    print("=" * 70)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()