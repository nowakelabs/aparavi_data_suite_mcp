# 🚀 Aparavi Data Suite MCP Server

**Transform your enterprise data into conversations with Claude Desktop.**

Turn complex data analysis into simple conversations. Ask questions like "Show me all duplicate files" or "Find sensitive data in finance folders" and get instant, actionable insights from your enterprise data - no technical skills required.

<div align="center">

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/nowakelabs/aparavi_data_suite_mcp)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://hub.docker.com/r/nowakelabs/aparavi-mcp-server)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**[Quick Start](#-5-minute-quick-start) • [What You Can Do](#-what-you-can-do) • [Step-by-Step Setup](#-complete-setup-guide) • [Troubleshooting](#-troubleshooting) • [Support](#-support)**

</div>

---

## 🌟 What This Does

Imagine having a data analyst who knows everything about your company's files, storage, and compliance status - available 24/7 through simple conversation. That's what this MCP server provides:

- **🗣️ Natural Language Queries**: Ask "What's taking up the most space?" instead of writing complex database queries
- **📊 Instant Reports**: Get compliance, storage, and security reports in seconds
- **🔍 Smart Discovery**: Find duplicates, sensitive data, and storage waste automatically
- **🏷️ Intelligent Tagging**: Organize and classify files with AI-powered assistance
- **⚡ Real-time Insights**: Live data from your Aparavi Data Suite instance

**Perfect for:** IT managers, compliance officers, data governance teams, storage administrators, and anyone who needs to understand their organization's data landscape.

---

## 🚀 5-Minute Quick Start

**Already have Aparavi Data Suite running?** Get up and running in 5 minutes:

### For Mac Users (Docker) 🍎

```bash
# 1. Download this project
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 2. Copy config to Claude Desktop
cp claudedesktop/claude_desktop_config_docker.json ~/.config/Claude/claude_desktop_config.json

# 3. Restart Claude Desktop
# That's it! Start asking Claude about your data.
```

### For Windows Users (Docker) 🪟

```powershell
# 1. Download this project (in PowerShell or Command Prompt)
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 2. Copy config to Claude Desktop
copy claudedesktop\claude_desktop_config_docker.json "%APPDATA%\Claude\claude_desktop_config.json"

# 3. Restart Claude Desktop
# You're ready to go!
```

**Don't have Aparavi Data Suite yet?** Continue to the [Complete Setup Guide](#-complete-setup-guide) below.

---

## 💬 What You Can Do

Once set up, you can have conversations like this with Claude:

### 📊 **Storage & Analytics**
- *"What's consuming the most storage space in our system?"*
- *"Show me storage usage by department"*
- *"Find all files larger than 100MB created this year"*
- *"Analyze our data growth trends over the last 2 years"*

### 🔍 **Data Discovery & Cleanup**
- *"Find duplicate files that we can safely delete"*
- *"Show me files that haven't been accessed in over a year"*
- *"What file types are taking up the most space?"*
- *"Identify files that should be archived"*

### 🛡️ **Security & Compliance**
- *"Find all files containing sensitive data"*
- *"Show me unclassified files in finance folders"*
- *"Generate a compliance report for GDPR"*
- *"What files have overly permissive access rights?"*

### 🏷️ **Data Organization**
- *"Tag all Excel files from Q4 2024 as 'financial reports'"*
- *"Find and tag all PDF contracts from legal department"*
- *"Show me all files tagged as 'confidential'"*
- *"Remove outdated tags from archived files"*

### 📈 **Business Intelligence**
- *"Run a complete storage optimization analysis"*
- *"Show me our data governance health score"*
- *"Generate an executive summary of our data landscape"*
- *"What are our biggest data management risks?"*

**🎯 Pro Tip:** Start any conversation with *"Help me get started with Aparavi"* and Claude will guide you through the available options!

---

## 📋 Complete Setup Guide

### Step 1: Install Prerequisites

#### What You Need:
1. **Aparavi Data Suite** - The data intelligence platform
2. **Claude Desktop** - Your AI assistant interface
3. **Docker Desktop** (recommended) OR Python 3.11+ (for advanced users)

---

### Step 2: Get Aparavi Data Suite Running

**⚠️ This is required before proceeding.**

#### Option A: New Installation

1. **Download Aparavi Data Suite:**
   - Visit: https://aparavi.com/download-aparavi-data-suite-baseline/
   - Download the installer for your operating system
   - Follow the installation wizard

2. **Initial Setup:**
   - Launch Aparavi Data Suite after installation
   - Complete the setup wizard to configure your data sources
   - Note the web interface URL (usually `http://localhost:80`)
   - Default credentials: `username: root` / `password: root`

