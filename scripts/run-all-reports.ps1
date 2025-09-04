# PowerShell script to run all Aparavi AQL reports and save to JSON files
# Usage: .\run-all-reports.ps1
# Requires: PowerShell 5.1 or later

param(
    [string]$AparaviHost = "localhost",
    [int]$AparaviPort = 80,
    [string]$Username = "root",
    [string]$Password = "root",
    [switch]$Interactive
)

# Create reports directory if it doesn't exist
$ReportsDir = Join-Path $PSScriptRoot "reports"
if (!(Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
    Write-Host "Created reports directory: $ReportsDir" -ForegroundColor Green
}

# Create log file with timestamp
$LogFile = Join-Path $ReportsDir "execution_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogEntry
    
    # Also write to console with appropriate color
    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        "WARNING" { Write-Host $Message -ForegroundColor Yellow }
        default { Write-Host $Message }
    }
}

# Base URL for Aparavi API
$BaseUrl = "http://${AparaviHost}:${AparaviPort}/server/api/v3/database/query"

# Create basic auth header
$AuthString = "${Username}:${Password}"
$AuthBytes = [System.Text.Encoding]::ASCII.GetBytes($AuthString)
$AuthBase64 = [System.Convert]::ToBase64String($AuthBytes)
$Headers = @{
    "Authorization" = "Basic $AuthBase64"
    "Content-Type" = "application/json"
}

