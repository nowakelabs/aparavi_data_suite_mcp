## Prompt Engineering Guide to Teach LLMs the Aparavi Query Language (AQL)

This document defines the concepts, syntax, and query examples needed to teach any large language model (LLM) how to generate valid and purposeful AQL (Aparavi Query Language) queries from natural language prompts. It also includes details on how to query and validate syntax through the Aparavi Endpoint API.

---

### 🔹 1. What is AQL?
AQL is a domain-specific query language used to retrieve, aggregate, and analyze file metadata within the Aparavi platform. It supports:
- File size, location, and extension filtering
- Classification-based queries (PII, financial, sensitive)
- Metadata analysis (author, page count, image size, etc.)
- Duplicate detection and storage optimization

---

### 🔹 2. AQL Syntax Overview
```sql
SELECT column1 AS "Alias1", column2
WHERE condition
GROUP BY column1
ORDER BY column2 DESC
```

#### Examples:
```sql
extension = 'pdf'
size > 104857600  -- files > 100MB
classifications LIKE '%Sensitive%'
metadata LIKE '%"Author":"John"%'
```

---

### 🔹 3. Core Fields for SELECT / WHERE
| Field | Description |
|-------|-------------|
| name | File name |
| path | Full file path |
| parentPath | Directory path within Aparavi (virtual) |
| localPath | Actual file system path |
| size | Size in bytes |
| accessTime | Last accessed time |
| createTime | Created time |
| modifyTime | Last modified time |
| extension | File extension |
| osOwner | OS-level file owner |
| osPermission | File permissions |
| classification | Primary classification |
| classifications | All matching classifications |
| confidence | Classification confidence score |
| dupCount | Number of duplicate files |
| dupKey | File content hash signature |
| metadata | Metadata string for LIKE filtering |
| metadataObject | Structured metadata output (SELECT only) |

---

### 🔹 4. Prompt to AQL Translation Examples

**Prompt**: My data is growing 200GB per week and I don’t know why  
**AQL**:
```sql
SELECT
  YEAR(createTime) AS "Year",
  WEEK(createTime) AS "Week",
  extension AS "File Type",
  COUNT(*) AS "Files Created",
  SUM(size)/1073741824 AS "Size Added (GB)"
WHERE
  createTime >= '2024-01-01' AND
  ClassID = 'idxobject'
GROUP BY
  YEAR(createTime), WEEK(createTime), extension
ORDER BY
  "Year", "Week", "Size Added (GB)" DESC
```

**Prompt**: Identify duplicate files and calculate storage waste
```sql
SELECT 
  SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates",
  SUM(CASE WHEN dupCount > 1 THEN dupCount - 1 ELSE 0 END) AS "Duplicate Instances",
  SUM(CASE WHEN dupCount > 1 THEN size * (dupCount - 1) ELSE 0 END)/1048576 AS "Potential Space Savings (MB)"
WHERE 
  dupCount > 1 AND
  ClassID = 'idxobject'
```

---

### 🔹 5. Using the Aparavi Endpoint API

You can validate or execute AQL queries via HTTP against the local Aparavi Endpoint:

**Endpoint**:
```
http://localhost/server/api/v3/database/query
```

**Query Parameters**:
- `select`: the AQL query (URL encoded)
- `options`: JSON string with execution flags

**Validation Example** (no data returned):
```http
GET /server/api/v3/database/query
?select=SELECT%20...your_query...
&options={"format":"json","stream":true,"validate":true}
```

**Authentication**:
- Basic Auth (`Authorization: Basic base64(username:password)`)

**Supported Formats**:
- `json`
- `csv`

**Validation Option**:
- `validate: true` → checks AQL syntax only, without executing the query

**Sample Options JSON**:
```json
{
  "format": "csv",
  "stream": true,
  "validate": true
}
```


---

### 🔹 6. Common Metadata Keys for Filtering

When filtering metadata, you must use `metadata LIKE '%...%'` and match known JSON patterns inside the string.

| Field Key | Description | Example Pattern |
|
> ⚠️ Avoid trying to extract or cast values from within `metadata` using functions like `CAST()`, `SUBSTRING()`, or `LOCATE()`. AQL does not support JSON parsing or complex string manipulation. Instead:
> - Use `metadata LIKE '%"Field":"Value"%'` for direct string matches
> - For numeric-like values (e.g., durations), use heuristic filters like `metadata LIKE '%:03%' OR '%:04%'` to simulate range checking
> - Consider preprocessing or tagging files externally if range queries on metadata are required


-----------|-------------|-----------------|
| `"containVBA"` | Detects Excel files with macros | `metadata LIKE '%"containVBA":"true"%'` |
| `"Author"` | Document author | `metadata LIKE '%"Author":"Jane Doe"%'` |
| `"Page-Count"` | Number of pages | `metadata LIKE '%"Page-Count":'` |
| `"Word-Count"` | Word total | `metadata LIKE '%"Word-Count":'` |
| `"Image-Width"` / `"Image-Height"` | Image resolution | `metadata LIKE '%"Image-Width":'` |
| `"xmpDM:duration"` | Video/audio duration | `metadata LIKE '%"xmpDM:duration":'` |
| `"geo:lat"` / `"geo:long"` | GPS tags | `metadata LIKE '%"geo:lat":'` |
| `"Message-From"` / `"Message-To"` | Email sender/recipient | `metadata LIKE '%"Message-From":"john@example.com"%'` |

> **WARNING:** Do not use dot notation or filters like `metadataObject.containVBA = true`. Only use `metadata LIKE` with the full JSON string.

---

Use this guide to teach any LLM how to reason over storage and data classification problems using AQL, validate syntax using the Aparavi Endpoint, and generate working queries ready for direct execution.

---

### 🔹 Handling “Unclassified” Files

Be aware that some files may contain the classification label "Unclassified", even though the field `classification IS NOT NULL`. To accurately filter out these files, always add:

```sql
classification != 'Unclassified'
```

or if using the `classifications` field:

```sql
classifications NOT LIKE '%Unclassified%'
```

This ensures the query returns only files with meaningful classification matches.