3. **Verify Installation:**
   - Open your web browser
   - Go to `http://localhost:80`
   - Log in with your credentials
   - You should see the Aparavi Data Suite dashboard

#### Option B: Existing Installation

If you already have Aparavi Data Suite:
- Ensure it's running and accessible at `http://localhost:80`
- Know your username and password
- Verify you can log into the web interface

**Need Help?** Check the [Aparavi Documentation](https://help.aparavi.com/) for detailed setup instructions.

---

### Step 3: Install Claude Desktop

**Don't have Claude Desktop yet?**

1. **Download Claude Desktop:**
   - **Mac:** Download from [claude.ai](https://claude.ai/download)
   - **Windows:** Download from [claude.ai](https://claude.ai/download)

2. **Install and Sign Up:**
   - Install Claude Desktop
   - Create a Claude account or sign in
   - Complete the initial setup

---

### Step 4: Choose Your Installation Method

## Method 1: Docker Installation (Recommended) 🐳

**✅ Best for:** Everyone - easiest setup, works on all platforms, no coding experience needed

**Prerequisites:** Docker Desktop installed on your computer

### Mac Docker Setup

```bash
# 1. Install Docker Desktop (if not already installed)
# Download from: https://www.docker.com/products/docker-desktop/

# 2. Clone this project
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 3. Configure Claude Desktop
mkdir -p ~/.config/Claude
cp claudedesktop/claude_desktop_config_docker.json ~/.config/Claude/claude_desktop_config.json

# 4. Restart Claude Desktop
# The server will automatically download and start when Claude needs it

# 5. Test the connection
# Open Claude Desktop and ask: "Check Aparavi server health"
```

### Windows Docker Setup

```powershell
# 1. Install Docker Desktop (if not already installed)
# Download from: https://www.docker.com/products/docker-desktop/

# 2. Clone this project (in PowerShell or Command Prompt)
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 3. Configure Claude Desktop
if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"
copy claudedesktop\claude_desktop_config_docker.json "%APPDATA%\Claude\claude_desktop_config.json"

# 4. Restart Claude Desktop
# The server will automatically download and start when Claude needs it

# 5. Test the connection
# Open Claude Desktop and ask: "Check Aparavi server health"
```

**How Docker Method Works:**
- When you ask Claude a question, it automatically downloads and runs the Aparavi MCP server
- The server connects to your local Aparavi Data Suite instance
- Results are returned instantly to your conversation
- Everything runs securely on your local machine

---

## Method 2: Local Installation (Advanced) 💻

**✅ Best for:** Developers, those who want to modify the code, or users who prefer not to use Docker

**Prerequisites:** Python 3.11 or newer, Git

### Mac Local Setup

```bash
# 1. Install Python 3.11+ (if not already installed)
# Check version: python3 --version
# If needed, install from: https://www.python.org/downloads/

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or with homebrew: brew install uv

# 3. Clone and setup the project
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 4. Create virtual environment and install dependencies
uv sync

# 5. Configure Claude Desktop
mkdir -p ~/.config/Claude
cp claudedesktop/claude_desktop_config_mac.json ~/.config/Claude/claude_desktop_config.json

# 6. Update the config paths (important!)
# Edit ~/.config/Claude/claude_desktop_config.json
# Replace ~/Documents/GitHub/aparavi_data_suite_mcp with your actual project path

# 7. Restart Claude Desktop and test
# Ask Claude: "Check Aparavi server health"
```

### Windows Local Setup

```powershell
# 1. Install Python 3.11+ (if not already installed)
# Check version: python --version
# If needed, download from: https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation

# 2. Install UV package manager
# Download and run: https://github.com/astral-sh/uv/releases/latest
# Or use pip: pip install uv

# 3. Clone and setup the project
git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
cd aparavi_data_suite_mcp

# 4. Create virtual environment and install dependencies
uv sync

# 5. Configure Claude Desktop
if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"
copy claudedesktop\claude_desktop_config_windows.json "%APPDATA%\Claude\claude_desktop_config.json"

# 6. Update the config paths (important!)
# Edit %APPDATA%\Claude\claude_desktop_config.json
# Replace %USERPROFILE%\Documents\GitHub\aparavi_data_suite_mcp with your actual project path

# 7. Restart Claude Desktop and test
# Ask Claude: "Check Aparavi server health"
```

**Path Configuration Note:**
You must update the file paths in the Claude config file to match where you downloaded the project. Look for lines containing file paths and update them to your actual project location.

---

### Step 5: Verify Everything Works

1. **Restart Claude Desktop** completely (quit and relaunch)

2. **Open a new conversation** with Claude

3. **Test the connection:**
   ```
   Check Aparavi server health
   ```

4. **Try a basic query:**
   ```
   Show me information about the Aparavi server
   ```

5. **Run your first report:**
   ```
   Show me a list of available reports
   ```

**✅ Success Indicators:**
- Claude responds with server health information
- No error messages about connection failures
- You can see available reports and tools

**❌ If Something's Wrong:**
- Check the [Troubleshooting section](#-troubleshooting) below
- Verify Aparavi Data Suite is running at `http://localhost:80`
- Ensure the Claude config file paths are correct

---

## 🎓 Learning to Use the System

### Your First Questions

Start with these beginner-friendly questions:

1. **"Help me get started with Aparavi"** - Claude will provide a personalized guide
2. **"What can you help me discover about our data?"** - Overview of capabilities
3. **"Show me the health status of our system"** - Verify everything is working
4. **"List all available reports"** - See what analysis tools are available

### Common Workflows

**Weekly Data Review:**
1. "Check server health and run a storage audit"
2. "Show me any new duplicate files from this week"
3. "What's our compliance status for classified data?"

**Monthly Cleanup:**
1. "Find files that haven't been accessed in 90 days"
2. "Show me storage waste opportunities"
3. "Run a complete data governance review"

**Executive Reporting:**
1. "Generate an executive summary of our data landscape"
2. "Show data growth trends over the last quarter"
3. "What are our biggest storage optimization opportunities?"

### Advanced Features

Once comfortable with basic queries:

- **Custom Analysis:** "Find all PDF files over 50MB created by the finance team last quarter"
- **Bulk Tagging:** "Tag all spreadsheets containing 'budget' as financial documents"
- **Complex Searches:** "Show files that are classified as sensitive but have public access permissions"
- **Workflow Automation:** "Run the complete security assessment workflow"

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### "Can't connect to Aparavi Data Suite"

**Problem:** Claude reports connection failures

**Solutions:**
1. **Verify Aparavi is running:**
   - Open browser to `http://localhost:80`
   - You should see Aparavi login page
   - If not, restart Aparavi Data Suite service

2. **Check credentials:**
   - Default: username `root`, password `root`
   - Update config file if you changed these

3. **Firewall/antivirus:**
   - Ensure port 80 is not blocked
   - Temporarily disable antivirus to test

4. **Docker users:**
   - Ensure Docker Desktop is running
   - Restart Docker Desktop if needed

#### "MCP server won't start"

**Problem:** Claude can't start the MCP server

**Docker Solutions:**
1. Ensure Docker Desktop is running
2. Check Docker has permission to run containers
3. Verify the config file path is correct

**Local Installation Solutions:**
1. Check Python version: `python3 --version` (must be 3.11+)
2. Verify UV is installed: `uv --version`
3. Check file paths in Claude config are absolute paths
4. Ensure virtual environment was created: look for `.venv` folder

#### "Claude doesn't see the MCP server"

**Problem:** Claude acts like the server doesn't exist

**Solutions:**
1. **Check config file location:**
   - Mac: `~/.config/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Verify config file contents:**
   - Should be valid JSON
   - No syntax errors (missing commas, brackets)
   - Correct file paths for your system

3. **Restart Claude Desktop:**
   - Completely quit Claude Desktop
   - Relaunch from Applications/Start Menu
   - Try a new conversation

#### "Permission denied" errors

**Problem:** Can't access files or folders

**Mac Solutions:**
```bash
# Fix permissions
chmod +x ~/.config/Claude/claude_desktop_config.json
sudo chown -R $USER ~/.config/Claude/
```

**Windows Solutions:**
- Run Command Prompt as Administrator
- Ensure your user has full control of the project folder
- Check Windows Defender isn't blocking file access

#### Performance Issues

**Problem:** Slow responses or timeouts

**Solutions:**
1. **For large datasets:**
   - Ask for smaller result sets: "Show me top 100 files by size"
   - Use date filters: "Files created in the last month"

2. **Aparavi Performance:**
   - Ensure adequate system resources (4GB+ RAM recommended)
   - Check Aparavi Data Suite isn't processing large scans

3. **Docker Performance:**
   - Increase Docker memory allocation in Docker Desktop settings
   - Restart Docker Desktop periodically

### Getting Debug Information

**Enable detailed logging:**

1. **Docker method:** Add to your conversation:
   ```
   Please enable debug logging and check the server health
   ```

2. **Local method:** Set environment variable:
   ```bash
   # Mac/Linux
   export LOG_LEVEL=DEBUG

   # Windows
   set LOG_LEVEL=DEBUG
   ```

**Check logs:**
- Docker: `docker logs $(docker ps -q --filter "ancestor=nowakelabs/aparavi-mcp-server")`
- Local: Look for log files in the project directory

---

## 📚 Configuration Reference

### Customizing Your Setup

#### Changing Aparavi Connection Settings

If your Aparavi Data Suite runs on different settings:

1. **Different port:** Edit the config file, change `APARAVI_PORT` from `80` to your port
2. **Different host:** Change `APARAVI_HOST` from `localhost` to your server IP
3. **Different credentials:** Update `APARAVI_USERNAME` and `APARAVI_PASSWORD`

#### Docker Configuration Example

```json
{
  "mcpServers": {
    "aparavi-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "APARAVI_HOST=192.168.1.100",
        "-e", "APARAVI_PORT=8080",
        "-e", "APARAVI_USERNAME=admin",
        "-e", "APARAVI_PASSWORD=mypassword",
        "-e", "LOG_LEVEL=INFO",
        "nowakelabs/aparavi-mcp-server:latest",
        "python", "/app/scripts/start_server.py"
      ]
    }
  }
}
```

#### Local Configuration Example

```json
{
  "mcpServers": {
    "aparavi-mcp-server": {
      "command": "/full/path/to/.venv/bin/python",
      "args": ["/full/path/to/scripts/start_server.py"],
      "cwd": "/full/path/to/aparavi_data_suite_mcp",
      "env": {
        "APARAVI_HOST": "localhost",
        "APARAVI_PORT": "80",
        "APARAVI_USERNAME": "root",
        "APARAVI_PASSWORD": "root",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Available Reports and Tools

The system includes **22 pre-built reports** in categories:

**📊 Storage & Optimization:**
- Data sources overview
- File type analysis
- Large files analysis
- Storage optimization opportunities
- Archive candidates

**🔄 Data Quality:**
- Duplicate files analysis
- Version control analysis
- Data cleanup opportunities

**🛡️ Security & Compliance:**
- Classification overview
- Sensitive data analysis
- Retention analysis
- Risk assessment

**📈 Analytics & Growth:**
- Data growth analysis
- User activity analysis
- Performance metrics
- Collaboration insights

**🔧 Workflows:**
- Storage audit (comprehensive storage analysis)
- Security assessment (security-focused analysis)
- Data lifecycle (usage and activity analysis)
- Growth analysis (historical trends)
- Compliance check (classification overview)

---

## 🚀 Performance Optimization for Large Environments

### Cache Warming & Data Preparation

**🏢 Enterprise environments with large data footprints (100GB+ or 1M+ files)** may experience slower initial responses as Aparavi Analytics processes complex queries. Here's how to optimize performance:

#### Automatic Cache Warming with Run-All-Reports Script

The included PowerShell script pre-executes all reports to warm up Aparavi's analytics cache, dramatically improving response times for subsequent Claude conversations.

**Windows Setup (Recommended for Large Environments):**

```powershell
# Navigate to the project directory
cd aparavi_data_suite_mcp

# Quick cache warm-up (excludes slow reports - takes 5-10 minutes)
.\scripts\run-all-reports.ps1

# Complete cache warm-up (includes all reports - takes 15-30 minutes)
.\scripts\run-all-reports.ps1 -IncludeSlow

# Interactive mode - choose which reports to run
.\scripts\run-all-reports.ps1 -Interactive

# For remote Aparavi instances
.\scripts\run-all-reports.ps1 -AparaviHost "192.168.1.100" -Username "admin" -Password "yourpassword"
```

**Mac/Linux Setup:**

```bash
# Run via PowerShell Core (install if needed: brew install powershell)
pwsh ./scripts/run-all-reports.ps1

# Alternative: Use the MCP server to run reports
# Start Claude Desktop and run:
# "Run all available reports to warm up the cache"
```

#### What Cache Warming Does

**Before Warming:** First-time queries may take 30-120 seconds as Aparavi:
- Indexes file metadata across data sources
- Calculates complex aggregations (duplicates, growth trends)
- Builds internal query optimization plans

**After Warming:** Same queries respond in 2-10 seconds because:
- ✅ Analytics results are cached in memory
- ✅ Query execution plans are optimized
- ✅ File metadata is pre-indexed
- ✅ Complex calculations are pre-computed

#### Performance Optimization Schedule

**Daily (Automated):**
```powershell
# Schedule via Windows Task Scheduler or cron
.\scripts\run-all-reports.ps1 -IncludeSlow > cache-warm-$(Get-Date -Format 'yyyyMMdd').log
```

**Before Important Analysis:**
- Run cache warming 15-30 minutes before executive presentations
- Warm cache after major data ingestion or Aparavi updates
- Schedule during off-hours to avoid impacting production queries

#### Enterprise Performance Tips

**🔄 Query Response Optimization:**
- **Small results first**: Ask for "top 10" or "last 30 days" before broad queries
- **Use date filters**: "Files created since 2024" vs. "all files ever"
- **Specific locations**: "Finance department files" vs. "all company files"

**⚡ Conversation Flow:**
```
1. "Check Aparavi server health" (verifies connection)
2. "Show me storage usage by top 5 departments" (quick overview)
3. "Find duplicate files over 100MB in finance folders" (specific analysis)
4. "Run complete storage optimization workflow" (comprehensive analysis)
```

**🏗️ Infrastructure Recommendations:**
- **Aparavi Server**: 8GB+ RAM, SSD storage for optimal query performance
- **Docker Resources**: Increase Docker Desktop memory to 4GB+ for large datasets
- **Network**: Ensure gigabit connection between Aparavi server and client

#### Troubleshooting Large Environment Issues

**"Query timeout" or "Connection reset":**
```powershell
# Increase timeout and run cache warming in batches
.\scripts\run-all-reports.ps1 -Interactive
# Select smaller subsets of reports to run
```

**"Out of memory" errors:**
- Restart Aparavi Data Suite service
- Increase system RAM or reduce concurrent queries
- Use filters to limit query scope: "last 6 months" instead of "all time"

**Slow Docker performance:**
- Increase Docker Desktop memory allocation
- Use local installation method for very large environments
- Consider running MCP server directly on Aparavi server machine

---

## 🚀 Advanced Usage

### Power User Tips

**Combine Multiple Queries:**
```
Run a storage audit workflow, then find all duplicate files over 100MB,
and finally show me files that haven't been accessed in 6 months
```

**Create Custom Searches:**
```
Find all Excel files created by users in the finance department
that contain the word "budget" and were modified in the last 30 days
```

**Automate Regular Tasks:**
```
Set up a weekly analysis that shows: storage growth, new duplicates,
compliance issues, and files that should be archived
```

### Integration Possibilities

- **Scheduled Reports:** Use Claude API to automate regular data analysis
- **Alerting:** Set up notifications for compliance violations or storage issues
- **Business Intelligence:** Export data for use in PowerBI, Tableau, or other BI tools
- **Workflow Integration:** Combine with other enterprise tools via APIs

---

## 💡 Best Practices

### Data Governance
- Run weekly compliance checks
- Monitor sensitive data classification status
- Review access permissions regularly
- Track data growth trends

### Storage Management
- Identify cleanup opportunities monthly
- Monitor duplicate file accumulation
- Track large file creation
- Plan archive strategies based on access patterns

### Security
- Regular sensitive data audits
- Monitor classification compliance
- Review file access patterns
- Identify overly permissive files

---

## 🆘 Support

### Getting Help

1. **First Steps:**
   - Ask Claude: "Help me troubleshoot Aparavi connection issues"
   - Check this README's troubleshooting section
   - Verify all prerequisites are installed correctly

2. **Community Support:**
   - GitHub Issues: [Report problems or request features](https://github.com/nowakelabs/aparavi_data_suite_mcp/issues)
   - Discussions: Share tips and ask questions

3. **Professional Support:**
   - Email: ask@nowakelabs.com
   - Include: Operating system, installation method, error messages, logs

### Contributing

We welcome contributions! Whether it's:
- 🐛 Bug reports and fixes
- ✨ New features and enhancements
- 📖 Documentation improvements
- 💡 Usage examples and tutorials

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🎯 What's Next?

Once you're up and running:

1. **Explore:** Try different types of questions to understand your data landscape
2. **Automate:** Set up regular analysis workflows for your team
3. **Integrate:** Connect insights to your broader data governance strategy
4. **Optimize:** Use findings to improve storage efficiency and compliance
5. **Scale:** Consider enterprise features for larger deployments

---

<div align="center">

**Built with ❤️ for seamless enterprise data management through AI conversation**

[⬆️ Back to Top](#-aparavi-data-suite-mcp-server) • [Quick Start](#-5-minute-quick-start) • [Support](#-support)

</div>