# Define all reports with their names and AQL queries
$Reports = @(
    @{
        Name = "Data_Sources_Overview"
        Query = @"
SELECT
 COMPONENTS(parentPath, 3) AS "Data Source",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COUNT(name) AS "File Count",
 AVG(size)/1048576 AS "Average File Size (MB)",
 
 -- Recent activity indicators
 SUM(CASE WHEN (cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Files Created Last 30 Days",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Stale Files (>1 Year)",
 
 -- Size categories
 SUM(CASE WHEN size > 1073741824 THEN 1 ELSE 0 END) AS "Large Files (>1GB)",
 
 -- Duplicates
 SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates"

FROM 
 STORE('/')
WHERE 
 ClassID = 'idxobject'
GROUP BY 
 COMPONENTS(parentPath, 3)
ORDER BY 
 "Total Size (GB)" DESC
"@
    },
    @{
        Name = "Subfolder_Overview"
        Query = @"
SELECT    
  COMPONENTS(parentPath, 7) AS Subfolder,
  SUM(size) as "Size",
  COUNT(name) as "Count"
WHERE ClassID LIKE 'idxobject'
GROUP BY Subfolder
ORDER BY SUM(size) DESC
"@
    },
    @{
        Name = "File_Type_Extension_Summary"
        Query = @"
SELECT
 CASE
   WHEN extension IS NULL THEN 'No Extension'
   WHEN extension = '' THEN 'No Extension'
   ELSE extension
 END AS "File Type",
 COUNT(name) AS "File Count",
 SUM(size) AS "Total Size (Bytes)",
 SUM(size)/1048576 AS "Total Size (MB)",
 AVG(size)/1048576 AS "Average File Size (MB)",
 MIN(size)/1048576 AS "Smallest File (MB)",
 MAX(size)/1048576 AS "Largest File (MB)"
FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject'
GROUP BY
 CASE
   WHEN extension IS NULL THEN 'No Extension'
   WHEN extension = '' THEN 'No Extension'
   ELSE extension
 END
ORDER BY
 SUM(size) DESC
"@
    },
    @{
        Name = "Classification_Summary_by_Data_Source"
        Query = @"
SELECT
 classification AS "Classification Type",
 COUNT(name) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COMPONENTS(parentPath, 3) AS "Primary Location"
FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject' AND
 classifications NOT LIKE '%Unclassified%'
GROUP BY
 classification, COMPONENTS(parentPath, 3)
ORDER BY
 "File Count" DESC
"@
    },
    @{
        Name = "Duplicate_File_Summary"
        Query = @"
-- Infrastructure-Wide Duplicate File Summary
SELECT
 -- Overall Duplicate Statistics
 COUNT(*) AS "Total Files Analyzed",
 SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates",
 SUM(CASE WHEN dupCount > 1 THEN dupCount - 1 ELSE 0 END) AS "Total Duplicate Instances",
 
 -- Storage Impact
 SUM(size)/1073741824 AS "Total Storage Used (GB)",
 SUM(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1073741824 AS "Potential Space Savings (GB)",
 SUM(CASE WHEN dupCount > 1 THEN size * dupCount ELSE 0 END)/1073741824 AS "Total Duplicate Storage (GB)",
 
 -- Duplicate Severity Analysis
 SUM(CASE WHEN dupCount = 2 THEN 1 ELSE 0 END) AS "Files with 2 Copies",
 SUM(CASE WHEN dupCount BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS "Files with 3-5 Copies",
 SUM(CASE WHEN dupCount BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS "Files with 6-10 Copies",
 SUM(CASE WHEN dupCount > 10 THEN 1 ELSE 0 END) AS "Files with 10+ Copies",
 MAX(dupCount) AS "Highest Duplicate Count",
 
 -- Size Categories of Duplicates
 SUM(CASE WHEN dupCount > 1 AND size > 1073741824 THEN 1 ELSE 0 END) AS "Large Duplicates (>1GB)",
 SUM(CASE WHEN dupCount > 1 AND size BETWEEN 104857600 AND 1073741824 THEN 1 ELSE 0 END) AS "Medium Duplicates (100MB-1GB)",
 SUM(CASE WHEN dupCount > 1 AND size < 104857600 THEN 1 ELSE 0 END) AS "Small Duplicates (<100MB)",
 
 -- Biggest Impact Files
 MAX(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1048576 AS "Largest Single File Waste (MB)",
 
 -- Category Analysis (simplified)
 SUM(CASE WHEN dupCount > 1 AND CATEGORY IS NOT NULL THEN 1 ELSE 0 END) AS "Categorized Duplicates",
 SUM(CASE WHEN dupCount > 1 AND CATEGORY IS NULL THEN 1 ELSE 0 END) AS "Uncategorized Duplicates"

FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject'
"@
    },
    @{
        Name = "Classifications_By_Age"
        Query = @"
SELECT
 CASE 
   WHEN (cast(NOW() as number) - accessTime) < (365 * 24 * 60 * 60) THEN 'Under 1 Year'
   WHEN (cast(NOW() as number) - accessTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN '1-2 Years'
   WHEN (cast(NOW() as number) - accessTime) BETWEEN (730 * 24 * 60 * 60) AND (1825 * 24 * 60 * 60) THEN '2-5 Years'
   ELSE '5+ Years'
 END AS "Age Range",
 
 classification AS "Classification Type",
 COUNT(*) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)",
 AVG(size)/1048576 AS "Average File Size (MB)"

FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject' AND
 accessTime IS NOT NULL AND
 classification IS NOT NULL
GROUP BY
 CASE 
   WHEN (cast(NOW() as number) - accessTime) < (365 * 24 * 60 * 60) THEN 'Under 1 Year'
   WHEN (cast(NOW() as number) - accessTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN '1-2 Years'
   WHEN (cast(NOW() as number) - accessTime) BETWEEN (730 * 24 * 60 * 60) AND (1825 * 24 * 60 * 60) THEN '2-5 Years'
   ELSE '5+ Years'
 END,
 classification
ORDER BY
 "Age Range", "File Count" DESC
"@
    },
    @{
        Name = "Classifications_by_Access_Permissions"
        Query = @"
SELECT  
 osPermission AS "User Permission",  
 classification AS "Classification",  
 COUNT(*) AS "File Count",  
 SUM(size)/1073741824 AS "Total Size (GB)",  
 AVG(size)/1048576 AS "Average File Size (MB)" 
FROM  
 STORE('/') 
WHERE  
 ClassID = 'idxobject' AND  
 classifications NOT LIKE '%Unclassified%' AND  
 osPermission IS NOT NULL 
GROUP BY  
 osPermission, classification 
ORDER BY  
 "File Count" DESC
"@
    },
    @{
        Name = "Classifications_by_Owner"
        Query = @"
SELECT  
 osOwner AS "Owner",  
 classification AS "Primary Classification",  
 COUNT(*) AS "File Count",  
 SUM(size)/1073741824 AS "Total Size (GB)",  
 AVG(size)/1048576 AS "Average File Size (MB)"  
FROM  
 STORE('/') 
WHERE  
 ClassID = 'idxobject' AND  
 classifications NOT LIKE '%Unclassified%' AND  
 osOwner IS NOT NULL 
GROUP BY  
 osOwner, classification 
ORDER BY  
 "File Count" DESC
"@
    }
)

# Function to execute AQL query with logging and timing
function Invoke-AQLQuery {
    param(
        [string]$Query,
        [string]$ReportName
    )
    
    $StartTime = Get-Date
    Write-Log "Starting execution of report: $ReportName" "INFO"
    
    try {
        Write-Log "Running report: $ReportName..." "INFO"
        
        # URL encode the query
        $EncodedQuery = [System.Web.HttpUtility]::UrlEncode($Query)
        
        # Build the full URL
        $Url = "${BaseUrl}?select=${EncodedQuery}&options=" + [System.Web.HttpUtility]::UrlEncode('{"format":"json","stream":true,"validate":false}')
        
        Write-Log "API URL: $Url" "INFO"
        
        # Make the HTTP request
        $Response = Invoke-RestMethod -Uri $Url -Method Get -Headers $Headers -TimeoutSec 300
        
        # Calculate execution time
        $ExecutionTime = (Get-Date) - $StartTime
        
        # Save to JSON file
        $OutputFile = Join-Path $ReportsDir "${ReportName}.json"
        $Response | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
        
        $Message = "Report '$ReportName' completed successfully in $($ExecutionTime.TotalSeconds.ToString('F2')) seconds. Saved to: $OutputFile"
        Write-Log $Message "SUCCESS"
        
        return $true
    }
    catch {
        $ExecutionTime = (Get-Date) - $StartTime
        $ErrorMessage = "Error running '$ReportName' after $($ExecutionTime.TotalSeconds.ToString('F2')) seconds: $($_.Exception.Message)"
        Write-Log $ErrorMessage "ERROR"
        return $false
    }
}

# Function to display interactive menu
function Show-ReportMenu {
    param(
        [array]$Reports
    )
    
    Write-Host "`nAvailable Reports:" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    for ($i = 0; $i -lt $Reports.Count; $i++) {
        Write-Host "$($i + 1). $($Reports[$i].Name)" -ForegroundColor White
    }
    
    Write-Host "$($Reports.Count + 1). Run All Reports" -ForegroundColor Yellow
    Write-Host "0. Exit" -ForegroundColor Red
    Write-Host "=" * 50
    
    do {
        $Selection = Read-Host "Select report number (0-$($Reports.Count + 1))"
        $SelectionInt = 0
        $ValidSelection = [int]::TryParse($Selection, [ref]$SelectionInt)
    } while (!$ValidSelection -or $SelectionInt -lt 0 -or $SelectionInt -gt ($Reports.Count + 1))
    
    return $SelectionInt
}

# Function to get selected reports based on user choice
function Get-SelectedReports {
    param(
        [array]$AllReports,
        [int]$Selection
    )
    
    if ($Selection -eq 0) {
        return @()  # Exit
    }
    elseif ($Selection -eq ($AllReports.Count + 1)) {
        return $AllReports  # Run all
    }
    else {
        return @($AllReports[$Selection - 1])  # Run selected report
    }
}

# Add System.Web assembly for URL encoding
Add-Type -AssemblyName System.Web

# Initialize logging
Write-Log "=== Aparavi AQL Reports Execution Started ===" "INFO"
Write-Log "Target: $BaseUrl" "INFO"
Write-Log "Output Directory: $ReportsDir" "INFO"
Write-Log "Log File: $LogFile" "INFO"
Write-Log "Interactive Mode: $Interactive" "INFO"

# Main execution
Write-Host "Starting Aparavi AQL Reports Execution" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl" -ForegroundColor Cyan
Write-Host "Output Directory: $ReportsDir" -ForegroundColor Cyan
Write-Host "Log File: $LogFile" -ForegroundColor Cyan
Write-Host "=" * 50

$SelectedReports = @()

if ($Interactive) {
    # Interactive mode - show menu and get user selection
    do {
        $Selection = Show-ReportMenu -Reports $Reports
        $SelectedReports = Get-SelectedReports -AllReports $Reports -Selection $Selection
        
        if ($SelectedReports.Count -eq 0 -and $Selection -ne 0) {
            Write-Log "No reports selected" "WARNING"
            continue
        }
        
        if ($Selection -eq 0) {
            Write-Log "User selected exit" "INFO"
            Write-Host "Exiting..." -ForegroundColor Yellow
            exit 0
        }
        
        # Execute selected reports
        $SuccessCount = 0
        $TotalReports = $SelectedReports.Count
        $OverallStartTime = Get-Date
        
        Write-Log "Executing $TotalReports selected report(s)" "INFO"
        
        foreach ($Report in $SelectedReports) {
            if (Invoke-AQLQuery -Query $Report.Query -ReportName $Report.Name) {
                $SuccessCount++
            }
            Start-Sleep -Milliseconds 500  # Brief pause between requests
        }
        
        $OverallExecutionTime = (Get-Date) - $OverallStartTime
        
        Write-Host "=" * 50
        Write-Log "Execution batch complete! Successfully executed: $SuccessCount/$TotalReports reports in $($OverallExecutionTime.TotalSeconds.ToString('F2')) seconds" "SUCCESS"
        
        # Ask if user wants to run more reports
        $Continue = Read-Host "`nRun more reports? (y/n)"
        if ($Continue -notmatch '^[Yy]') {
            break
        }
        
    } while ($true)
}
else {
    # Non-interactive mode - run all reports
    $SelectedReports = $Reports
    $SuccessCount = 0
    $TotalReports = $Reports.Count
    $OverallStartTime = Get-Date
    
    Write-Log "Executing all $TotalReports reports" "INFO"
    
    foreach ($Report in $Reports) {
        if (Invoke-AQLQuery -Query $Report.Query -ReportName $Report.Name) {
            $SuccessCount++
        }
        Start-Sleep -Milliseconds 500  # Brief pause between requests
    }
    
    $OverallExecutionTime = (Get-Date) - $OverallStartTime
    
    Write-Host "=" * 50
    Write-Log "Execution Complete! Successfully executed: $SuccessCount/$TotalReports reports in $($OverallExecutionTime.TotalSeconds.ToString('F2')) seconds" "SUCCESS"
}

Write-Host "Reports saved to: $ReportsDir" -ForegroundColor Green
Write-Host "Execution log saved to: $LogFile" -ForegroundColor Green
Write-Log "=== Aparavi AQL Reports Execution Finished ===" "INFO"
