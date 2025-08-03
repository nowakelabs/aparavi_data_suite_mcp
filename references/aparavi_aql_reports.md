# AQL Queries from APARAVI Default Reports

## How to Query the Aparavi API Endpoint

To run these AQL queries via the Aparavi Endpoint API, use the following details:

**Endpoint URL**:
```
http://localhost/server/api/v3/database/query
```

**Required Parameters**:
- `select`: URL-encoded AQL query string
- `options`: JSON string specifying execution flags

**Example HTTP Request**:
```
GET /server/api/v3/database/query?
select=SELECT%20extension%2C%20COUNT(*)%20WHERE%20ClassID%20%3D%20%27idxobject%27%20GROUP%20BY%20extension
&options={"format":"json","stream":true,"validate":true}
```

**Options Object Fields**:
```json
{
  "format": "csv",         // or "json"
  "stream": true,          // stream large results
  "validate": true         // validate syntax without executing
}
```

**Authentication**:
- Use HTTP Basic Auth: `Authorization: Basic base64(username:password)`

**Supported Response Formats**:
- JSON
- CSV

---

## APARAVI - Data Sources Overview

**Description**: Comprehensive analysis of data sources including size, activity indicators, and file categorization metrics.

**Keywords**: data source, storage distribution, file activity, recent files, stale files, large files, duplicates

**Combine with**: Classification Summary, Duplicate File Summary for deeper insights

**Business Questions**:
- Where is my data stored and how is it distributed?
- Which sources have recent activity vs stale data?
- Which sources contain large files or many duplicates?

```sql
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
```

## APARAVI - Subfolder Overview

**Description**: Analyzes subfolder structure showing size and file count distribution across deeper directory levels.

**Keywords**: subfolder, directory structure, folder depth, file count, storage size

**Combine with**: File Type Summary, Classification Summary for context by folder

**Business Questions**:
- Which subfolders consume the most storage?
- Are there deeply nested folders with significant data accumulation?
- Where should cleanup efforts be targeted?

```sql
SELECT    
  COMPONENTS(parentPath, 7) AS Subfolder,
  SUM(size) as "Size",
  COUNT(name) as "Count"
WHERE ClassID LIKE 'idxobject'
GROUP BY Subfolder
ORDER BY SUM(size) DESC
```

## APARAVI - File Type / Extension Summary

**Description**: Comprehensive analysis of file types including size metrics, distribution, and file size ranges.

**Keywords**: extension, file type, format analysis, file size distribution

**Combine with**: Classification Summary, Duplicate File Summary for deeper insights

**Business Questions**:
- What file types consume the most storage?
- What's the size distribution across different file formats?
- Which file types should be prioritized for policy reviews?

```sql
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
```

## APARAVI - Classification Summary by Data Source

**Description**: Shows classified files grouped by data source and classification type, excluding unclassified files.

**Keywords**: classification, pii, sensitive data, category, data source

**Combine with**: Data Source Overview, Monthly Growth by Category

**Business Questions**:
- Where is sensitive or regulated data located?
- Which sources contain the most classified information?
- What's the size distribution of classified data by location?

```sql
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
```

## APARAVI - Duplicate File Summary

**Description**: Comprehensive infrastructure-wide duplicate analysis including severity, size categories, and potential savings.

**Keywords**: duplicate files, deduplication, storage waste, optimization, space savings

**Combine with**: Duplicate File Summary - DETAILED, File Type Summary

**Business Questions**:
- How much storage is being wasted by duplicate files?
- What's the severity distribution of duplicates?
- Which size categories have the most duplication waste?

```sql
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
```

## APARAVI - Classifications By Age

**Description**: Analyzes classified files by age ranges based on last access time, showing aging patterns of sensitive data.

**Keywords**: classification, data age, access patterns, file lifecycle

**Combine with**: Yearly Data Growth, Monthly Data Growth

**Business Questions**:
- How old is our classified data?
- Which age ranges contain the most sensitive information?
- Are we retaining stale classified data?

```sql
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
```

## APARAVI - Classifications by Access Permissions

**Description**: Correlates file classifications with OS-level access permissions to identify security risks.

**Keywords**: access control, osPermission, sensitive data, classification, security risk

**Combine with**: User/Owner Summary, Access Summary

**Business Questions**:
- Are sensitive files overly accessible?
- What permission levels exist on regulated files?
- Do we need to restrict access based on data classification?

