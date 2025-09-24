# Aparavi AQL Reports Runner
# Executes Aparavi AQL reports and saves results to timestamped JSON files
# 
# USAGE EXAMPLES:
#   .\run-all-reports.ps1                                    # Run all fast reports automatically
#   .\run-all-reports.ps1 -Interactive                      # Interactive menu to select reports
#   .\run-all-reports.ps1 -IncludeSlow                      # Run all reports including slow ones
#   .\run-all-reports.ps1 -Interactive -IncludeSlow         # Interactive mode with slow reports
#   .\run-all-reports.ps1 -File "sample.json"               # Use reports from JSON export file
#   .\run-all-reports.ps1 -AparaviHost "10.1.10.163"       # Connect to specific host
#   .\run-all-reports.ps1 -Username "admin" -Password "pwd" # Custom credentials
#
# PARAMETERS:
#   -AparaviHost  Aparavi server hostname/IP (default: localhost)
#   -AparaviPort  Aparavi server port (default: 80)
#   -Username     Authentication username (default: root)
#   -Password     Authentication password (default: root)
#   -Interactive  Show interactive menu for report selection
#   -IncludeSlow  Include long-running reports that may take several minutes
#   -File         Path to Aparavi JSON export file (uses built-in reports if not specified)
#
# OUTPUT:
#   - Creates timestamped folders in ./reports/ directory
#   - Saves each report as JSON file with report name
#   - Generates execution log with timing and status information
#
# REQUIREMENTS: PowerShell 5.1 or later

param(
    [string]$AparaviHost = "localhost",
    [int]$AparaviPort = 80,
    [string]$Username = "root",
    [string]$Password = "root",
    [switch]$Interactive,
    [switch]$IncludeSlow,
    [string]$File = ""
)

# Create reports directory if it doesn't exist
$BaseReportsDir = Join-Path $PSScriptRoot "reports"
if (!(Test-Path $BaseReportsDir)) {
    New-Item -ItemType Directory -Path $BaseReportsDir -Force | Out-Null
    Write-Host "Created reports directory: $BaseReportsDir" -ForegroundColor Green
}

# Create timestamped subdirectory for this run
$RunTimestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportsDir = Join-Path $BaseReportsDir $RunTimestamp
New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
Write-Host "Created run directory: $ReportsDir" -ForegroundColor Green

# Create log file with timestamp in the run directory
$LogFile = Join-Path $ReportsDir "$RunTimestamp.log"

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

# Function to load reports from JSON export file
function Load-ReportsFromJson {
    param([string]$JsonFilePath)
    
    if (!(Test-Path $JsonFilePath)) {
        Write-Log "JSON export file not found: $JsonFilePath" "ERROR"
        return @()
    }
    
    try {
        $JsonContent = Get-Content $JsonFilePath -Raw | ConvertFrom-Json
        $LoadedReports = @()
        
        foreach ($ReportId in $JsonContent.PSObject.Properties.Name) {
            $Report = $JsonContent.$ReportId
            $ReportName = $Report.name -replace "APARAVI - ", "" -replace "[^a-zA-Z0-9_]", "_"
            $Query = $Report.query.queries[0].value
            
            $LoadedReports += @{
                Name = $ReportName
                Query = $Query
                IsLongRunning = $false  # Default to fast, can be overridden
            }
        }
        
        Write-Log "Loaded $($LoadedReports.Count) reports from JSON export: $JsonFilePath" "INFO"
        return $LoadedReports
    }
    catch {
        Write-Log "Error loading JSON export file: $($_.Exception.Message)" "ERROR"
        return @()
    }
}

# Define all reports with their names, AQL queries, and category usage flag
$Reports = @(
    @{
        Name = "Data_Sources_Overview"
        Query = @"
SELECT 
  COMPONENTS(parentPath, 3) as data_source,
  SUM(size) as total_size_bytes,
  COUNT(*) as file_count
FROM STORE('/')
WHERE ClassID = 'idxobject'
GROUP BY COMPONENTS(parentPath, 3)
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
        IsLongRunning = $true
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
    },
    @{
        Name = "Monthly_Data_Growth_by_Category"
        IsLongRunning = $true
        Query = @"
SELECT
 YEAR(createTime) AS "Year",
 MONTH(createTime) AS "Month", 
 CATEGORY AS "File Category",
 COUNT(name) AS "Files Added",
 SUM(size)/1073741824 AS "Size Added (GB)"

FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject' AND
 createTime IS NOT NULL AND
 CATEGORY IS NOT NULL
GROUP BY
 YEAR(createTime), MONTH(createTime), CATEGORY
ORDER BY
 "Year" DESC, "Month" DESC, "Size Added (GB)" DESC
"@
    },
    @{
        Name = "User_Owner_File_Categories_Summary"
        IsLongRunning = $true
        Query = @"
SELECT
 osOwner AS "User/Owner",
 CATEGORY AS "File Category",
 COUNT(name) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)"
FROM 
 STORE('/')
WHERE
 createTime >= '2024-01-01' AND
 ClassID = 'idxobject' AND
 CATEGORY IS NOT NULL
GROUP BY
 osOwner, CATEGORY
ORDER BY
 "Total Size (GB)" DESC
"@
    },
    @{
        Name = "Access_Permissions_File_Categories_Summary"
        IsLongRunning = $true
        Query = @"
SELECT
 osPermission AS "User",
 CATEGORY AS "File Category",
 COUNT(name) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)"
FROM 
 STORE('/')
WHERE
 createTime >= '2024-01-01' AND
 ClassID = 'idxobject' AND
 CATEGORY IS NOT NULL AND
 osPermission IS NOT NULL
GROUP BY
 osPermission, CATEGORY
ORDER BY
 "Total Size (GB)" DESC