```sql
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
```

## APARAVI - Classifications by Owner

**Description**: Groups classified files by their owner to understand data ownership patterns and accountability.

**Keywords**: classification, ownership, accountability, data owner, responsibility

**Combine with**: Data Owner Summary, User File Categories

**Business Questions**:
- Who owns the most sensitive data?
- Which users are responsible for high-risk files?
- How is classified data distributed among users?

```sql
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
```

## APARAVI - Monthly Data Growth by Category

**Description**: Tracks monthly file creation patterns by category to understand data growth trends.

**Keywords**: data growth, monthly trends, category, createTime, file creation patterns

**Combine with**: Classification Summary, Yearly Growth

**Business Questions**:
- How is data growing over time by category?
- Which categories are growing the fastest?
- Are we creating new content in specific categories monthly?

```sql
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
```

## APARAVI - User / Owner File Categories Summary

**Description**: Analyzes file categories by owner for files created since 2024, showing user activity patterns.

**Keywords**: user activity, osOwner, file owner, category, recent activity

**Combine with**: Classification by Owner, Access Summary

**Business Questions**:
- Which users are creating files in specific categories?
- How are file categories distributed by user?
- Who are the most active users by data volume?

```sql
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
```

## APARAVI - Access / Permissions File Categories Summary

**Description**: Maps file categories to OS permissions for files created since 2024, analyzing permission patterns.

**Keywords**: access permissions, file categories, osPermission, security patterns

**Combine with**: Classification by Owner, Sensitive Data Reports

**Business Questions**:
- How are permission settings distributed across categories?
- Are certain categories consistently over-permissioned?
- What's the relationship between file category and access control?

```sql
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
```

## APARAVI - Data Sources Overview - Last Modified

**Description**: Analyzes data sources by modification age ranges, showing activity patterns and data freshness.

**Keywords**: last modified, activity, data source, freshness, modification patterns

**Combine with**: File Type Activity, Created and Accessed Reports

**Business Questions**:
- Which data sources are actively changing?
- How much data in each source is stale vs recently modified?
- What's the modification age distribution across sources?

```sql
SELECT
 COMPONENTS(parentPath, 3) AS "Data Source",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COUNT(name) AS "Total Count",
 
 -- Age ranges by last modified (consistent ranges)
 SUM(CASE WHEN modifyTime IS NULL THEN 1 ELSE 0 END) AS "Unknown Modified",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) < (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified <1 Year",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 1-2 Years",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 2-3 Years",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 3-4 Years",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) > (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Modified 4+ Years",
 
 -- Size by age ranges
 SUM(CASE WHEN modifyTime IS NULL THEN size ELSE 0 END)/1073741824 AS "Unknown Modified Size (GB)",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) < (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recent Modified Size (GB)",
 SUM(CASE WHEN (cast(NOW() as number) - modifyTime) > (1460 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Very Old Modified Size (GB)"

FROM 
 STORE('/')
WHERE 
 ClassID = 'idxobject'
GROUP BY 
 COMPONENTS(parentPath, 3)
ORDER BY 
 "Total Size (GB)" DESC
```

## APARAVI - Data Sources Overview - Created

**Description**: Analyzes data sources by creation age ranges, showing data source lifecycle patterns.

**Keywords**: creation time, data source, file age, lifecycle, data history

**Combine with**: Last Accessed, Classification by Age

**Business Questions**:
- How long has data existed in each source?
- Which repositories are hosting legacy vs recent files?
- What's the creation age distribution of our data assets?

```sql
SELECT
 COMPONENTS(parentPath, 3) AS "Data Source",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COUNT(name) AS "Total Count",
 
 -- Age ranges by creation time (consistent ranges)
 SUM(CASE WHEN createTime IS NULL THEN 1 ELSE 0 END) AS "Unknown Created",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created <1 Year",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (365 * 24 * 60 * 60) AND (730 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 1-2 Years",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (730 * 24 * 60 * 60) AND (1095 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 2-3 Years",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) BETWEEN (1095 * 24 * 60 * 60) AND (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 3-4 Years",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) > (1460 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Created 4+ Years",
 
 -- Size by age ranges
 SUM(CASE WHEN createTime IS NULL THEN size ELSE 0 END)/1073741824 AS "Unknown Created Size (GB)",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) < (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recent Created Size (GB)",
 SUM(CASE WHEN (cast(NOW() as number) - createTime) > (1460 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Very Old Created Size (GB)"

FROM 
 STORE('/')
WHERE 
 ClassID = 'idxobject'
GROUP BY 
 COMPONENTS(parentPath, 3)
ORDER BY 
 "Total Size (GB)" DESC
```

## APARAVI - Data Sources Overview - Last Accessed

**Description**: Analyzes data sources by access patterns, showing usage trends and identifying stale data.

**Keywords**: access time, user behavior, data value, usage recency, stale data

**Combine with**: Last Modified, Owner Summary

**Business Questions**:
- Which sources are actively accessed vs abandoned?
- How much storage is consumed by unused data?
- What's the access age distribution across data sources?

```sql
SELECT
 COMPONENTS(parentPath, 3) AS "Data Source",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COUNT(name) AS "Total Count",
 
 -- Age ranges by last access time
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed Last 30 Days",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) BETWEEN (30 * 24 * 60 * 60) AND (90 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed 1-3 Months Ago",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) BETWEEN (90 * 24 * 60 * 60) AND (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Accessed 3-12 Months Ago",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Not Accessed >1 Year",
 
 -- Size by access age ranges
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) < (30 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Recently Accessed Size (GB)",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN size ELSE 0 END)/1073741824 AS "Stale Access Size (GB)",
 
 -- Average access age
 AVG((cast(NOW() as number) - accessTime)/(24 * 60 * 60)) AS "Average Days Since Access"

FROM 
 STORE('/')
WHERE 
 ClassID = 'idxobject' AND
 accessTime IS NOT NULL
GROUP BY 
 COMPONENTS(parentPath, 3)
ORDER BY 
 "Total Size (GB)" DESC
```

## APARAVI - File Type / Extension Activity

**Description**: Categorizes file types by activity status, showing which formats are actively used vs stale.

**Keywords**: file type, recent activity, modification, extension, usage patterns

**Combine with**: File Type Summary, Data Growth Reports

**Business Questions**:
- Which file types are currently in use vs dormant?
- What formats should be archived or migrated?
- Are certain file types consistently stale across the environment?

```sql
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
```

## APARAVI - Duplicate File Summary - DETAILED

**Description**: Detailed duplicate analysis by age groups, showing duplication patterns across different file generations.

**Keywords**: duplicate hash, storage waste, age-based analysis, deduplication by timeframe

**Combine with**: Duplicate Summary, File Type Summary

**Business Questions**:
- Which age groups have the most duplication waste?
- Are older files more likely to be duplicated?
- What's the potential savings by targeting specific age ranges?

```sql
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
```

## APARAVI - Yearly Data Growth Report

**Description**: Simple yearly data creation analysis showing file count and size trends over time.

**Keywords**: data growth, yearly trend, createTime, file volume, historical analysis

**Combine with**: Monthly Growth, Classification by Age

**Business Questions**:
- How is our data footprint evolving year over year?
- Are recent years showing accelerated growth?
- When did major data creation events occur?

```sql
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
```

## APARAVI - Data Owner Summary

**Description**: Aggregates file ownership showing which users consume the most storage, limited to top 50 owners.

**Keywords**: ownership, osOwner, storage use, user footprint, top consumers

**Combine with**: Classification by Owner, Duplicate Summary

**Business Questions**:
- Who owns the most data in our environment?
- How is storage consumption distributed among users?
- Which users should be targeted for storage optimization?

```sql
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
```

## APARAVI - Simple Classification Summary

**Description**: Basic classification overview showing file count and size for all classification types including unclassified.

**Keywords**: classification, tagging, data categories, sensitive data, overview

**Combine with**: Classification by Source, Classification by Owner

**Business Questions**:
- How much of our data is classified vs unclassified?
- What are the most common classification types?
- What's the storage distribution across classifications?

```sql
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
```

## APARAVI - File Type / Category Summary DETAILED

**Description**: Comprehensive analysis of Aparavi categories including size distribution, activity metrics, and duplicate analysis.

**Keywords**: aparavi category, size distribution, activity analysis, file lifecycle, duplicate waste

**Combine with**: File Type Summary, Classification Summary

**Business Questions**:
- How are files distributed across Aparavi categories?
- Which categories contain the most stale or duplicate data?
- What's the activity level and storage efficiency by category?

```sql
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
```