"@
    },
    @{
        Name = "Data_Sources_Overview_Last_Modified"
        Query = @"
SELECT 
  COMPONENTS(parentPath, 3) AS "Data Source",
  SUM(size)/1073741824 AS "Total Size (GB)",
  COUNT(name) AS "Total Count",
  SUM(CASE WHEN modifyTime IS NULL THEN 1 ELSE 0 END) AS "Unknown Modified",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) < (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified <1 Year",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 1-2 Years",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 2-3 Years",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 3-4 Years",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) > (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 4+ Years",
  SUM(CASE WHEN modifyTime IS NULL THEN size ELSE 0 END)/1073741824 AS "Unknown Modified Size (GB)",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) < (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recent Modified Size (GB)",
  SUM(CASE WHEN (cast(NOW() as number) - modifyTime) > (1460 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Very Old Modified Size (GB)"
FROM STORE('/')
WHERE ClassID = 'idxobject'
GROUP BY COMPONENTS(parentPath, 3)
ORDER BY "Total Size (GB)" DESC
"@
    },
    @{
        Name = "Data_Sources_Overview_Created"
        Query = @"
SELECT 
  COMPONENTS(parentPath, 3) AS "Data Source",
  SUM(size)/1073741824 AS "Total Size (GB)",
  COUNT(name) AS "Total Count",
  SUM(CASE WHEN createTime IS NULL THEN 1 ELSE 0 END) AS "Unknown Created",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created <1 Year",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 1-2 Years",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 2-3 Years",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 3-4 Years",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) > (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 4+ Years",
  SUM(CASE WHEN createTime IS NULL THEN size ELSE 0 END)/1073741824 AS "Unknown Created Size (GB)",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recent Created Size (GB)",
  SUM(CASE WHEN (cast(NOW() as number) - createTime) > (1460 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Very Old Created Size (GB)"
FROM STORE('/')
WHERE ClassID = 'idxobject'
GROUP BY COMPONENTS(parentPath, 3)
ORDER BY "Total Size (GB)" DESC
"@
    },
    @{
        Name = "Data_Sources_Overview_Last_Accessed"
        Query = @"
SELECT 
  COMPONENTS(parentPath, 3) AS "Data Source",
  SUM(size)/1073741824 AS "Total Size (GB)",
  COUNT(name) AS "Total Count",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed Last 30 Days",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) BETWEEN (30 * 24 * 60 * 60) AND (90 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed 1-3 Months Ago",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) BETWEEN (90 * 24 * 60 * 60) AND (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed 3-12 Months Ago",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Not Accessed >1 Year",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) < (30 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recently Accessed Size (GB)",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Stale Access Size (GB)",
  AVG((cast(NOW() as number) - accessTime)/(24 * 60 * 60)) AS "Average Days Since Access"
FROM STORE('/')
WHERE ClassID = 'idxobject' AND accessTime IS NOT NULL
GROUP BY COMPONENTS(parentPath, 3)
ORDER BY "Total Size (GB)" DESC
"@
    },
    @{
        Name = "File_Type_Extension_Activity"
        Query = @"
SELECT
 extension AS "File Extension",
 CASE
   WHEN (cast(NOW() as number) - accessTime) > (180 * 24 * 60 * 60) THEN 'Stale (Not Accessed 6+ Months)'
   WHEN (cast(NOW() as number) - modifyTime) > (180 * 24 * 60 * 60) THEN 'Read-Only (Not Modified 6+ Months)'
   WHEN (cast(NOW() as number) - accessTime) < (7 * 24 * 60 * 60) THEN 'Very Active (Accessed This Week)'
   ELSE 'Moderately Active'
 END AS "Activity Status",
 COUNT(name) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)",
 AVG(size)/1048576 AS "Average File Size (MB)"
FROM 
 STORE('/')
WHERE
 (cast(NOW() as number) - createTime) > (180 * 24 * 60 * 60) AND
 ClassID = 'idxobject'
GROUP BY
 extension,
 CASE
   WHEN (cast(NOW() as number) - accessTime) > (180 * 24 * 60 * 60) THEN 'Stale (Not Accessed 6+ Months)'
   WHEN (cast(NOW() as number) - modifyTime) > (180 * 24 * 60 * 60) THEN 'Read-Only (Not Modified 6+ Months)'
   WHEN (cast(NOW() as number) - accessTime) < (7 * 24 * 60 * 60) THEN 'Very Active (Accessed This Week)'
   ELSE 'Moderately Active'
 END
ORDER BY
 extension
"@
    },
    @{
        Name = "Duplicate_File_Summary_Detailed"
        IsLongRunning = $true
        Query = @"
SELECT
 CASE 
   WHEN createTime IS NULL THEN 'Unknown Age'
   WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN 'Created <1 Year'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 'Created 1-2 Years'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 'Created 2-3 Years'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 'Created 3-4 Years'
   ELSE 'Created 4+ Years'
 END AS "Age Group",
 
 -- Overall file statistics per age group
 COUNT(*) AS "Total Files in Age Group",
 SUM(size)/1073741824 AS "Total Storage (GB)",
 
 -- Duplicate analysis per age group
 SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates",
 SUM(CASE WHEN dupCount > 1 THEN dupCount - 1 ELSE 0 END) AS "Duplicate Instances",
 SUM(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1073741824 AS "Potential Space Savings (GB)",
 
 -- Duplicate severity in each age group
 SUM(CASE WHEN dupCount = 2 THEN 1 ELSE 0 END) AS "Files with 2 Copies",
 SUM(CASE WHEN dupCount BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS "Files with 3-5 Copies",
 SUM(CASE WHEN dupCount > 10 THEN 1 ELSE 0 END) AS "Files with 10+ Copies",
 
 -- Average duplicate statistics per age group
 AVG(CASE WHEN dupCount > 1 THEN dupCount ELSE 0 END) AS "Average Duplicates",
 AVG(CASE WHEN dupCount > 1 THEN size ELSE 0 END)/1048576 AS "Average Duplicate File Size (MB)",
 
 -- Largest waste in each age group
 MAX(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1048576 AS "Largest Single File Waste (MB)"

FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject'
GROUP BY
 CASE 
   WHEN createTime IS NULL THEN 'Unknown Age'
   WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN 'Created <1 Year'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 'Created 1-2 Years'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 'Created 2-3 Years'
   WHEN (cast(NOW() as number) - createTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 'Created 3-4 Years'
   ELSE 'Created 4+ Years'
 END
ORDER BY
 "Potential Space Savings (GB)" DESC
"@
    },
    @{
        Name = "Yearly_Data_Growth_Report"
        Query = @"
SET @@DEFAULT_COLUMNS=createTime,name,size,ClassID;

SELECT 
  YEAR(createTime) as "Creation Year",
  COUNT(name) as "File Count",
  SUM(size) as "Total Size (Bytes)",
  SUM(size)/1048576 as "Total Size (MB)",
  AVG(size) as "Average File Size (Bytes)"
WHERE 
  ClassID LIKE 'idxobject'
GROUP BY 
  YEAR(createTime)
ORDER BY 
  YEAR(createTime) DESC;
"@
    },
    @{
        Name = "Data_Owner_Summary"
        Query = @"
SET @@DEFAULT_COLUMNS=osOwner,name,size,ClassID;

SELECT 
  CASE 
    WHEN osOwner IS NULL THEN 'Unowned'
    WHEN osOwner = '' THEN 'Unowned'
    ELSE osOwner
  END as "Owner",
  COUNT(name) as "File Count",
  SUM(size) as "Total Size (Bytes)",
  SUM(size)/1048576 as "Total Size (MB)",
  AVG(size) as "Average File Size (Bytes)"
WHERE 
  ClassID LIKE 'idxobject'
GROUP BY 
  CASE 
    WHEN osOwner IS NULL THEN 'Unowned'
    WHEN osOwner = '' THEN 'Unowned'
    ELSE osOwner 
  END
ORDER BY 
  SUM(size) DESC
LIMIT 50;
"@
    },
    @{
        Name = "Simple_Classification_Summary"
        Query = @"
SET @@DEFAULT_COLUMNS=classification,name,size,ClassID;
SELECT
CASE
WHEN classification IS NULL THEN 'Unclassified'
WHEN classification = '' THEN 'Unclassified'
ELSE classification
END as "Classification",
COUNT(name) as "File Count",
SUM(size) as "Total Size (Bytes)",
SUM(size)/1048576 as "Total Size (MB)"
WHERE
ClassID LIKE 'idxobject'
GROUP BY
CASE
WHEN classification IS NULL THEN 'Unclassified'
WHEN classification = '' THEN 'Unclassified'
ELSE classification
END
ORDER BY
COUNT(name) DESC;
"@
    },
    @{
        Name = "File_Type_Category_Summary_Detailed"
        IsLongRunning = $true
        Query = @"
SELECT
 COALESCE(CATEGORY, 'Uncategorized') AS "Aparavi Category",
 COUNT(name) AS "File Count",
 SUM(size)/1073741824 AS "Total Size (GB)",
 AVG(size)/1048576 AS "Average File Size (MB)",
 MIN(size)/1048576 AS "Smallest File (MB)",
 MAX(size)/1048576 AS "Largest File (MB)",
 
 -- Size distribution analysis
 SUM(CASE WHEN size > 1073741824 THEN 1 ELSE 0 END) AS "Large Files (>1GB)",
 SUM(CASE WHEN size BETWEEN 104857600 AND 1073741824 THEN 1 ELSE 0 END) AS "Medium Files (100MB-1GB)",
 SUM(CASE WHEN size < 1048576 THEN 1 ELSE 0 END) AS "Small Files (<1MB)",
 
 -- Age and activity analysis
 SUM(CASE WHEN (cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created Last 30 Days",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Not Accessed 1+ Years",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Stale Data Size (GB)",
 
 -- Duplicate analysis
 SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates",
 SUM(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1073741824 AS "Duplicate Waste (GB)"

FROM
 STORE('/')
WHERE
 ClassID = 'idxobject'
GROUP BY
 COALESCE(CATEGORY, 'Uncategorized')
ORDER BY
 "Total Size (GB)" DESC
"@
    }
)

# Override reports with JSON export if specified
if ($File -ne "") {
    Write-Log "Using JSON export file: $File" "INFO"
    $JsonReports = Load-ReportsFromJson $File
    if ($JsonReports.Count -gt 0) {
        $Reports = $JsonReports
        Write-Log "Replaced built-in reports with $($Reports.Count) reports from JSON export" "INFO"
    } else {
        Write-Log "Failed to load JSON export, falling back to built-in reports" "WARNING"
    }
}

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
    Write-Host ("=" * 50)
    
    for ($i = 0; $i -lt $Reports.Count; $i++) {
        $ReportDisplay = "$($i + 1). $($Reports[$i].Name)"
        if ($Reports[$i].IsLongRunning) {
            $ReportDisplay += " [LONG RUNNING - Slow]"
            Write-Host $ReportDisplay -ForegroundColor Yellow
        } else {
            Write-Host $ReportDisplay -ForegroundColor White
        }
    }
    
    Write-Host "$($Reports.Count + 1). Run All Reports" -ForegroundColor Yellow
    Write-Host "0. Exit" -ForegroundColor Red
    Write-Host ("=" * 50)
    
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
Write-Log "Include Slow Reports: $IncludeSlow" "INFO"

# Filter reports based on long running status
$FilteredReports = if ($IncludeSlow) {
    $Reports
} else {
    $Reports | Where-Object { -not $_.IsLongRunning }
}

# Main execution
Write-Host "Starting Aparavi AQL Reports Execution" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl" -ForegroundColor Cyan
Write-Host "Output Directory: $ReportsDir" -ForegroundColor Cyan
Write-Host "Log File: $LogFile" -ForegroundColor Cyan
if (-not $IncludeSlow) {
    $LongRunningReportCount = ($Reports | Where-Object { $_.IsLongRunning }).Count
    Write-Host "Excluding $LongRunningReportCount slow reports (use -IncludeSlow to include)" -ForegroundColor Yellow
}
Write-Host ("=" * 50)

$SelectedReports = @()

if ($Interactive) {
    # Interactive mode - show menu and get user selection
    do {
        $Selection = Show-ReportMenu -Reports $FilteredReports
        $SelectedReports = Get-SelectedReports -AllReports $FilteredReports -Selection $Selection
        
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
        
        Write-Host ("=" * 50)
        Write-Log "Execution batch complete! Successfully executed: $SuccessCount/$TotalReports reports in $($OverallExecutionTime.TotalSeconds.ToString('F2')) seconds" "SUCCESS"
        
        # Ask if user wants to run more reports
        $Continue = Read-Host "`nRun more reports? (y/n)"
        if ($Continue -notmatch '^[Yy]') {
            break
        }
        
    } while ($true)
}
else {
    # Non-interactive mode - run filtered reports
    $SelectedReports = $FilteredReports
    $SuccessCount = 0
    $TotalReports = $FilteredReports.Count
    $OverallStartTime = Get-Date
    
    Write-Log "Executing $TotalReports filtered reports" "INFO"
    
    foreach ($Report in $FilteredReports) {
        if (Invoke-AQLQuery -Query $Report.Query -ReportName $Report.Name) {
            $SuccessCount++
        }
        Start-Sleep -Milliseconds 500  # Brief pause between requests
    }
    
    $OverallExecutionTime = (Get-Date) - $OverallStartTime
    
    Write-Host ("=" * 50)
    Write-Log "Execution Complete! Successfully executed: $SuccessCount/$TotalReports reports in $($OverallExecutionTime.TotalSeconds.ToString('F2')) seconds" "SUCCESS"
}

Write-Host "Reports saved to: $ReportsDir" -ForegroundColor Green
Write-Host "Execution log saved to: $LogFile" -ForegroundColor Green
Write-Log "=== Aparavi AQL Reports Execution Finished ===" "INFO"
